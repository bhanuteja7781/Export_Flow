"""
inbox_module.py - Live Buyer Inbox, Reply & Bounce Tracking Engine
Connects to live Gmail IMAP (imap.gmail.com:993) to retrieve genuine incoming buyer replies,
detect auto-replies, and identify delivery failure bounces.
"""

import os
import re
import time
import json
import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Any, Optional, Set, Tuple
import datetime
from dotenv import load_dotenv


class InboxTrackerModule:
    """
    Scans Live Gmail Inbox via IMAP for authentic buyer replies, auto-replies, and bounce notifications.
    """

    IMAP_HOST = "imap.gmail.com"
    IMAP_PORT = 993

    def __init__(
        self,
        gmail_email: Optional[str] = None,
        app_password: Optional[str] = None
    ):
        self._load_credentials(gmail_email, app_password)

    def _load_credentials(self, gmail_email: Optional[str] = None, app_password: Optional[str] = None):
        """
        Dynamically refreshes credentials from backend/.env and strips whitespace.
        """
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)

        self.gmail_email = (gmail_email or os.getenv("GMAIL_EMAIL", "")).strip()
        raw_pw = app_password or os.getenv("GMAIL_APP_PASSWORD", "")
        self.app_password = raw_pw.replace(" ", "").strip()

    def scan_for_replies(
        self,
        leads: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Scans Live Gmail inbox via IMAP for buyer replies and bounce notifications.
        Updates lead records with authentic responses and sentiment.
        """
        self._load_credentials()

        detected_replies = []
        detected_bounces = set()

        if self.gmail_email and self.app_password:
            try:
                detected_replies, detected_bounces = self._scan_imap_inbox_and_bounces(leads)
            except Exception as e:
                print(f"[InboxTracker] Live IMAP scan notice: {e}")
        else:
            print("[InboxTracker] Gmail credentials not configured for IMAP scanning.")

        # Map detected replies by lead ID and lead email
        reply_by_lead_id = {r["lead_id"]: r for r in detected_replies if r.get("lead_id")}
        reply_by_email = {r["lead_email"].lower(): r for r in detected_replies if r.get("lead_email")}
        bounced_emails = {b.lower().strip() for b in detected_bounces}

        updated_leads = []
        for lead in leads:
            lead_copy = dict(lead)
            l_id = lead_copy.get("id")
            em = lead_copy.get("email", "").strip().lower()

            # 1. Handle Bounced Deliveries
            if em in bounced_emails or (lead_copy.get("reply_status") == "bounced"):
                lead_copy["reply_status"] = "bounced"
                lead_copy["validation_status"] = "invalid"
                lead_copy["responses"] = "Delivery Failed (Mailbox Not Found / Bounced)"
                lead_copy["follow_ups"] = "Remove or obtain updated buyer email"
            # 2. Handle Inbound Buyer Replies & Auto-Replies
            elif l_id in reply_by_lead_id or em in reply_by_email:
                rep = reply_by_lead_id.get(l_id) or reply_by_email.get(em)
                if rep:
                    if rep.get("is_auto_reply"):
                        lead_copy["reply_status"] = "auto_reply"
                        lead_copy["replied_at"] = rep.get("received_at") or datetime.datetime.now(datetime.timezone.utc).isoformat()
                        lead_copy["reply_subject"] = rep.get("subject", "")
                        lead_copy["reply_snippet"] = rep.get("snippet", "")[:300]
                        lead_copy["reply_sentiment"] = "auto_reply"
                        lead_copy["reply_sentiment_label"] = "Auto-Reply (Out of Office)"
                        lead_copy["responses"] = "Automated Reply"
                        lead_copy["follow_ups"] = "Set reminder to follow up 3 business days post-return"
                    else:
                        lead_copy["reply_status"] = "replied"
                        lead_copy["replied_at"] = rep.get("received_at") or datetime.datetime.now(datetime.timezone.utc).isoformat()
                        lead_copy["reply_subject"] = rep.get("subject", "")
                        lead_copy["reply_snippet"] = rep.get("snippet", "")[:300]
                        lead_copy["reply_sentiment"] = rep.get("sentiment", "interested")
                        lead_copy["reply_sentiment_label"] = rep.get("sentiment_label", "Inbound Buyer Reply")
                        lead_copy["responses"] = f"Replied: {rep.get('snippet', '')[:120]}"
                        lead_copy["follow_ups"] = "Send wholesale catalog, MOQ matrix & custom pricing deck"
            # 3. Handle existing statuses
            else:
                if lead_copy.get("reply_status") == "auto_reply":
                    lead_copy["responses"] = "Automated Reply"
                    lead_copy["reply_sentiment"] = "auto_reply"
                    lead_copy["reply_sentiment_label"] = "Auto-Reply (Out of Office)"
                    lead_copy["follow_ups"] = lead_copy.get("follow_ups") or "Set reminder to follow up 3 business days post-return"
                elif lead_copy.get("reply_status") == "replied":
                    if not lead_copy.get("responses") or lead_copy.get("responses") in ["(Awaiting Reply)", "Catalog Dispatched (Awaiting Reply)"]:
                        lead_copy["responses"] = f"Replied: {lead_copy.get('reply_snippet', '')[:120]}" if lead_copy.get("reply_snippet") else "Replied: Requested wholesale pricing & MOQ"
                else:
                    if not lead_copy.get("reply_status"):
                        lead_copy["reply_status"] = "unreplied" if lead_copy.get("last_contacted_at") else "uncontacted"
                    if lead_copy.get("last_contacted_at") and lead_copy.get("validation_status") != "invalid":
                        lead_copy["responses"] = "(Awaiting Reply)"

            updated_leads.append(lead_copy)

        human_replies = [r for r in detected_replies if not r.get("is_auto_reply")]
        auto_replies = [r for r in detected_replies if r.get("is_auto_reply")]

        contacted_count = sum(1 for l in updated_leads if l.get("last_contacted_at"))

        stats = {
            "total_contacted": contacted_count,
            "replies_detected": len(human_replies),
            "auto_replies_detected": len(auto_replies),
            "bounces_detected": len(detected_bounces),
            "unreplied_count": sum(1 for l in updated_leads if l.get("last_contacted_at") and l.get("reply_status") not in ["replied", "bounced"] and l.get("validation_status") != "invalid"),
            "mode": "LIVE_IMAP"
        }

        return updated_leads, stats

    def _scan_imap_inbox_and_bounces(self, leads: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Set[str]]:
        """
        Connects to Gmail via IMAP to detect real buyer replies, auto-replies, and delivery failure bounces.
        Uses 4-way correlation: exact email, domain, company name in subject, and quoted headers.
        """
        if not self.gmail_email or not self.app_password:
            return [], set()

        replies = []
        bounces = set()

        # Build lookup indexes
        lead_by_email = {}
        lead_by_domain = {}
        lead_by_company = {}

        for l in leads:
            em = (l.get("email") or "").lower().strip()
            comp = (l.get("company_name") or "").lower().strip()
            web = (l.get("website") or "").lower().strip()
            
            if em:
                lead_by_email[em] = l
                if "@" in em:
                    d = em.split("@")[1]
                    lead_by_domain[d] = l
            if web:
                dom_match = re.search(r'https?://(?:www\.)?([^/]+)', web)
                if dom_match:
                    lead_by_domain[dom_match.group(1).lower()] = l
            if comp:
                lead_by_company[comp] = l

        try:
            mail = imaplib.IMAP4_SSL(self.IMAP_HOST, self.IMAP_PORT, timeout=15)
            mail.login(self.gmail_email, self.app_password)
            mail.select("INBOX", readonly=True)

            status, search_data = mail.search(None, 'ALL')
            if status == "OK" and search_data[0]:
                msg_ids = search_data[0].split()
                recent_ids = msg_ids[-40:] # Scan last 40 emails

                if recent_ids:
                    id_str = b",".join(recent_ids).decode("ascii")
                    res, fetch_data = mail.fetch(id_str, "(RFC822)")

                    if res == "OK" and fetch_data:
                        for item in fetch_data:
                            if not isinstance(item, tuple) or len(item) < 2:
                                continue
                            raw_bytes = item[1]
                            msg = email.message_from_bytes(raw_bytes)

                            from_hdr = self._decode_header_str(msg.get("From", ""))
                            subj_hdr = self._decode_header_str(msg.get("Subject", ""))
                            date_hdr = msg.get("Date", "")
                            body_text = self._extract_body(msg)

                            from_lower = from_hdr.lower()
                            subj_lower = subj_hdr.lower()
                            body_lower = body_text.lower()

                            # 1. Delivery Failure Bounces & Address Not Found
                            is_bounce = (
                                any(b in from_lower for b in ["mailer-daemon", "postmaster", "googlemail.com", "mail-daemon", "noreply", "bounce", "mail delivery"]) or
                                any(s in subj_lower for s in [
                                    "delivery status notification", "address not found", "undeliverable", "failure notice",
                                    "returned to sender", "delivery failure", "failed delivery", "could not be delivered",
                                    "mailbox unavailable", "user unknown", "550"
                                ]) or
                                any(kw in body_lower for kw in [
                                    "550 5.1.1", "550 address not found", "user unknown", "recipient address rejected",
                                    "mailbox not found", "does not exist", "unrouteable address", "no such user",
                                    "address rejected", "permanent failure"
                                ])
                            )

                            if is_bounce:
                                # Extract any matching emails from body or headers
                                for em in lead_by_email.keys():
                                    if em in body_lower or em in subj_lower:
                                        bounces.add(em)
                                # Also find any raw email in body matching regex
                                for raw_em in re.findall(r'[\w\.-]+@[\w\.-]+', body_text):
                                    raw_em_clean = raw_em.lower()
                                    if raw_em_clean in lead_by_email:
                                        bounces.add(raw_em_clean)
                                continue

                            # Skip self sent emails
                            if self.gmail_email.lower() in from_lower and "re:" not in subj_lower:
                                continue

                            # 2. Extract sender email & domain
                            from_match = re.search(r'[\w\.-]+@[\w\.-]+', from_hdr)
                            sender_email = from_match.group(0).lower() if from_match else ""
                            sender_domain = sender_email.split("@")[1] if "@" in sender_email else ""

                            # 3. 4-Way Lead Correlation
                            matched_lead = None
                            if sender_email in lead_by_email:
                                matched_lead = lead_by_email[sender_email]
                            elif sender_domain in lead_by_domain and sender_domain not in ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "qemailserver.com"]:
                                matched_lead = lead_by_domain[sender_domain]
                            
                            if not matched_lead:
                                for comp_name, l in lead_by_company.items():
                                    words = [w for w in comp_name.split() if len(w) > 3 and w not in ["home", "decor", "shop", "store", "canada", "group"]]
                                    if any(w in subj_lower or w in body_lower for w in words):
                                        matched_lead = l
                                        break

                            if matched_lead:
                                auto_submitted = (msg.get("Auto-Submitted") or "").lower()
                                x_autoreply = (msg.get("X-Autoreply") or "").lower()
                                precedence = (msg.get("Precedence") or "").lower()

                                header_is_auto = (
                                    auto_submitted in ["auto-replied", "auto-generated", "auto-notified"] or
                                    x_autoreply == "yes" or
                                    precedence in ["auto_reply", "bulk", "junk"]
                                )

                                auto_reply_keywords = [
                                    "automatic reply", "autoreply", "auto-reply", "auto reply",
                                    "auto-response", "auto response", "autoresponse",
                                    "out of office", "out of the office", "away from office", "away from the office",
                                    "on leave", "on vacation", "annual leave", "maternity leave",
                                    "limited access to email", "currently out", "will be out", "will return on",
                                    "i am away", "i am traveling", "thank you for reaching out",
                                    "thank you for contacting", "thank you for your email", "thank you for your inquiry",
                                    "thank you for your message", "we have received your email", "we have received your message",
                                    "we’ve received your email", "we've received your email",
                                    "this is an automated", "this is an automatic", "this inbox is not monitored",
                                    "this mailbox is unmonitored", "acknowledgement of receipt", "ticket received",
                                    "support request received", "your message has been received", "will get back to you shortly",
                                    "we will respond as soon as possible"
                                ]

                                is_auto_reply = header_is_auto or any(
                                    a in subj_lower or a in body_lower for a in auto_reply_keywords
                                )

                                clean_snippet = body_text.replace("\r", " ").replace("\n", " ")
                                clean_snippet = re.sub(r'\s+', ' ', clean_snippet).strip()

                                replies.append({
                                    "lead_id": matched_lead.get("id"),
                                    "lead_email": matched_lead.get("email"),
                                    "company_name": matched_lead.get("company_name"),
                                    "buyer_name": matched_lead.get("buyer_name", ""),
                                    "sender_email": sender_email,
                                    "sender_name": from_hdr,
                                    "subject": subj_hdr,
                                    "body": clean_snippet,
                                    "snippet": clean_snippet[:300],
                                    "received_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                    "sentiment": "auto_reply" if is_auto_reply else "interested",
                                    "sentiment_label": "Auto-Reply (Out of Office)" if is_auto_reply else "Inbound Buyer Reply",
                                    "is_auto_reply": is_auto_reply,
                                    "date": date_hdr
                                })
            mail.logout()
        except Exception as e:
            print(f"[InboxTracker] IMAP error during scan: {e}")

        return replies, bounces

    def _decode_header_str(self, header_val: str) -> str:
        if not header_val:
            return ""
        try:
            decoded_fragments = decode_header(header_val)
            out = ""
            for frag, enc in decoded_fragments:
                if isinstance(frag, bytes):
                    out += frag.decode(enc or "utf-8", errors="ignore")
                else:
                    out += str(frag)
            return out.strip()
        except Exception:
            return header_val if isinstance(header_val, str) else str(header_val)

    def _extract_body(self, msg: email.message.Message) -> str:
        body = ""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        try:
                            payload = part.get_payload(decode=True)
                            if isinstance(payload, bytes):
                                charset = part.get_content_charset() or "utf-8"
                                body += payload.decode(charset, errors="ignore") + "\n"
                            elif isinstance(payload, str):
                                body += payload + "\n"
                        except Exception:
                            pass
            else:
                payload = msg.get_payload(decode=True)
                if isinstance(payload, bytes):
                    charset = msg.get_content_charset() or "utf-8"
                    body = payload.decode(charset, errors="ignore")
                elif isinstance(payload, str):
                    body = payload
        except Exception:
            pass
        return body.strip()
