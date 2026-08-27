"""
gmail_module.py - Live Gmail SMTP Dispatcher & Rate Limiting
Handles secure TLS/SSL SMTP connections, personalized MIME message composition,
catalog attachment binding, auto-reconnect retry logic, and rate-limited live dispatch.
"""

import os
import time
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict, Any, Optional, Tuple

from modules.presentation_module import PresentationModule


class GmailDispatcherModule:
    """
    Gmail SMTP Campaign Dispatcher with rate limiting and automatic reconnection.
    """

    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT_TLS = 587
    SMTP_PORT_SSL = 465

    DEFAULT_SUBJECT_TEMPLATE = "Handcrafted {product} catalog for {company}"
    DEFAULT_BODY_TEMPLATE = """Hi there,

Hope you're having a great week!

I came across {company} and wanted to introduce Product Zone International. We manufacture handcrafted {product}, metal lanterns, and tabletop decor.

I've attached our 2026 catalog showcasing our complete collection and latest designs for your review.

Would love to know your thoughts on our pieces!

Warm regards,

Product Zone International
Email: {sender_email}
"""

    def __init__(
        self,
        gmail_email: Optional[str] = None,
        app_password: Optional[str] = None,
        monitor_cc: Optional[str] = None,
        send_delay: float = 2.0
    ):
        self.gmail_email = gmail_email or os.getenv("GMAIL_EMAIL", "")
        self.app_password = app_password or os.getenv("GMAIL_APP_PASSWORD", "")
        self.monitor_cc = monitor_cc or os.getenv("MONITOR_CC_EMAIL", "")
        self.send_delay = float(send_delay or os.getenv("SEND_DELAY_SECONDS", 2.0))
        self.presentation_handler = PresentationModule()
        self.smtp_connection: Optional[smtplib.SMTP] = None

    def _connect_smtp(self) -> smtplib.SMTP:
        """
        Establishes TLS SMTP connection and logs in with App Password credentials.
        """
        if not self.gmail_email or not self.app_password:
            raise ValueError("Gmail Email and App Password must be configured in Settings to send live campaigns.")

        context = ssl.create_default_context()
        server = smtplib.SMTP(self.SMTP_HOST, self.SMTP_PORT_TLS, timeout=20)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(self.gmail_email, self.app_password)
        return server

    def _close_smtp(self):
        """
        Safely closes SMTP session.
        """
        if self.smtp_connection:
            try:
                self.smtp_connection.quit()
            except Exception:
                pass
            self.smtp_connection = None

    def compose_email(
        self,
        recipient: Dict[str, Any],
        subject_template: str,
        body_template: str,
        attach_presentation: bool = True
    ) -> Tuple[MIMEMultipart, str]:
        """
        Composes MIME email with personalized variables and catalog attachment.
        """
        company_name = recipient.get("company_name") or "Your Company"
        product = recipient.get("product_niche") or os.getenv("SEARCH_KEYWORD", "Metal Candle Holders")
        country = recipient.get("country") or "North America"
        sender_email = self.gmail_email or "export@productzoneintl.com"

        replacements = {
            "{{name}}": "there",
            "{name}": "there",
            "{{buyer_name}}": "there",
            "{buyer_name}": "there",
            "{{company}}": company_name,
            "{company}": company_name,
            "{{company_name}}": company_name,
            "{company_name}": company_name,
            "{{product}}": product,
            "{product}": product,
            "{{country}}": country,
            "{country}": country,
            "{{sender_email}}": sender_email,
            "{sender_email}": sender_email
        }

        subject = subject_template or self.DEFAULT_SUBJECT_TEMPLATE
        body = body_template or self.DEFAULT_BODY_TEMPLATE

        for placeholder, val in replacements.items():
            subject = subject.replace(placeholder, str(val))
            body = body.replace(placeholder, str(val))

        msg = MIMEMultipart()
        msg["From"] = f"Product Zone International <{sender_email}>"
        msg["To"] = str(recipient.get("email") or "")
        if self.monitor_cc:
            msg["Cc"] = self.monitor_cc
        msg["Subject"] = subject
        domain = sender_email.split('@')[1] if '@' in sender_email else 'productzoneintl.com'
        msg["List-Unsubscribe"] = f"<mailto:unsubscribe@{domain}?subject=unsubscribe>"

        # Attach text body
        msg.attach(MIMEText(body, "plain"))

        # Attach presentation PDF if enabled
        if attach_presentation:
            mime_part, _ = self.presentation_handler.get_mime_attachment()
            if mime_part:
                msg.attach(mime_part)

        return msg, subject

    def send_campaign(
        self,
        recipients: List[Dict[str, Any]],
        subject_template: Optional[str] = None,
        body_template: Optional[str] = None,
        attach_presentation: bool = True
    ) -> Dict[str, Any]:
        """
        Executes live outreach campaign over Gmail SMTP with rate-limit pacing.
        """
        subject_tpl = subject_template or self.DEFAULT_SUBJECT_TEMPLATE
        body_tpl = body_template or self.DEFAULT_BODY_TEMPLATE

        report_data = {
            "total": len(recipients),
            "success_count": 0,
            "failed_count": 0,
            "successful": [],
            "failed": [],
            "mode": "LIVE_GMAIL_SMTP"
        }

        if not recipients:
            return report_data

        try:
            self.smtp_connection = self._connect_smtp()
        except Exception as e:
            err_msg = f"SMTP Connection Failed: {str(e)}"
            return {
                "total": len(recipients),
                "success_count": 0,
                "failed_count": len(recipients),
                "successful": [],
                "failed": [{"email": r.get("email"), "error": err_msg} for r in recipients],
                "error": err_msg,
                "mode": "LIVE_GMAIL_SMTP"
            }

        for idx, recipient in enumerate(recipients):
            email = (recipient.get("email") or "").strip().lower()
            if not email:
                continue

            # Live Pre-Flight Domain MX check before touching SMTP
            if "@" in email:
                domain = email.split("@")[1]
                try:
                    import dns.resolver
                    res = dns.resolver.Resolver()
                    res.timeout = 2.0
                    res.lifetime = 2.0
                    mx = res.resolve(domain, 'MX')
                    if not mx or len(mx) == 0:
                        report_data["failed_count"] += 1
                        report_data["failed"].append({
                            "email": email,
                            "error": f"Pre-flight check failed: Domain {domain} has no mail exchange (MX) server.",
                            "status": "FAILED",
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        })
                        continue
                except Exception as dns_err:
                    if "NXDOMAIN" in str(dns_err) or "NoAnswer" in str(dns_err) or "not exist" in str(dns_err).lower():
                        report_data["failed_count"] += 1
                        report_data["failed"].append({
                            "email": email,
                            "error": f"Pre-flight check failed: Domain {domain} does not exist or has no active mail server.",
                            "status": "FAILED",
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        })
                        continue

            try:
                msg, formatted_subject = self.compose_email(
                    recipient,
                    subject_tpl,
                    body_tpl,
                    attach_presentation=attach_presentation
                )

                all_to = [email] + ([self.monitor_cc] if self.monitor_cc else [])
                if self.smtp_connection is None:
                    self.smtp_connection = self._connect_smtp()

                refused = None
                try:
                    refused = self.smtp_connection.sendmail(self.gmail_email, all_to, msg.as_string())
                except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError):
                    # Reconnect and retry once
                    time.sleep(1.0)
                    self.smtp_connection = self._connect_smtp()
                    refused = self.smtp_connection.sendmail(self.gmail_email, all_to, msg.as_string())

                if refused and email in refused:
                    report_data["failed_count"] += 1
                    report_data["failed"].append({
                        "email": email,
                        "error": f"SMTP rejected recipient: {refused[email]}",
                        "status": "FAILED",
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    })
                    continue

                report_data["success_count"] += 1
                report_data["successful"].append({
                    "email": email,
                    "company_name": recipient.get("company_name"),
                    "subject": formatted_subject,
                    "status": "SENT",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                })

                if self.send_delay > 0 and idx < len(recipients) - 1:
                    time.sleep(self.send_delay)

            except smtplib.SMTPRecipientsRefused as r_err:
                report_data["failed_count"] += 1
                report_data["failed"].append({
                    "email": email,
                    "error": f"Recipient address refused by server: {str(r_err)}",
                    "status": "FAILED",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                })
            except Exception as ex:
                report_data["failed_count"] += 1
                report_data["failed"].append({
                    "email": email,
                    "error": str(ex),
                    "status": "FAILED",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                })

        self._close_smtp()
        return report_data
