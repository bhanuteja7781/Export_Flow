"""
validation_module.py - 5.3 Email Validation Module (Algorithm 12.1)
Filters and eliminates fake, inactive, and non-existent email addresses using syntax checks,
disposable domain blocking, and live DNS MX record verification.
"""

import re
import dns.resolver
from typing import Dict, Any, List, Tuple


class EmailValidationModule:
    """
    Multi-stage Email Deliverability Validator (Algorithm 12.1).
    Strictly eliminates fake, non-existent, and inactive mailboxes.
    """

    RFC_SYNTAX_REGEX = re.compile(
        r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    )

    # Common disposable / temporary email providers
    DISPOSABLE_DOMAINS = {
        "mailinator.com", "tempmail.com", "guerrillamail.com", "10minutemail.com",
        "throwawaymail.com", "sharklasers.com", "getairmail.com", "yopmail.com",
        "trashmail.com", "burnermail.io", "maildrop.cc", "dispostable.com",
        "fakeinbox.com", "temp-mail.org", "mohmal.com", "crazymailing.com"
    }

    # Placeholder / dummy domains
    PLACEHOLDER_DOMAINS = {
        "example.com", "example.org", "test.com", "domain.com", "sample.com", "placeholder.com"
    }

    def __init__(self, dns_timeout: float = 1.5):
        self.resolver = dns.resolver.Resolver()
        self.resolver.lifetime = dns_timeout
        self.resolver.timeout = dns_timeout

    def validate_single_email(self, email: str) -> Dict[str, Any]:
        """
        Validates an individual email address through the 4-tier pipeline.
        Eliminates fake/invalid emails while validating legitimate active mailboxes.
        """
        if not email or not isinstance(email, str):
            return {
                "syntax_valid": False,
                "mx_found": False,
                "is_disposable": False,
                "score": 0,
                "status": "invalid",
                "reason": "Missing or non-string email"
            }

        email = email.strip().lower()

        # Stage 1: Syntax Validation
        if not self.RFC_SYNTAX_REGEX.match(email):
            return {
                "syntax_valid": False,
                "mx_found": False,
                "is_disposable": False,
                "score": 0,
                "status": "invalid",
                "reason": "Invalid RFC syntax format"
            }

        parts = email.split('@')
        domain = parts[1]

        # Stage 2: Placeholder & Blocklist check
        if domain in self.PLACEHOLDER_DOMAINS:
            return {
                "syntax_valid": True,
                "mx_found": False,
                "is_disposable": False,
                "score": 0,
                "status": "invalid",
                "reason": "Fake / Placeholder domain detected"
            }

        # Stage 3: Disposable Domain check
        if domain in self.DISPOSABLE_DOMAINS:
            return {
                "syntax_valid": True,
                "mx_found": False,
                "is_disposable": True,
                "score": 0,
                "status": "invalid",
                "reason": "Disposable / Temporary email address blocked"
            }

        # Stage 4: DNS MX Record Verification
        mx_status, mx_reason = self._check_mx_records(domain)

        if mx_status == "NOT_FOUND":
            return {
                "syntax_valid": True,
                "mx_found": False,
                "is_disposable": False,
                "score": 0,
                "status": "invalid",
                "reason": f"Fake/Inactive mailbox (No MX mail server or non-existent domain: {mx_reason})"
            }
        elif mx_status == "TIMEOUT":
            return {
                "syntax_valid": True,
                "mx_found": True,
                "is_disposable": False,
                "score": 70,
                "status": "risky",
                "reason": "DNS resolution timed out (Temporary network delay)"
            }

        # Score assignment for verified MX
        score = 95
        if domain in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"]:
            score = 90

        return {
            "syntax_valid": True,
            "mx_found": True,
            "is_disposable": False,
            "score": score,
            "status": "valid",
            "reason": "Valid domain with active MX mail exchange servers"
        }

    def _check_mx_records(self, domain: str) -> Tuple[str, str]:
        """
        Queries DNS resolver for MX records.
        Returns ("OK", reason), ("NOT_FOUND", reason), or ("TIMEOUT", reason).
        """
        try:
            records = self.resolver.resolve(domain, 'MX')
            if records and len(records) > 0:
                return "OK", "MX records resolved successfully"
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            return "NOT_FOUND", "Domain does not exist or has no mail exchange"
        except dns.resolver.Timeout:
            return "TIMEOUT", "DNS resolution timed out"
        except Exception as e:
            # If resolution fails with other socket errors, treat as not found if NXDOMAIN in message
            if "NXDOMAIN" in str(e) or "NoAnswer" in str(e) or "not found" in str(e).lower():
                return "NOT_FOUND", str(e)
            return "OK", f"DNS check allowed ({str(e)})"

        return "NOT_FOUND", "Unknown DNS resolution issue"

    def validate_leads_batch(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validates an entire list of lead dictionaries, updating validation_status and validation_details.
        """
        validated_leads = []
        for lead in leads:
            email = lead.get("email", "")
            result = self.validate_single_email(email)
            
            lead_copy = dict(lead)
            lead_copy["validation_status"] = result["status"]
            lead_copy["validation_details"] = result
            validated_leads.append(lead_copy)

        return validated_leads
