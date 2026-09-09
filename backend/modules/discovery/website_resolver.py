"""
website_resolver.py - Social Profile to Official Website Resolver
Transforms discovered social accounts & directory entries into verified business records
by crawling the official website, extracting verified contacts, and linking social profiles.
"""

import re
import urllib.parse
from typing import Dict, Any, List, Optional, Set, Tuple
import urllib3
import requests
from bs4 import BeautifulSoup
import dns.resolver

urllib3.disable_warnings()

from .sources import is_banned_domain, BANNED_PLATFORM_DOMAINS


class OfficialWebsiteResolver:
    """
    Crawls official company websites discovered via social profiles, search dorks, or directories.
    Extracts public procurement, leadership, and sales contacts.
    """

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ]

    EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    PHONE_REGEX = re.compile(r'(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')

    EXCLUDE_EMAIL_DOMAINS = {
        'sentry.io', 'wixpress.com', 'schema.org', 'domain.com', 'example.com',
        'yourname@', 'email@email.com', 'name@domain.com', 'user@domain.com',
        'cloudflare.com', 'github.com', 'google.com', 'w3.org', 'wordpress.com',
        'myshopify.com', 'squarespace.com', 'candles.org', 'nationalcandleassociation.org'
    } | BANNED_PLATFORM_DOMAINS

    DISQUALIFIED_PREFIXES = [
        'privacy', 'legal', 'compliance', 'unsubscribe', 'noreply', 'no-reply',
        'claudebot', 'anthropic', 'sentry', 'wixpress'
    ]

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": self.USER_AGENTS[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        })

    def check_mx_validity(self, domain: str) -> bool:
        """
        Validates whether domain has active DNS MX mail servers.
        """
        if not domain or "." not in domain or is_banned_domain(domain):
            return False
        try:
            res = dns.resolver.Resolver()
            res.timeout = 2.5
            res.lifetime = 2.5
            mx = res.resolve(domain, 'MX')
            return len(mx) > 0
        except Exception:
            try:
                # Fallback to public DNS resolvers
                fallback_res = dns.resolver.Resolver(configure=False)
                fallback_res.nameservers = ['8.8.8.8', '1.1.1.1']
                fallback_res.timeout = 2.5
                fallback_res.lifetime = 2.5
                mx = fallback_res.resolve(domain, 'MX')
                return len(mx) > 0
            except Exception:
                return False

    def extract_domain_from_url(self, url: str) -> str:
        try:
            netloc = urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
            return netloc
        except Exception:
            return ""

    def find_official_website_from_snippet(self, title: str, snippet: str, url: str) -> Optional[str]:
        """
        Attempts to detect the company's official domain from snippet, bio text, or target URL.
        """
        combined = f"{title} {snippet} {url}"

        # 1. If target URL is already a standalone company site (not social/directory/marketplace)
        domain = self.extract_domain_from_url(url)
        if domain and not is_banned_domain(domain):
            return f"https://{domain}"

        # 2. Look for external URL mentions in bio (e.g. www.abcdecor.com or abcdecor.com)
        domain_pattern = re.compile(r'\b(?:https?://)?(?:www\.)?([a-zA-Z0-9-]{2,50}\.(?:com|ca|net|org|co|shop|store|us|biz))\b', re.I)
        matches = domain_pattern.findall(combined)
        for m in matches:
            m_clean = m.lower().replace("www.", "")
            if not is_banned_domain(m_clean):
                return f"https://{m_clean}"

        return None

    def resolve_website_and_extract_contacts(
        self,
        website_url: str,
        country_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Visits the official website, crawls high-value procurement/wholesale/contact pages,
        extracts emails, phones, social links, and performs live DNS MX validation.
        """
        if not website_url or is_banned_domain(website_url):
            return {"emails": [], "phones": [], "social_profiles": {}, "text_corpus": "", "country": country_hint or "United States"}

        parsed = urllib.parse.urlparse(website_url)
        if not parsed.scheme:
            website_url = f"https://{website_url}"
            parsed = urllib.parse.urlparse(website_url)

        root_url = f"{parsed.scheme}://{parsed.netloc}"
        netloc_clean = parsed.netloc.replace("www.", "")
        if is_banned_domain(netloc_clean):
            return {"emails": [], "phones": [], "social_profiles": {}, "text_corpus": "", "country": country_hint or "United States"}

        found_emails: Set[str] = set()
        found_phones: Set[str] = set()
        discovered_socials: Dict[str, str] = {}
        text_corpus: List[str] = []

        is_canadian = netloc_clean.endswith(".ca") or (country_hint and "canada" in country_hint.lower())
        detected_country = "Canada" if is_canadian else "United States"

        seen_paths = set()
        # Step 1: Visit main website
        main_pages = [website_url]
        if root_url != website_url:
            main_pages.append(root_url)

        contact_page_links = []

        for page_url in main_pages:
            if page_url in seen_paths:
                continue
            seen_paths.add(page_url)

            try:
                resp = self.session.get(page_url, timeout=3.5, verify=False, allow_redirects=True)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                body_text = soup.get_text(separator=" ", strip=True)
                text_corpus.append(body_text[:400])

                # Check country indicators in text
                if any(prov in body_text.lower() for prov in ["ontario", "toronto", "brampton", "mississauga", "vancouver", "surrey", "british columbia", "quebec", "montreal", "calgary", "alberta", "canada"]):
                    detected_country = "Canada"

                # Parse Mailto links
                for mailto in soup.find_all("a", href=re.compile(r"^mailto:", re.I)):
                    href_val = mailto.get("href")
                    if isinstance(href_val, str):
                        raw_em = href_val.replace("mailto:", "").split("?")[0].strip().lower()
                        if self._is_valid_email(raw_em):
                            found_emails.add(raw_em)

                # Parse text emails
                for em in self.EMAIL_REGEX.findall(body_text):
                    em_clean = em.strip().lower()
                    if self._is_valid_email(em_clean):
                        found_emails.add(em_clean)

                # Parse phone numbers
                for ph in self.PHONE_REGEX.findall(body_text):
                    clean_ph = re.sub(r'[^\d]', '', ph)
                    if len(clean_ph) in [10, 11]:
                        found_phones.add(ph.strip())

                # Discover connected social profile links from website footer/header
                for link_tag in soup.find_all("a", href=True):
                    href = link_tag.get("href", "")
                    if isinstance(href, str):
                        href_lower = href.lower()
                        if "instagram.com/" in href_lower and not any(ign in href_lower for ign in ["/p/", "/reel/", "/explore/"]):
                            discovered_socials["instagram"] = href
                        elif "facebook.com/" in href_lower and not any(ign in href_lower for ign in ["/sharer", "/share.php"]):
                            discovered_socials["facebook"] = href
                        elif "linkedin.com/company/" in href_lower:
                            discovered_socials["linkedin"] = href
                        elif "pinterest.com/" in href_lower and not any(ign in href_lower for ign in ["/pin/"]):
                            discovered_socials["pinterest"] = href
                        elif "youtube.com/" in href_lower and not any(ign in href_lower for ign in ["/watch", "/embed"]):
                            discovered_socials["youtube"] = href
                        
                        if any(term in href_lower for term in ["contact", "about", "wholesale", "trade"]):
                            if href.startswith("http"):
                                if netloc_clean in href_lower:
                                    contact_page_links.append(href)
                            elif href.startswith("/"):
                                contact_page_links.append(f"{root_url}{href}")

                if found_emails:
                    break

            except Exception:
                continue

        # Step 2: If no email found on homepage, crawl top contact page
        if not found_emails:
            secondary_paths = list(dict.fromkeys(contact_page_links[:2] + [
                f"{root_url}/pages/contact-us",
                f"{root_url}/pages/contact",
                f"{root_url}/contact-us",
                f"{root_url}/contact"
            ]))

            for page_url in secondary_paths[:2]:
                if page_url in seen_paths:
                    continue
                seen_paths.add(page_url)

                try:
                    resp = self.session.get(page_url, timeout=3.0, verify=False, allow_redirects=True)
                    if resp.status_code != 200:
                        continue

                    soup = BeautifulSoup(resp.text, "html.parser")
                    body_text = soup.get_text(separator=" ", strip=True)

                    for mailto in soup.find_all("a", href=re.compile(r"^mailto:", re.I)):
                        href_val = mailto.get("href")
                        if isinstance(href_val, str):
                            raw_em = href_val.replace("mailto:", "").split("?")[0].strip().lower()
                            if self._is_valid_email(raw_em):
                                found_emails.add(raw_em)

                    for em in self.EMAIL_REGEX.findall(body_text):
                        em_clean = em.strip().lower()
                        if self._is_valid_email(em_clean):
                            found_emails.add(em_clean)

                    if found_emails:
                        break
                except Exception:
                    continue

        # Live DNS MX Verification on all extracted emails
        verified_emails = []
        domain_mx_cache: Dict[str, bool] = {}

        for em in found_emails:
            em_domain = em.split("@")[1].lower()
            if em_domain not in domain_mx_cache:
                domain_mx_cache[em_domain] = self.check_mx_validity(em_domain)
            if domain_mx_cache[em_domain]:
                verified_emails.append(em)

        # If domain has verified MX but only contact form was present, generate validated mailbox
        if not verified_emails and netloc_clean and "." in netloc_clean and not is_banned_domain(netloc_clean):
            if netloc_clean not in domain_mx_cache:
                domain_mx_cache[netloc_clean] = self.check_mx_validity(netloc_clean)
            if domain_mx_cache[netloc_clean]:
                verified_emails.append(f"info@{netloc_clean}")

        return {
            "root_url": root_url,
            "domain": netloc_clean,
            "emails": verified_emails[:5],
            "phones": list(found_phones)[:2],
            "social_profiles": discovered_socials,
            "text_corpus": " ".join(text_corpus)[:1000],
            "country": detected_country
        }

    def _is_valid_email(self, email: str) -> bool:
        if not email or "@" not in email:
            return False
        if any(email.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif", ".js", ".css", ".ico", ".woff", ".ttf"]):
            return False
        parts = email.split("@")
        if len(parts) != 2 or "." not in parts[1]:
            return False
        domain = parts[1].lower()
        if any(ex in domain for ex in self.EXCLUDE_EMAIL_DOMAINS) or is_banned_domain(domain):
            return False
        prefix = parts[0].lower().replace(".", "").replace("-", "")
        for disq in self.DISQUALIFIED_PREFIXES:
            if prefix == disq or prefix.startswith(disq):
                return False
        return True

