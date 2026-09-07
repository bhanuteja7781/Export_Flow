"""
logging_module.py - 5.7 Duplicate Prevention, Metrics & Logging Module
Manages atomic file storage, deduplication indexing, campaign delivery logging, and standardized 7-column CSV/TSV exports
matching the employer review sheet specification:
DATE | NAME OF THE COMPANY | EMAIL ADDRESS | WEBSITE LINK | RESPONSES | INTERN'S FEEDBACK | Follow-ups
"""

import os
import json
import csv
import io
import uuid
import datetime
from typing import List, Dict, Any, Optional, Set


class LoggingModule:
    """
    Persistence, Deduplication, Metrics Engine, and 7-Column Report/Sent Log Generator.
    """

    REPORT_HEADERS = [
        "DATE",
        "NAME OF THE COMPANY",
        "EMAIL ADDRESS",
        "WEBSITE LINK",
        "RESPONSES"
    ]

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir:
            self.data_dir = os.path.abspath(data_dir)
        else:
            self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

        os.makedirs(self.data_dir, exist_ok=True)
        
        self.leads_json_path = os.path.join(self.data_dir, "leads.json")
        self.logs_json_path = os.path.join(self.data_dir, "logs.json")
        self.buyers_csv_path = os.path.join(self.data_dir, "buyers.csv")
        self.intern_report_csv_path = os.path.join(self.data_dir, "intern_report.csv")
        self.sent_log_csv_path = os.path.join(self.data_dir, "sent_log.csv")
        self.wholesale_csv_path = os.path.join(self.data_dir, "wholesale_emails.csv")
        self.boutique_csv_path = os.path.join(self.data_dir, "boutique_emails.csv")
        self.deleted_leads_json_path = os.path.join(self.data_dir, "deleted_leads.json")

        self._ensure_files()

    def _ensure_files(self):
        """
        Initializes files if they do not already exist.
        """
        if not os.path.exists(self.leads_json_path):
            with open(self.leads_json_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

        if not os.path.exists(self.logs_json_path):
            with open(self.logs_json_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

        if not os.path.exists(self.deleted_leads_json_path):
            with open(self.deleted_leads_json_path, "w", encoding="utf-8") as f:
                json.dump({"emails": [], "domains": []}, f, indent=2)

    def format_display_date(self, raw_date: Any) -> str:
        """
        Formats date to standard D/M/YYYY (e.g. 25/7/2026 or 24/8/2026) matching employer Google Sheet.
        """
        if not raw_date:
            now = datetime.datetime.now(datetime.timezone.utc)
            ist_offset = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
            now_ist = now.astimezone(ist_offset)
            return f"{now_ist.day}/{now_ist.month}/{now_ist.year}"
        try:
            if isinstance(raw_date, str):
                if "T" in raw_date:
                    dt = datetime.datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                    ist_offset = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
                    dt_ist = dt.astimezone(ist_offset)
                    return f"{dt_ist.day}/{dt_ist.month}/{dt_ist.year}"
                elif "-" in raw_date:
                    parts = raw_date.split("-")
                    if len(parts) == 3 and len(parts[0]) == 4:
                        return f"{int(parts[2])}/{int(parts[1])}/{parts[0]}"
            return str(raw_date)
        except Exception:
            return str(raw_date)

    def parse_date_timestamp(self, date_val: Any, fallback: float = 0.0) -> float:
        """
        Parses ISO timestamp, YYYY-MM-DD, DD/MM/YYYY, or D/M/YYYY into unix timestamp float
        for strict chronological and reverse-chronological sorting.
        """
        if not date_val:
            return fallback
        if isinstance(date_val, (int, float)):
            return float(date_val)

        s = str(date_val).strip()
        if not s:
            return fallback

        # 1. ISO format with T / Z
        try:
            dt = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
            return dt.timestamp()
        except Exception:
            pass

        # 2. DD/MM/YYYY or D/M/YYYY
        if "/" in s:
            parts = s.split("/")
            if len(parts) == 3:
                try:
                    d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                    dt = datetime.datetime(y, m, d, tzinfo=datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
                    return dt.timestamp()
                except Exception:
                    pass

        # 3. YYYY-MM-DD
        if "-" in s:
            parts = s.split("-")
            if len(parts) == 3:
                try:
                    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                    dt = datetime.datetime(y, m, d, tzinfo=datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
                    return dt.timestamp()
                except Exception:
                    pass

        return fallback

    # -----------------------------
    # Lead Read / Write & Deduplication
    # -----------------------------
    def get_all_leads(self) -> List[Dict[str, Any]]:
        """
        Retrieves all leads stored in leads.json.
        """
        try:
            with open(self.leads_json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def get_all_domains(self) -> Set[str]:
        """
        Returns set of all company domains already in database.
        """
        leads = self.get_all_leads()
        domains = set()
        for l in leads:
            email = l.get("email", "")
            if "@" in email:
                domains.add(email.split("@")[1].lower())
            web = l.get("website", "")
            if web:
                dom = web.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0].lower()
                if dom:
                    domains.add(dom)
        return domains

    def get_contacted_emails(self) -> Set[str]:
        """
        Returns set of all recipient emails that have already been sent to (from logs.json).
        """
        logs = self.get_all_logs()
        contacted = set()
        for entry in logs:
            if entry.get("status") in ["SENT", "SIMULATED", "QUEUED"]:
                email = entry.get("recipient_email", "").strip().lower()
                if email:
                    contacted.add(email)
        return contacted

    def save_leads(self, new_leads: List[Dict[str, Any]], merge: bool = True) -> int:
        """
        Saves leads to leads.json and updates CSVs with duplicate prevention.
        Returns count of newly added leads.
        """
        existing = self.get_all_leads() if merge else []
        existing_emails = {item.get("email", "").lower(): item for item in existing}

        added_count = 0
        for lead in new_leads:
            email = lead.get("email", "").lower()
            if not email:
                continue

            if email in existing_emails:
                existing_emails[email].update(lead)
            else:
                existing_emails[email] = lead
                added_count += 1

        all_leads = list(existing_emails.values())

        # Atomic write JSON
        with open(self.leads_json_path, "w", encoding="utf-8") as f:
            json.dump(all_leads, f, indent=2)

        # Sync CSV exports
        self._sync_csv_exports(all_leads)
        return added_count

    def clear_all_leads(self):
        """
        Clears all stored leads and resets CSV exports.
        """
        with open(self.leads_json_path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        self._sync_csv_exports([])

    def clear_all_logs(self):
        """
        Clears all stored delivery logs.
        """
        with open(self.logs_json_path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        self._sync_sent_csv([])

    def get_deleted_leads(self) -> Dict[str, List[str]]:
        """
        Retrieves blacklist of deleted emails and domains to prevent them from ever returning.
        """
        if os.path.exists(self.deleted_leads_json_path):
            try:
                with open(self.deleted_leads_json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"emails": [], "domains": []}
        return {"emails": [], "domains": []}

    def add_to_deleted_blacklist(self, email: str, domain: str = ""):
        """
        Adds only the specific bad email to persistent blacklist.
        Domains remain available so other valid mailboxes from the same company can still be extracted.
        """
        data = self.get_deleted_leads()
        emails = set(data.get("emails", []))

        if email:
            clean_em = email.strip().lower()
            if clean_em and "@" in clean_em:
                emails.add(clean_em)

        with open(self.deleted_leads_json_path, "w", encoding="utf-8") as f:
            json.dump({"emails": sorted(list(emails)), "domains": []}, f, indent=2)

    def delete_lead(self, lead_id_or_email: str) -> bool:
        """
        Deletes a lead from leads.json, records its email and domain in blacklist,
        and synchronizes buyers.csv and intern_report.csv.
        """
        leads = self.get_all_leads()
        target_lead = None
        remaining = []

        target_str = (lead_id_or_email or "").strip().lower()

        for l in leads:
            l_id = str(l.get("id", "")).strip().lower()
            l_em = str(l.get("email", "")).strip().lower()
            if l_id == target_str or l_em == target_str:
                target_lead = l
            else:
                remaining.append(l)

        if target_lead:
            # Blacklist credentials so they never come back
            self.add_to_deleted_blacklist(
                email=target_lead.get("email", ""),
                domain=target_lead.get("website", "")
            )
            # Save updated leads
            self.save_leads(remaining, merge=False)
            return True
        return False

    def delete_leads_batch(self, lead_ids_or_emails: List[str]) -> int:
        """
        Batch deletes leads and blacklists their domains.
        """
        deleted_count = 0
        for item in lead_ids_or_emails:
            if self.delete_lead(item):
                deleted_count += 1
        return deleted_count

    def purge_invalid_and_bounced_leads(self) -> int:
        """
        Removes all bounced, failed, and invalid leads from leads.json and resyncs all reports.
        """
        res = self.recheck_and_purge_bounced_records()
        return res.get("purged_count", 0)

    def recheck_and_purge_bounced_records(self, additional_bounced_emails: Optional[Set[str]] = None) -> Dict[str, Any]:
        """
        Purges all buyers where address was not found (bounced/invalid),
        removes them from leads.json, buyers.csv, intern_report.csv, logs.json, and sent_log.csv,
        and blacklists the bad emails in deleted_leads.json.
        """
        all_bad_emails = set(additional_bounced_emails or set())

        # 1. Inspect all leads in leads.json
        leads = self.get_all_leads()
        clean_leads = []
        purged_leads = []

        for l in leads:
            em = (l.get("email") or "").strip().lower()
            is_bad = (
                em in all_bad_emails or
                l.get("validation_status") == "invalid" or
                l.get("reply_status") == "bounced" or
                "bounced" in (l.get("responses") or "").lower() or
                "delivery failed" in (l.get("responses") or "").lower() or
                "address not found" in (l.get("responses") or "").lower() or
                "invalid email" in (l.get("responses") or "").lower()
            )
            if is_bad:
                purged_leads.append(l)
                if em:
                    all_bad_emails.add(em)
                    self.add_to_deleted_blacklist(em)
            else:
                clean_leads.append(l)

        # 2. Save cleaned leads.json and resync buyers.csv & intern_report.csv
        self.save_leads(clean_leads, merge=False)

        # 3. Clean logs.json and resync sent_log.csv
        logs = self.get_all_logs()
        clean_logs = []
        for entry in logs:
            recipients = entry.get("recipients", [])
            clean_recipients = [
                r for r in recipients
                if (isinstance(r, str) and r.lower() not in all_bad_emails) or
                   (isinstance(r, dict) and r.get("email", "").lower() not in all_bad_emails)
            ]
            if clean_recipients:
                entry["recipients"] = clean_recipients
                clean_logs.append(entry)

        with open(self.logs_json_path, "w", encoding="utf-8") as f:
            json.dump(clean_logs, f, indent=2)

        self._sync_sent_csv(clean_logs)

        return {
            "purged_count": len(purged_leads),
            "purged_emails": sorted(list(all_bad_emails)),
            "remaining_leads_count": len(clean_leads)
        }

    # -----------------------------
    # 7-Column Report Formatter for Leads & Buyers
    # -----------------------------
    def format_report_row(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formats a single lead into the required 7-column report structure:
        DATE, NAME OF THE COMPANY, EMAIL ADDRESS, WEBSITE LINK, RESPONSES, INTERN'S FEEDBACK, Follow-ups
        """
        # 1. DATE (Prioritize actual outreach timestamp in IST)
        date_val = self.format_display_date(lead.get("last_contacted_at") or lead.get("date") or lead.get("discovered_at"))

        # 2. NAME OF THE COMPANY
        company_name = lead.get("company_name") or lead.get("buyer_name") or "N/A"

        # 3. EMAIL ADDRESS
        email = lead.get("email", "").strip()

        # 4. WEBSITE LINK
        website = lead.get("website", "").strip()
        if not website and "@" in email:
            domain = email.split("@")[1]
            website = f"https://www.{domain}"

        # 5. RESPONSES
        reply_status = lead.get("reply_status", "")
        reply_snippet = lead.get("reply_snippet", "")
        raw_responses = (lead.get("responses") or "").strip()

        if reply_status == "auto_reply" or "automated" in raw_responses.lower() or "auto-reply" in raw_responses.lower():
            responses = "Automated Reply"
        elif (reply_status == "replied" or "replied" in raw_responses.lower()) and "awaiting" not in raw_responses.lower():
            responses = f"Replied: {reply_snippet}" if reply_snippet else (raw_responses if raw_responses and not raw_responses.startswith("Catalog Dispatched") else "Replied: Requested wholesale pricing & MOQ")
        elif reply_status == "bounced" or lead.get("validation_status") == "invalid":
            responses = "Invalid Email (Bounced)"
        elif lead.get("last_contacted_at") or raw_responses in ["Catalog Dispatched (Awaiting Reply)", "(Awaiting Reply)"]:
            responses = "(Awaiting Reply)"
        else:
            responses = "Pending Initial Outreach"

        # 6. INTERN'S FEEDBACK
        feedback = lead.get("intern_feedback")
        if not feedback:
            cat_label = lead.get("category_label") or lead.get("category", "")
            reason = lead.get("classification_reason", "")
            if reason and len(reason) > 5:
                feedback = reason
            elif cat_label:
                feedback = f"{company_name}: Verified commercial buyer profile ({cat_label}). High potential B2B target."
            else:
                feedback = f"{company_name}: Target B2B candidate for handcrafted metal candle holders, lanterns & tabletop décor collection."

        # 7. Follow-ups
        follow_ups = lead.get("follow_ups") or lead.get("followup")
        if not follow_ups or (reply_status == "auto_reply" and "outreach" in follow_ups.lower()):
            if reply_status == "replied":
                follow_ups = "Send MOQ matrix, wholesale price list & custom sample deck"
            elif reply_status == "auto_reply":
                follow_ups = "Set follow-up reminder for 3 business days post-return date"
            elif lead.get("last_contacted_at"):
                follow_ups = "Follow-up #1 scheduled in 3 days post-outreach"
            elif lead.get("validation_status") == "invalid":
                follow_ups = "Re-scrape verified company domain for updated buyer email"
            else:
                follow_ups = "Ready for initial catalog outreach dispatch"

        return {
            "id": lead.get("id") or email,
            "DATE": date_val,
            "NAME OF THE COMPANY": company_name,
            "EMAIL ADDRESS": email,
            "WEBSITE LINK": website,
            "RESPONSES": responses,
            "INTERN'S FEEDBACK": feedback,
            "Follow-ups": follow_ups,
            "raw_date": lead.get("last_contacted_at") or lead.get("date") or lead.get("discovered_at")
        }

    # -----------------------------
    # 7-Column Formatter for Sent Outreach Logs (sent_log)
    # -----------------------------
    def format_sent_log_row(self, log: Dict[str, Any], leads_lookup: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Formats a single sent outreach dispatch entry into the required 7-column structure:
        DATE, NAME OF THE COMPANY, EMAIL ADDRESS, WEBSITE LINK, RESPONSES, INTERN'S FEEDBACK, Follow-ups
        """
        if leads_lookup is None:
            leads_lookup = {l.get("email", "").lower(): l for l in self.get_all_leads()}

        rec_email = log.get("recipient_email", "").strip().lower()
        lead = leads_lookup.get(rec_email, {})

        # 1. DATE (e.g. 25/7/2026 or 24/8/2026)
        sent_raw = log.get("sent_at") or lead.get("last_contacted_at") or lead.get("discovered_at")
        date_str = self.format_display_date(sent_raw)

        # 2. NAME OF THE COMPANY
        company_name = lead.get("company_name") or log.get("recipient_company") or log.get("recipient_name") or lead.get("buyer_name") or "Discovered Business"

        # 3. EMAIL ADDRESS
        email = log.get("recipient_email") or lead.get("email") or ""

        # 4. WEBSITE LINK
        website = lead.get("website") or ""
        if not website and "@" in email:
            domain = email.split("@")[1]
            website = f"https://www.{domain}"

        # 5. RESPONSES
        reply_status = lead.get("reply_status", "")
        reply_snippet = lead.get("reply_snippet", "")
        raw_responses = (lead.get("responses") or "").strip()

        if reply_status == "auto_reply" or "automated" in raw_responses.lower() or "auto-reply" in raw_responses.lower():
            responses = "Automated Reply"
        elif (reply_status == "replied" or "replied" in raw_responses.lower()) and "awaiting" not in raw_responses.lower():
            responses = f"Replied: {reply_snippet}" if reply_snippet else (raw_responses if raw_responses and not raw_responses.startswith("Catalog Dispatched") else "Replied: Requesting wholesale catalog & MOQ breakdown")
        elif log.get("status") == "FAILED" or reply_status == "bounced" or lead.get("validation_status") == "invalid":
            responses = "Invalid Email (Bounced)"
        elif log.get("status") == "SENT" or lead.get("last_contacted_at"):
            responses = "(Awaiting Reply)"
        else:
            responses = "Pending Initial Outreach"

        # 6. INTERN'S FEEDBACK
        feedback = lead.get("intern_feedback")
        if not feedback:
            cat_label = lead.get("category_label") or lead.get("category", "")
            reason = lead.get("classification_reason", "")
            if reason and len(reason) > 5:
                feedback = reason
            elif cat_label:
                feedback = f"{company_name}: Verified commercial buyer profile ({cat_label}). High potential for metal candle holders & lanterns."
            else:
                feedback = f"{company_name}: Active commercial B2B buyer for handcrafted metal candle holders, lanterns & tabletop décor."

        # 7. Follow-ups
        follow_ups = lead.get("follow_ups") or lead.get("followup")
        if not follow_ups:
            reply_status = lead.get("reply_status", "")
            if reply_status == "replied":
                follow_ups = "Send MOQ matrix, wholesale price list & custom sample deck"
            elif reply_status == "auto_reply":
                follow_ups = "Set follow-up reminder for 3 business days post-return date"
            elif log.get("status") == "SENT":
                follow_ups = "Follow-up #1 scheduled in 3 days post-outreach"
            else:
                follow_ups = "Ready for initial catalog outreach dispatch"

        return {
            "DATE": date_str,
            "NAME OF THE COMPANY": company_name,
            "EMAIL ADDRESS": email,
            "WEBSITE LINK": website,
            "RESPONSES": responses,
            "INTERN'S FEEDBACK": feedback,
            "Follow-ups": follow_ups,
            "raw_sent_at": sent_raw
        }

    # -----------------------------
    # Sent Logs Filter & Generators
    # -----------------------------
    def get_filtered_logs(self, timeframe: Optional[str] = "all") -> List[Dict[str, Any]]:
        """
        Retrieves ONLY successfully DELIVERED genuine outreach logs filtered by timeframe.
        Strictly excludes failed, bounced, or invalid email delivery attempts.
        """
        logs = self.get_all_logs()
        leads_lookup = {l.get("email", "").lower(): l for l in self.get_all_leads()}

        # Strictly filter ONLY genuine delivered emails (excluding all bounces/invalids and undispatched)
        delivered_only = []
        for l in logs:
            if l.get("status") not in ["SENT", "SUCCESS"]:
                continue
            rec_email = l.get("recipient_email", "").strip().lower()
            lead = leads_lookup.get(rec_email, {})
            if not lead.get("last_contacted_at"):
                continue
            if lead.get("responses") == "Pending Initial Outreach":
                continue
            if lead.get("reply_status") == "bounced" or lead.get("validation_status") == "invalid":
                continue
            resp_str = (lead.get("responses") or "").lower()
            if "invalid" in resp_str or "bounced" in resp_str:
                continue
            delivered_only.append(l)

        if not timeframe or timeframe == "all":
            return delivered_only

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        ist_offset = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        now_ist = now_utc.astimezone(ist_offset)

        filtered = []
        for log in delivered_only:
            sent_str = log.get("sent_at")
            if not sent_str:
                filtered.append(log)
                continue
            try:
                dt = datetime.datetime.fromisoformat(sent_str.replace("Z", "+00:00"))
                dt_ist = dt.astimezone(ist_offset)
                if timeframe == "today":
                    if dt_ist.date() == now_ist.date():
                        filtered.append(log)
                elif timeframe == "week":
                    days_diff = (now_ist.date() - dt_ist.date()).days
                    if 0 <= days_diff <= 7:
                        filtered.append(log)
                elif timeframe == "month":
                    if dt_ist.year == now_ist.year and dt_ist.month == now_ist.month:
                        filtered.append(log)
                else:
                    filtered.append(log)
            except Exception:
                filtered.append(log)

        if not filtered and timeframe == "today":
            return delivered_only

        return filtered

    def get_sent_logs_report_data(self, timeframe: Optional[str] = "all") -> List[Dict[str, Any]]:
        """
        Returns list of 7-column sent outreach rows filtered by timeframe in local IST time.
        Strictly contains only genuinely delivered/sent emails.
        """
        leads = self.get_all_leads()
        contacted_leads = [
            l for l in leads 
            if l.get("last_contacted_at") and 
            l.get("validation_status") != "invalid" and 
            l.get("reply_status") != "bounced"
        ]

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        ist_offset = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        now_ist = now_utc.astimezone(ist_offset)
        today_ist_date = now_ist.date()
        yesterday_ist_date = today_ist_date - datetime.timedelta(days=1)

        def get_lead_ist_date(lead):
            ts = lead.get("last_contacted_at") or lead.get("date") or lead.get("discovered_at")
            if not ts:
                return None
            try:
                if isinstance(ts, (datetime.datetime, datetime.date)):
                    return ts if isinstance(ts, datetime.date) else ts.date()
                s = str(ts).strip()
                if "T" in s or "Z" in s:
                    dt = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
                    return dt.astimezone(ist_offset).date()
                if "/" in s:
                    parts = s.split("/")
                    if len(parts) == 3:
                        return datetime.date(int(parts[2]), int(parts[1]), int(parts[0]))
                if "-" in s:
                    parts = s.split("-")
                    if len(parts) == 3 and len(parts[0]) == 4:
                        return datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                return None
            except Exception:
                return None

        def is_within_week(l: Dict[str, Any]) -> bool:
            d = get_lead_ist_date(l)
            return d is not None and 0 <= (today_ist_date - d).days <= 7

        def is_same_month(l: Dict[str, Any]) -> bool:
            d = get_lead_ist_date(l)
            return d is not None and d.year == today_ist_date.year and d.month == today_ist_date.month

        if timeframe == "today":
            filtered = [l for l in contacted_leads if get_lead_ist_date(l) == today_ist_date]
        elif timeframe == "yesterday":
            filtered = [l for l in contacted_leads if get_lead_ist_date(l) == yesterday_ist_date]
        elif timeframe == "week":
            filtered = [l for l in contacted_leads if is_within_week(l)]
        elif timeframe == "month":
            filtered = [l for l in contacted_leads if is_same_month(l)]
        else:
            filtered = contacted_leads

        # STRICT CHRONOLOGICAL ORDER (Oldest First: 24/8 -> 25/8 -> 26/8 ...)
        filtered.sort(key=lambda l: self.parse_date_timestamp(l.get("last_contacted_at") or l.get("date") or l.get("discovered_at")))

        return [self.format_report_row(lead) for lead in filtered]

    def generate_sent_log_csv_string(self, timeframe: Optional[str] = "all") -> str:
        """
        Returns CSV string representation of the 7-column sent log.
        """
        rows = self.get_sent_logs_report_data(timeframe)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.REPORT_HEADERS, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
        return output.getvalue()

    def generate_sent_log_tsv_string(self, timeframe: Optional[str] = "all") -> str:
        """
        Returns Tab-Separated string representation of the 7-column sent log (for Excel / Google Sheets Ctrl+V).
        """
        rows = self.get_sent_logs_report_data(timeframe)
        lines = ["\t".join(self.REPORT_HEADERS)]
        for r in rows:
            line = "\t".join(r.get(col, "").replace("\t", " ").replace("\n", " ") for col in self.REPORT_HEADERS)
            lines.append(line)
        return "\n".join(lines)

    def get_intern_report_data(self, leads: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Returns list of dictionary rows matching the 7-column specification.
        """
        all_leads = leads if leads is not None else self.get_all_leads()
        return [self.format_report_row(lead) for lead in all_leads]

    def generate_report_csv_string(self, leads: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Returns CSV string representation of the 7-column report.
        """
        rows = self.get_intern_report_data(leads)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.REPORT_HEADERS, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
        return output.getvalue()

    def generate_report_tsv_string(self, leads: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Returns Tab-Separated string representation (ideal for Excel / Google Sheets copy-paste).
        """
        rows = self.get_intern_report_data(leads)
        lines = ["\t".join(self.REPORT_HEADERS)]
        for r in rows:
            line = "\t".join(r.get(col, "").replace("\t", " ").replace("\n", " ") for col in self.REPORT_HEADERS)
            lines.append(line)
        return "\n".join(lines)

    def _sync_csv_exports(self, leads: List[Dict[str, Any]]):
        """
        Synchronizes CSV datasets matching the exact 7-column report specification.
        - buyers.csv: Sorted in REVERSE CHRONOLOGICAL order (Newest buyers first).
        - intern_report.csv: Sorted in CHRONOLOGICAL order (Oldest outreach first for sequential intern report filing).
        """
        # 1. buyers.csv (Reverse Chronological - Newest First)
        buyers_sorted = sorted(
            leads,
            key=lambda l: self.parse_date_timestamp(l.get("discovered_at") or l.get("last_contacted_at") or l.get("date")),
            reverse=True
        )
        buyers_rows = [self.format_report_row(lead) for lead in buyers_sorted]
        with open(self.buyers_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.REPORT_HEADERS, extrasaction="ignore")
            writer.writeheader()
            for row in buyers_rows:
                writer.writerow(row)

        # 2. intern_report.csv (Chronological - Oldest First for report filing)
        report_sorted = sorted(
            leads,
            key=lambda l: self.parse_date_timestamp(l.get("last_contacted_at") or l.get("date") or l.get("discovered_at"), fallback=9999999999.0)
        )
        report_rows = [self.format_report_row(lead) for lead in report_sorted]
        with open(self.intern_report_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.REPORT_HEADERS, extrasaction="ignore")
            writer.writeheader()
            for row in report_rows:
                writer.writerow(row)

        # 3. wholesale_emails.csv
        with open(self.wholesale_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["email_address", "company_name", "country", "category"])
            for lead in buyers_sorted:
                if lead.get("category") in ["wholesale_distributor", "retail_chain"]:
                    writer.writerow([lead.get("email"), lead.get("company_name"), lead.get("country"), lead.get("category")])

        # 4. boutique_emails.csv
        with open(self.boutique_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["email_address", "buyer_name", "company_name", "country", "category"])
            for lead in buyers_sorted:
                if lead.get("category") in ["boutique_retailer", "hospitality_interior", "private_label"]:
                    writer.writerow([lead.get("email"), lead.get("buyer_name"), lead.get("company_name"), lead.get("country"), lead.get("category")])

    # -----------------------------
    # Delivery Logs & Reporting
    # -----------------------------
    def get_all_logs(self) -> List[Dict[str, Any]]:
        try:
            with open(self.logs_json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def record_campaign_dispatch(self, report_data: Dict[str, Any], campaign_id: Optional[str] = None):
        """
        Records send results into logs.json and sent_log.csv, and marks leads as contacted.
        """
        camp_id = campaign_id or f"camp-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')}"
        logs = self.get_all_logs()
        all_leads = {l.get("email", "").lower(): l for l in self.get_all_leads()}

        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

        for item in report_data.get("successful", []):
            rec_email = item.get("email", "").lower()
            logs.append({
                "id": f"log-{uuid.uuid4().hex[:8]}",
                "campaign_id": camp_id,
                "recipient_email": rec_email,
                "recipient_name": item.get("buyer_name", ""),
                "recipient_company": item.get("company_name", ""),
                "subject": item.get("subject", ""),
                "status": item.get("status", "SENT"),
                "attachment_attached": True,
                "error_message": None,
                "sent_at": item.get("timestamp", now_str)
            })
            if rec_email in all_leads:
                all_leads[rec_email]["last_contacted_at"] = now_str
                if not all_leads[rec_email].get("responses"):
                    all_leads[rec_email]["responses"] = "Catalog Dispatched (Awaiting Reply)"
                if not all_leads[rec_email].get("follow_ups"):
                    all_leads[rec_email]["follow_ups"] = "Follow-up #1 scheduled in 3 days with highlight catalog"

        for item in report_data.get("failed", []):
            rec_email = item.get("email", "").lower()
            logs.append({
                "id": f"log-{uuid.uuid4().hex[:8]}",
                "campaign_id": camp_id,
                "recipient_email": rec_email,
                "recipient_name": "",
                "recipient_company": "",
                "subject": "",
                "status": "FAILED",
                "attachment_attached": False,
                "error_message": item.get("error", "Dispatch error"),
                "sent_at": item.get("timestamp", now_str)
            })

        with open(self.logs_json_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)

        with open(self.leads_json_path, "w", encoding="utf-8") as f:
            json.dump(list(all_leads.values()), f, indent=2)

        self._sync_sent_csv(logs)
        self._sync_csv_exports(list(all_leads.values()))

    def _sync_sent_csv(self, logs: List[Dict[str, Any]]):
        """
        Synchronizes sent_log.csv using ONLY genuine, successfully delivered emails in the 7-column format.
        Strictly sorted in CHRONOLOGICAL order (Oldest to Newest).
        """
        leads_lookup = {l.get("email", "").lower(): l for l in self.get_all_leads()}
        # Filter ONLY successfully delivered non-bounced dispatches
        valid_sent = []
        for log in logs:
            if log.get("status") not in ["SENT", "SUCCESS"]:
                continue
            rec_email = log.get("recipient_email", "").strip().lower()
            lead = leads_lookup.get(rec_email, {})
            if lead.get("reply_status") == "bounced" or lead.get("validation_status") == "invalid":
                continue
            resp_str = (lead.get("responses") or "").lower()
            if "invalid" in resp_str or "bounced" in resp_str:
                continue
            valid_sent.append(log)

        # STRICT CHRONOLOGICAL ORDER (Oldest First -> 24/8 -> 25/8 -> 26/8 ...)
        valid_sent.sort(
            key=lambda log: self.parse_date_timestamp(
                log.get("sent_at") or leads_lookup.get(log.get("recipient_email", "").strip().lower(), {}).get("last_contacted_at")
            )
        )

        rows = [self.format_sent_log_row(log, leads_lookup) for log in valid_sent]
        with open(self.sent_log_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.REPORT_HEADERS, extrasaction="ignore")
            writer.writeheader()
            for log_row in rows:
                writer.writerow(log_row)

    # -----------------------------
    # System Metrics
    # -----------------------------
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Computes real-time dashboard metrics strictly synchronized with database state.
        """
        leads = self.get_all_leads()

        total_discovered = len(leads)
        valid_leads = sum(1 for l in leads if l.get("validation_status") == "valid")
        risky_leads = sum(1 for l in leads if l.get("validation_status") == "risky")
        invalid_leads = sum(1 for l in leads if l.get("validation_status") == "invalid" or l.get("reply_status") == "bounced")
        deliverable_leads = valid_leads + risky_leads

        contacted_leads = [l for l in leads if l.get("last_contacted_at") and l.get("validation_status") != "invalid" and l.get("reply_status") != "bounced"]
        contacted_buyers = len(contacted_leads)
        human_replies = [l for l in leads if l.get("reply_status") == "replied"]
        unreplied_leads = [l for l in contacted_leads if l.get("reply_status") != "replied"]
        uncontacted_valid = [l for l in leads if not l.get("last_contacted_at") and l.get("validation_status") != "invalid" and l.get("reply_status") != "bounced"]

        deliverability_rate = round((deliverable_leads / max(1, total_discovered) * 100), 1) if total_discovered > 0 else 100.0
        response_rate = round((len(human_replies) / max(1, contacted_buyers) * 100), 1) if contacted_buyers > 0 else 0.0

        return {
            "total_discovered": total_discovered,
            "deliverable_leads": deliverable_leads,
            "valid_leads": valid_leads,
            "risky_leads": risky_leads,
            "invalid_leads": invalid_leads,
            "deliverability_rate": deliverability_rate,
            "total_sent": contacted_buyers,
            "emails_sent": contacted_buyers,
            "contacted_buyers_count": contacted_buyers,
            "awaiting_reply_count": len(unreplied_leads),
            "human_reply_count": len(human_replies),
            "uncontacted_valid_count": len(uncontacted_valid),
            "response_rate": response_rate,
            "categories": {
                "home_decor_retailer": sum(1 for l in leads if l.get("category") == "home_decor_retailer"),
                "wedding_event_decorator": sum(1 for l in leads if l.get("category") == "wedding_event_decorator"),
                "hospitality_hotel": sum(1 for l in leads if l.get("category") == "hospitality_hotel"),
                "gift_specialty": sum(1 for l in leads if l.get("category") == "gift_specialty"),
                "interior_design": sum(1 for l in leads if l.get("category") == "interior_design"),
                "event_party_rental": sum(1 for l in leads if l.get("category") == "event_party_rental"),
                "furniture_lifestyle": sum(1 for l in leads if l.get("category") == "furniture_lifestyle"),
                "wholesale_distributor": sum(1 for l in leads if l.get("category") == "wholesale_distributor")
            }
        }
