import os
import sys
import io
import re
import csv
import json
import time
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from modules.search_module import BuyerSearchModule
from modules.extraction_module import DataExtractionModule
from modules.validation_module import EmailValidationModule
from modules.classification_module import AIClassificationModule
from modules.presentation_module import PresentationModule
from modules.gmail_module import GmailDispatcherModule
from modules.logging_module import LoggingModule
from modules.inbox_module import InboxTrackerModule

DIST_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")

app = Flask(__name__, static_folder=DIST_FOLDER, static_url_path="")
CORS(app)

# Initialize singletons
logger = LoggingModule()
searcher = BuyerSearchModule()
extractor = DataExtractionModule()
validator = EmailValidationModule()
presenter = PresentationModule()
inbox_tracker = InboxTrackerModule()

# Ensure presentation PDF exists on boot
presenter.ensure_presentation_exists()


# -------------------------------------------------------------
# Frontend Static Hosting Fallback
# -------------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    if os.path.exists(os.path.join(DIST_FOLDER, "index.html")):
        return send_from_directory(DIST_FOLDER, "index.html")
    return jsonify({
        "status": "healthy",
        "system": "Product Zone International Export Outreach Automation API",
        "message": "Frontend dev server running on port 3000, or build with 'npm run build' inside frontend/"
    })


# -------------------------------------------------------------
# User Authentication Routes
# -------------------------------------------------------------
USERS_FILE = os.path.join(os.path.dirname(__file__), "data", "users.json")

def _load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def _save_users(users):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    data = request.json or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", "")).strip()
    name = str(data.get("name", "")).strip() or "Exporter"
    company = str(data.get("company", "")).strip() or "Product Zone International"

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    users = _load_users()
    if any(u.get("email") == email for u in users):
        return jsonify({"error": "An account with this email already exists"}), 409

    new_user = {
        "id": f"user-{len(users) + 1}",
        "name": name,
        "email": email,
        "password": password,
        "company": company,
        "created_at": "2026-08-24T12:00:00Z"
    }
    users.append(new_user)
    _save_users(users)

    return jsonify({
        "status": "success",
        "message": "Account registered successfully",
        "user": {
            "id": new_user["id"],
            "name": new_user["name"],
            "email": new_user["email"],
            "company": new_user["company"]
        }
    })

@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.json or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", "")).strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    users = _load_users()
    user = next((u for u in users if u.get("email") == email and u.get("password") == password), None)

    # Demo fallback user if no registered accounts exist yet
    if not user and email == "exporter@gmail.com" and password == "password123":
        user = {
            "id": "user-demo",
            "name": "Export Manager",
            "email": "exporter@gmail.com",
            "company": "Product Zone International"
        }

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({
        "status": "success",
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "company": user.get("company", "Product Zone International")
        }
    })


import threading

# -------------------------------------------------------------
# Lead Management & Discovery Routes
# -------------------------------------------------------------
_last_inbox_sync_time = 0
_is_syncing_inbox = False

def _do_inbox_sync():
    global _is_syncing_inbox
    try:
        leads = logger.get_all_leads()
        updated, stats = inbox_tracker.scan_for_replies(leads)
        if stats.get("bounces_detected", 0) > 0 or stats.get("replies_detected", 0) > 0:
            logger.save_leads(updated, merge=False)
            logger._sync_sent_csv(logger.get_all_logs())
            logger._sync_csv_exports(updated)
    except Exception as e:
        print(f"[AutoSync] IMAP sync notice: {e}")
    finally:
        _is_syncing_inbox = False

def _sync_inbox_if_needed():
    global _last_inbox_sync_time, _is_syncing_inbox
    now = time.time()
    if now - _last_inbox_sync_time > 60 and not _is_syncing_inbox:
        _last_inbox_sync_time = now
        _is_syncing_inbox = True
        threading.Thread(target=_do_inbox_sync, daemon=True).start()

@app.route("/api/leads", methods=["GET"])
def get_leads():
    _sync_inbox_if_needed()
    category = request.args.get("category")
    buyer_size = request.args.get("buyer_size")
    status = request.args.get("status")
    country_filter = request.args.get("country")
    state_filter = request.args.get("state")
    city_filter = request.args.get("city")
    reply_filter = request.args.get("reply_status")
    search_q = request.args.get("q", "").lower()

    leads = logger.get_all_leads()

    if category and category != "all":
        leads = [l for l in leads if l.get("category") == category]
    if buyer_size and buyer_size != "all":
        leads = [l for l in leads if l.get("buyer_size") == buyer_size]
    if status and status != "all":
        leads = [l for l in leads if l.get("validation_status") == status]
    if reply_filter and reply_filter != "all":
        if reply_filter == "replied":
            leads = [l for l in leads if l.get("reply_status") == "replied"]
        elif reply_filter == "unreplied":
            leads = [l for l in leads if l.get("last_contacted_at") and l.get("reply_status") != "replied" and l.get("validation_status") != "invalid"]
        elif reply_filter == "uncontacted":
            leads = [l for l in leads if not l.get("last_contacted_at")]
    if country_filter and country_filter != "all":
        if "canada" in country_filter.lower():
            leads = [l for l in leads if "canada" in (l.get("country") or "").lower()]
        elif "united states" in country_filter.lower() or "usa" in country_filter.lower():
            leads = [l for l in leads if "united states" in (l.get("country") or "").lower() or "usa" in (l.get("country") or "").lower()]
    if state_filter and state_filter != "all":
        leads = [l for l in leads if state_filter.lower() in (l.get("state") or "").lower()]
    if city_filter and city_filter != "all":
        leads = [l for l in leads if city_filter.lower() in (l.get("city") or "").lower()]
    if search_q:
        leads = [
            l for l in leads if
            search_q in (l.get("email") or "").lower() or
            search_q in (l.get("buyer_name") or "").lower() or
            search_q in (l.get("company_name") or "").lower() or
            search_q in (l.get("city") or "").lower() or
            search_q in (l.get("state") or "").lower() or
            search_q in (l.get("country") or "").lower() or
            search_q in (l.get("source_platform") or "").lower() or
            search_q in (l.get("reply_snippet") or "").lower()
        ]

    return jsonify({"leads": leads, "count": len(leads)})


@app.route("/api/leads/search", methods=["POST"])
def search_leads():
    """
    Triggers Deep Multi-Platform Discovery across Web, Social Media, Directories,
    and Marketplaces for ANY product keyword and ANY target location.
    """
    body = request.json or {}
    keyword = body.get("keyword") or os.getenv("SEARCH_KEYWORD", "Handcrafted Products")
    sources = body.get("sources")
    raw_limit = body.get("max_results") or body.get("limit") or body.get("maxResults")
    try:
        max_results = int(raw_limit) if raw_limit is not None else 10
    except (ValueError, TypeError):
        max_results = 10
    discovery_mode = body.get("discovery_mode") or body.get("source") or "all"
    location = body.get("location") or body.get("country") or "America & Canada"
    country = body.get("country") or location
    state = body.get("state") or None
    city = body.get("city") or None
    preview = bool(body.get("preview", False))

    if location and location.lower() not in ["all", "america & canada", "global", "worldwide"]:
        parts = [p.strip() for p in location.split(",") if p.strip()]
        if len(parts) >= 2 and not city and not state:
            city = parts[0]
            state = parts[1]

    buyer_type = body.get("buyer_type") or "all"
    buyer_size = body.get("buyer_size") or "all"
    price_segment = body.get("price_segment") or body.get("market_segment") or "all"
    diaspora_focus = bool(body.get("diaspora_focus") or body.get("diaspora_only") or buyer_type == "diaspora_ethnic")
    target_domains = body.get("target_domains", [])

    if isinstance(target_domains, str):
        target_domains = [d.strip() for d in re.split(r'[\n,]+', target_domains) if d.strip()]

    # Collect known emails and domains to guarantee finding NEW buyers
    existing_leads = logger.get_all_leads()
    existing_emails = {l.get("email", "").lower() for l in existing_leads if l.get("email")}
    existing_domains = logger.get_all_domains()

    # 1. Deep Multi-Platform Search with dynamic product keyword and location
    raw_results = searcher.search(
        keyword=keyword,
        sources=sources,
        max_results=max_results,
        discovery_mode=discovery_mode,
        country=country if country != "All" else "America & Canada",
        state=state if state != "all" else None,
        city=city if city != "all" else None,
        buyer_type=buyer_type,
        buyer_size=buyer_size,
        price_segment=price_segment,
        diaspora_focus=diaspora_focus,
        target_domains=target_domains,
        exclude_emails=existing_emails,
        exclude_domains=existing_domains
    )

    # 2. Extract & normalize into schema
    normalized_records = extractor.extract_and_normalize(raw_results)[:max_results]
    for r in normalized_records:
        r["keyword"] = keyword
        if location and not r.get("city"):
            r["city"] = city or location

    # 3. Automatically Classify into B2B commercial categories
    classifier = AIClassificationModule(api_key=os.getenv("GEMINI_API_KEY"))
    classified_records = classifier.classify_leads(normalized_records, product_niche=keyword)

    # 4. Save to database if not in preview-only mode
    added_count = 0
    if not preview:
        added_count = logger.save_leads(classified_records)

    return jsonify({
        "status": "success",
        "keyword": keyword,
        "location": location,
        "discovered": len(classified_records),
        "newly_added": added_count,
        "leads": classified_records
    })


@app.route("/api/leads/import_selected", methods=["POST"])
def import_selected_leads():
    """
    Imports a user-selected array of discovered buyer lead cards into the main database.
    """
    data = request.json or {}
    selected_leads = data.get("leads", [])
    if not isinstance(selected_leads, list) or len(selected_leads) == 0:
        return jsonify({"error": "No leads provided for importing"}), 400

    # Ensure validation status and date
    normalized = extractor.extract_and_normalize(selected_leads)
    classifier = AIClassificationModule(api_key=os.getenv("GEMINI_API_KEY"))
    classified = classifier.classify_leads(normalized)
    
    added_count = logger.save_leads(classified)
    return jsonify({
        "status": "success",
        "imported_count": added_count,
        "total_leads": len(logger.get_all_leads()),
        "message": f"Successfully imported {added_count} buyer leads into the directory."
    })


# -------------------------------------------------------------
# Multi-Source Discovery Routes (Req 15, 16, 17, 23, 24)
# -------------------------------------------------------------
@app.route("/api/discovery/sources", methods=["GET"])
def get_discovery_sources():
    """
    Returns list of all available discovery sources with status and priority weights.
    """
    sources = searcher.get_available_sources()
    return jsonify({
        "status": "success",
        "sources": sources,
        "count": len(sources)
    })


@app.route("/api/discovery/modes", methods=["GET"])
def get_discovery_modes():
    """
    Returns available buyer discovery modes (Quick, Deep, Social, Wholesale, Retail, Multi-Source).
    """
    modes = searcher.get_discovery_modes()
    return jsonify({
        "status": "success",
        "modes": modes
    })


@app.route("/api/discovery/analytics", methods=["GET"])
def get_discovery_analytics():
    """
    Returns calculated discovery source performance analytics:
    Source | Discovered | Leads | Qualified | Qualification %
    """
    leads = logger.get_all_leads()
    analytics = searcher.get_source_analytics(leads)
    return jsonify({
        "status": "success",
        "analytics": analytics,
        "total_sources": len(analytics)
    })


@app.route("/api/discovery/sources/toggle", methods=["POST"])
def toggle_discovery_source():
    """
    Dynamically toggles a source or updates its priority weight.
    """
    data = request.json or {}
    source_id = data.get("source_id")
    enabled = data.get("enabled")
    weight = data.get("priority_weight")

    if not source_id or source_id not in searcher.discovery_engine.sources:
        return jsonify({"error": "Invalid or missing source_id"}), 400

    src = searcher.discovery_engine.sources[source_id]
    if enabled is not None:
        src.enabled = bool(enabled)
    if weight is not None:
        try:
            src.priority_weight = float(weight)
        except (ValueError, TypeError):
            pass

    return jsonify({
        "status": "success",
        "source": src.to_dict()
    })


@app.route("/api/leads/purge_failed", methods=["POST"])
def purge_failed_leads():
    """
    Removes all bounced, invalid, and failed email records from the database
    so their company domains can be re-discovered with fresh working emails.
    """
    purged_count = logger.purge_invalid_and_bounced_leads()
    return jsonify({
        "status": "success",
        "purged_count": purged_count,
        "remaining_count": len(logger.get_all_leads()),
        "message": f"Successfully purged {purged_count} failed/bounced buyer records from database."
    })


@app.route("/api/leads/clear", methods=["POST"])
def clear_leads():
    """
    Clears all saved leads and logs from the database to start completely fresh.
    """
    logger.clear_all_leads()
    logger.clear_all_logs()
    searcher.reset_state()
    return jsonify({
        "status": "success",
        "message": "Database cleared successfully. Ready for fresh discovery."
    })


@app.route("/api/leads/validate", methods=["POST"])
def validate_leads():
    """
    Runs 5.3 Email Validation (Algorithm 12.1)
    """
    body = request.json or {}
    lead_ids = body.get("lead_ids")

    leads = logger.get_all_leads()
    to_validate = [l for l in leads if not lead_ids or l.get("id") in lead_ids]

    validated_results = validator.validate_leads_batch(to_validate)
    logger.save_leads(validated_results)

    valid_cnt = sum(1 for l in validated_results if l.get("validation_status") == "valid")
    invalid_cnt = sum(1 for l in validated_results if l.get("validation_status") == "invalid")
    risky_cnt = sum(1 for l in validated_results if l.get("validation_status") == "risky")

    return jsonify({
        "status": "success",
        "total_validated": len(validated_results),
        "valid_count": valid_cnt,
        "invalid_count": invalid_cnt,
        "risky_count": risky_cnt,
        "leads": validated_results
    })


@app.route("/api/leads/classify", methods=["POST"])
def classify_leads():
    """
    Runs 5.4 AI Lead & Content Classifier (Algorithm 12.2)
    """
    body = request.json or {}
    lead_ids = body.get("lead_ids")
    product_niche = body.get("product_niche") or os.getenv("SEARCH_KEYWORD", "Metal Candle Holders")

    leads = logger.get_all_leads()
    to_classify = [l for l in leads if not lead_ids or l.get("id") in lead_ids]

    classifier = AIClassificationModule(api_key=os.getenv("GEMINI_API_KEY"))
    classified_results = classifier.classify_leads(to_classify, product_niche=product_niche)

    logger.save_leads(classified_results)

    return jsonify({
        "status": "success",
        "total_classified": len(classified_results),
        "leads": classified_results
    })


@app.route("/api/leads/upload", methods=["POST"])
def upload_leads_csv():
    """
    Upload CSV or JSON of external leads
    """
    classifier = AIClassificationModule(api_key=os.getenv("GEMINI_API_KEY"))
    niche = os.getenv("SEARCH_KEYWORD", "Metal Candle Holders")

    if "file" in request.files:
        file = request.files["file"]
        content = file.read().decode("utf-8", errors="ignore")
        reader = csv.DictReader(io.StringIO(content))
        raw_items = [{"raw_content": json.dumps(row), "source_platform": "CSV Upload"} for row in reader]
        extracted = extractor.extract_and_normalize(raw_items)
        classified = classifier.classify_leads(extracted, product_niche=niche)
        added_count = logger.save_leads(classified)
        return jsonify({"status": "success", "added_count": added_count, "leads": classified})
    elif request.json and "leads" in request.json:
        extracted = extractor.extract_and_normalize(request.json["leads"])
        classified = classifier.classify_leads(extracted, product_niche=niche)
        added_count = logger.save_leads(classified)
        return jsonify({"status": "success", "added_count": added_count, "leads": classified})

    return jsonify({"error": "No file or valid JSON payload provided"}), 400


@app.route("/api/leads/update", methods=["POST"])
def update_lead():
    """
    Updates individual lead fields
    """
    data = request.json or {}
    lead_id = data.get("id") or data.get("email")
    if not lead_id:
        return jsonify({"error": "Lead ID or Email is required"}), 400

    leads = logger.get_all_leads()
    updated = False
    for l in leads:
        if l.get("id") == lead_id or l.get("email", "").lower() == str(lead_id).lower():
            for k, v in data.items():
                if k != "id":
                    l[k] = v
            updated = True
            break

    if updated:
        logger.save_leads(leads, merge=False)
        return jsonify({"status": "success", "message": "Lead updated successfully"})
    return jsonify({"error": "Lead not found"}), 404


@app.route("/api/leads/delete", methods=["POST"])
def delete_lead_endpoint():
    """
    Deletes lead and permanently blacklists its email address so it never re-appears.
    """
    data = request.json or {}
    lead_id = data.get("id") or data.get("email")
    if not lead_id:
        return jsonify({"error": "Lead ID or Email is required"}), 400

    deleted = logger.delete_lead(str(lead_id))
    if deleted:
        return jsonify({"status": "success", "message": "Lead deleted and email blacklisted from future discovery."})
    return jsonify({"error": "Lead not found"}), 404


@app.route("/api/leads/purge_failed", methods=["POST"])
def purge_failed_leads_endpoint():
    """
    Purges all bounced, failed, or address-not-found buyers from database and reports.
    """
    purge_res = logger.recheck_and_purge_bounced_records()
    return jsonify({
        "status": "success",
        "message": f"Purged {purge_res['purged_count']} invalid/bounced buyers from report and database.",
        "purged_count": purge_res["purged_count"],
        "purged_emails": purge_res["purged_emails"],
        "remaining_count": purge_res["remaining_leads_count"]
    })


# -------------------------------------------------------------
# Inbox & Reply Tracking Routes
# -------------------------------------------------------------
@app.route("/api/inbox/replies", methods=["GET"])
def get_inbox_replies():
    """
    Retrieves all received buyer replies, unreplied follow-up queue, and response statistics.
    """
    leads = logger.get_all_leads()
    replies = [l for l in leads if l.get("reply_status") == "replied"]
    auto_replies = [l for l in leads if l.get("reply_status") == "auto_reply"]
    bounced = [l for l in leads if l.get("reply_status") == "bounced"]
    unreplied = [l for l in leads if l.get("last_contacted_at") and l.get("reply_status") not in ["replied", "bounced"] and l.get("validation_status") != "invalid"]
    invalid_count = sum(1 for l in leads if l.get("validation_status") == "invalid" or l.get("reply_status") == "bounced")
    contacted_count = sum(1 for l in leads if l.get("last_contacted_at"))

    return jsonify({
        "replies": replies,
        "reply_count": len(replies),
        "auto_replies": auto_replies,
        "auto_reply_count": len(auto_replies),
        "bounced_count": len(bounced),
        "unreplied_leads": unreplied,
        "unreplied_count": len(unreplied),
        "contacted_count": contacted_count,
        "invalid_count": invalid_count,
        "response_rate": round((len(replies) / max(1, contacted_count)) * 100, 1) if contacted_count > 0 else 0.0
    })


@app.route("/api/inbox/scan", methods=["POST"])
def scan_inbox_replies():
    """
    Scans Gmail IMAP inbox for buyer responses, updates leads.json, and returns telemetry.
    """
    leads = logger.get_all_leads()
    updated_leads, stats = inbox_tracker.scan_for_replies(leads)
    logger.save_leads(updated_leads, merge=False)
    logger._sync_sent_csv(logger.get_all_logs())
    logger._sync_csv_exports(updated_leads)

    replies = [l for l in updated_leads if l.get("reply_status") == "replied"]
    auto_replies = [l for l in updated_leads if l.get("reply_status") == "auto_reply"]
    unreplied = [l for l in updated_leads if l.get("last_contacted_at") and l.get("reply_status") not in ["replied", "bounced"] and l.get("validation_status") != "invalid"]

    return jsonify({
        "status": "success",
        "message": f"Inbox scan complete: {stats['replies_detected']} buyer replies, {stats.get('auto_replies_detected', 0)} auto-replies detected ({stats['mode']}).",
        "stats": stats,
        "replies": replies,
        "auto_replies": auto_replies,
        "unreplied_count": len(unreplied)
    })


@app.route("/api/inbox/recheck_and_clean", methods=["POST"])
def recheck_and_clean_endpoint():
    """
    Connects to live Gmail via IMAP, scans for new bounce notifications (Address not found / 550),
    and automatically purges all failed buyers from leads.json, intern_report.csv, buyers.csv, and sent_log.csv.
    """
    leads = logger.get_all_leads()
    updated_leads, stats = inbox_tracker.scan_for_replies(leads)

    # Extract all detected bounces from scan
    detected_bounces = set()
    for l in updated_leads:
        if l.get("reply_status") == "bounced" or l.get("validation_status") == "invalid":
            em = (l.get("email") or "").strip().lower()
            if em:
                detected_bounces.add(em)

    # Purge all bounced/address not found records across database and reports
    purge_res = logger.recheck_and_purge_bounced_records(detected_bounces)

    return jsonify({
        "status": "success",
        "message": f"Mailbox rechecked: {stats.get('replies_detected', 0)} replies found, {purge_res['purged_count']} invalid address buyers removed from report.",
        "bounces_purged": purge_res["purged_count"],
        "purged_emails": purge_res["purged_emails"],
        "remaining_leads": purge_res["remaining_leads_count"],
        "stats": stats
    })


# -------------------------------------------------------------
# Campaign & Outreach Routes (Zero-Gap + Follow-Up Sequences)
# -------------------------------------------------------------
@app.route("/api/campaign/send", methods=["POST"])
def send_campaign():
    """
    Runs 5.5 Gmail Dispatcher over live Gmail SMTP,
    strictly eliminating fake/invalid emails while delivering to valid buyers.
    """
    body = request.json or {}
    lead_ids = body.get("lead_ids")
    audience = body.get("audience", "all")
    campaign_mode = body.get("campaign_mode", "all")
    subject_template = body.get("subject")
    body_template = body.get("body")
    attach_presentation = body.get("attach_presentation", True)
    force_resend = body.get("force_resend", False)
    include_risky = body.get("include_risky", True)
    include_unvalidated = body.get("include_unvalidated", True)

    all_leads = logger.get_all_leads()

    target_recipients = []
    skipped_leads = []

    for lead in all_leads:
        # 1. If explicit lead_ids were passed, filter strictly to them
        if lead_ids is not None and len(lead_ids) > 0:
            if lead.get("id") not in lead_ids and lead.get("email") not in lead_ids:
                continue

        email = (lead.get("email") or "").strip().lower()
        if not email:
            continue

        # 2. ELIMINATE ONLY FAKE / INVALID / BOUNCED EMAILS
        # Auto-validate if pending
        if lead.get("validation_status") == "pending" and include_unvalidated:
            val_res = validator.validate_single_email(email)
            lead["validation_status"] = val_res["status"]
            lead["validation_details"] = val_res

        val_status = lead.get("validation_status", "valid")
        if val_status == "invalid":
            skipped_leads.append({
                "email": email,
                "reason": f"ELIMINATED: Fake or inactive mailbox ({lead.get('validation_details', {}).get('reason', 'Failed DNS MX')})"
            })
            continue

        if val_status == "risky" and not include_risky:
            skipped_leads.append({
                "email": email,
                "reason": "Filtered out (Risky deliverability)"
            })
            continue

        # 3. Explicit User Approval Check
        if lead.get("approved") is False:
            skipped_leads.append({
                "email": email,
                "reason": "Lead explicitly unapproved by user"
            })
            continue

        target_recipients.append(lead)

    if not target_recipients:
        return jsonify({
            "status": "warning",
            "message": f"No eligible recipients found for dispatch ({len(skipped_leads)} skipped/eliminated).",
            "report": {
                "total": 0,
                "success_count": 0,
                "failed_count": 0,
                "skipped_count": len(skipped_leads),
                "successful": [],
                "failed": [],
                "skipped": skipped_leads
            }
        })

    dispatcher = GmailDispatcherModule(
        gmail_email=os.getenv("GMAIL_EMAIL"),
        app_password=os.getenv("GMAIL_APP_PASSWORD"),
        monitor_cc=os.getenv("MONITOR_CC_EMAIL"),
        send_delay=float(os.getenv("SEND_DELAY_SECONDS", 2.0))
    )

    report_data = dispatcher.send_campaign(
        recipients=target_recipients,
        subject_template=subject_template,
        body_template=body_template,
        attach_presentation=attach_presentation
    )

    report_data["skipped_count"] = len(skipped_leads)
    report_data["skipped"] = skipped_leads

    # Persist log event & update lead status
    logger.record_campaign_dispatch(report_data)

    return jsonify({
        "status": "success",
        "message": f"Dispatched campaign to {report_data.get('success_count', 0)} recipients ({report_data.get('mode')}).",
        "report": report_data
    })


# -------------------------------------------------------------
# Configuration & Settings Routes
# -------------------------------------------------------------
@app.route("/api/settings", methods=["GET"])
def get_settings():
    """
    Retrieve current runtime and .env configuration
    """
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()

    return jsonify({
        "gmail_email": env_vars.get("GMAIL_EMAIL") or os.getenv("GMAIL_EMAIL", ""),
        "gmail_app_password": env_vars.get("GMAIL_APP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD", ""),
        "monitor_cc_email": env_vars.get("MONITOR_CC_EMAIL") or os.getenv("MONITOR_CC_EMAIL", ""),
        "gemini_api_key": env_vars.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY", ""),
        "search_keyword": env_vars.get("SEARCH_KEYWORD") or os.getenv("SEARCH_KEYWORD", "Metal Candle Holders"),
        "daily_send_limit": int(env_vars.get("DAILY_SEND_LIMIT") or os.getenv("DAILY_SEND_LIMIT", 100)),
        "send_delay": float(env_vars.get("SEND_DELAY_SECONDS") or os.getenv("SEND_DELAY_SECONDS", 2.5)),
        "send_delay_seconds": float(env_vars.get("SEND_DELAY_SECONDS") or os.getenv("SEND_DELAY_SECONDS", 2.5))
    })


@app.route("/api/settings", methods=["POST"])
def save_settings():
    """
    Persist configuration to .env and active runtime environment
    """
    data = request.json or {}
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

    # Read existing .env
    env_data = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_data[k.strip()] = v.strip()

    # Update values from request
    if "gmail_email" in data:
        val = str(data.get("gmail_email", "")).strip()
        env_data["GMAIL_EMAIL"] = val
        os.environ["GMAIL_EMAIL"] = val

    if "gmail_app_password" in data or "app_password" in data:
        val = str(data.get("gmail_app_password") or data.get("app_password") or "").strip()
        env_data["GMAIL_APP_PASSWORD"] = val
        os.environ["GMAIL_APP_PASSWORD"] = val

    if "monitor_cc_email" in data:
        val = str(data.get("monitor_cc_email", "")).strip()
        env_data["MONITOR_CC_EMAIL"] = val
        os.environ["MONITOR_CC_EMAIL"] = val

    if "gemini_api_key" in data:
        val = str(data.get("gemini_api_key", "")).strip()
        env_data["GEMINI_API_KEY"] = val
        os.environ["GEMINI_API_KEY"] = val

    if "search_keyword" in data:
        val = str(data.get("search_keyword", "Metal Candle Holders")).strip()
        env_data["SEARCH_KEYWORD"] = val
        os.environ["SEARCH_KEYWORD"] = val

    if "daily_send_limit" in data:
        val = str(data.get("daily_send_limit", 100)).strip()
        env_data["DAILY_SEND_LIMIT"] = val
        os.environ["DAILY_SEND_LIMIT"] = val

    if "send_delay" in data or "send_delay_seconds" in data:
        val = str(data.get("send_delay") or data.get("send_delay_seconds") or 2.5).strip()
        env_data["SEND_DELAY_SECONDS"] = val
        os.environ["SEND_DELAY_SECONDS"] = val

    env_data["PRESENTATION_PATH"] = "assets/Candle_Holders_Rebrand.pdf"

    # Write back to .env
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("# --- Gmail Credentials (SMTP) ---\n")
        f.write(f"GMAIL_EMAIL={env_data.get('GMAIL_EMAIL', '')}\n")
        f.write(f"GMAIL_APP_PASSWORD={env_data.get('GMAIL_APP_PASSWORD', '')}\n")
        f.write(f"MONITOR_CC_EMAIL={env_data.get('MONITOR_CC_EMAIL', '')}\n\n")
        f.write("# --- Google Gemini AI Credentials ---\n")
        f.write(f"GEMINI_API_KEY={env_data.get('GEMINI_API_KEY', '')}\n\n")
        f.write("# --- Campaign & Dispatch Settings ---\n")
        f.write(f"SEARCH_KEYWORD={env_data.get('SEARCH_KEYWORD', 'Metal Candle Holders')}\n")
        f.write(f"DAILY_SEND_LIMIT={env_data.get('DAILY_SEND_LIMIT', '100')}\n")
        f.write(f"SEND_DELAY_SECONDS={env_data.get('SEND_DELAY_SECONDS', '2.5')}\n")
        f.write(f"PRESENTATION_PATH={env_data.get('PRESENTATION_PATH', 'assets/Candle_Holders_Rebrand.pdf')}\n")

    return jsonify({
        "status": "success",
        "message": "Configuration saved successfully.",
        "settings": {
            "gmail_email": env_data.get("GMAIL_EMAIL", ""),
            "gmail_app_password": env_data.get("GMAIL_APP_PASSWORD", ""),
            "monitor_cc_email": env_data.get("MONITOR_CC_EMAIL", ""),
            "gemini_api_key": env_data.get("GEMINI_API_KEY", ""),
            "search_keyword": env_data.get("SEARCH_KEYWORD", "Metal Candle Holders"),
            "daily_send_limit": int(env_data.get("DAILY_SEND_LIMIT", 100)),
            "send_delay": float(env_data.get("SEND_DELAY_SECONDS", 2.5)),
            "send_delay_seconds": float(env_data.get("SEND_DELAY_SECONDS", 2.5))
        }
    })


# -------------------------------------------------------------
# Reporting & Export Routes
# -------------------------------------------------------------
@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    _sync_inbox_if_needed()
    summary = logger.get_metrics_summary()
    return jsonify(summary)


@app.route("/api/report/data", methods=["GET"])
def get_report_data():
    """
    Returns structured 7-column report dataset for dashboard inspection and copy-paste.
    Columns: DATE, NAME OF THE COMPANY, EMAIL ADDRESS, WEBSITE LINK, RESPONSES, INTERN'S FEEDBACK, Follow-ups
    """
    category = request.args.get("category")
    status = request.args.get("status")
    reply_filter = request.args.get("reply_status")
    search_q = request.args.get("q", "").lower()

    leads = logger.get_all_leads()

    if category and category != "all":
        leads = [l for l in leads if l.get("category") == category]
    if status and status != "all":
        leads = [l for l in leads if l.get("validation_status") == status]
    if reply_filter and reply_filter != "all":
        if reply_filter == "replied":
            leads = [l for l in leads if l.get("reply_status") == "replied"]
        elif reply_filter == "auto_reply":
            leads = [l for l in leads if l.get("reply_status") == "auto_reply"]
        elif reply_filter == "unreplied":
            leads = [l for l in leads if l.get("last_contacted_at") and l.get("reply_status") not in ["replied", "bounced"]]
        elif reply_filter == "uncontacted":
            leads = [l for l in leads if not l.get("last_contacted_at")]
    if search_q:
        leads = [
            l for l in leads if
            search_q in l.get("email", "").lower() or
            search_q in l.get("company_name", "").lower() or
            search_q in l.get("buyer_name", "").lower() or
            search_q in l.get("intern_feedback", "").lower() or
            search_q in l.get("follow_ups", "").lower() or
            search_q in l.get("responses", "").lower()
        ]

    report_rows = logger.get_intern_report_data(leads)
    return jsonify({
        "status": "success",
        "headers": logger.REPORT_HEADERS,
        "rows": report_rows,
        "count": len(report_rows)
    })


@app.route("/api/sent_log/data", methods=["GET"])
def get_sent_log_data():
    """
    Returns structured 5-column sent outreach log dataset for dashboard inspection and copy-paste.
    Columns: DATE, NAME OF THE COMPANY, EMAIL ADDRESS, WEBSITE LINK, RESPONSES
    """
    timeframe = request.args.get("timeframe") or request.args.get("range", "today")
    rows = logger.get_sent_logs_report_data(timeframe)
    available_dates = logger.get_available_sent_dates()
    return jsonify({
        "status": "success",
        "timeframe": timeframe,
        "headers": logger.REPORT_HEADERS,
        "rows": rows,
        "count": len(rows),
        "available_dates": available_dates
    })


@app.route("/api/export/<file_type>", methods=["GET"])
def export_file(file_type: str):
    """
    Download report or sent_log matching the 7-column employer review format:
    DATE, NAME OF THE COMPANY, EMAIL ADDRESS, WEBSITE LINK, RESPONSES, INTERN'S FEEDBACK, Follow-ups
    Supports CSV and TSV (Excel/Google Sheets Ctrl+V) formats.
    """
    export_format = request.args.get("format", "csv").lower()
    timeframe = request.args.get("timeframe") or request.args.get("range", "today")

    if file_type in ["buyers", "report", "intern_report"]:
        leads = logger.get_all_leads()
        
        # Filter if requested
        category = request.args.get("category")
        reply_filter = request.args.get("reply_status")
        if category and category != "all":
            leads = [l for l in leads if l.get("category") == category]
        if reply_filter and reply_filter != "all":
            if reply_filter == "replied":
                leads = [l for l in leads if l.get("reply_status") == "replied"]
            elif reply_filter == "unreplied":
                leads = [l for l in leads if l.get("last_contacted_at") and l.get("reply_status") != "replied"]
            elif reply_filter == "uncontacted":
                leads = [l for l in leads if not l.get("last_contacted_at")]

        if export_format == "tsv":
            tsv_data = logger.generate_report_tsv_string(leads)
            mem = io.BytesIO()
            mem.write(tsv_data.encode('utf-8'))
            mem.seek(0)
            return send_file(mem, mimetype="text/tab-separated-values", as_attachment=True, download_name="intern_outreach_report.tsv")
        else:
            csv_data = logger.generate_report_csv_string(leads)
            mem = io.BytesIO()
            mem.write(csv_data.encode('utf-8'))
            mem.seek(0)
            return send_file(mem, mimetype="text/csv", as_attachment=True, download_name="intern_outreach_report.csv")

    elif file_type == "sent_log":
        if export_format == "tsv":
            tsv_data = logger.generate_sent_log_tsv_string(timeframe)
            mem = io.BytesIO()
            mem.write(tsv_data.encode('utf-8'))
            mem.seek(0)
            download_name = f"sent_log_{timeframe}.tsv" if timeframe != "all" else "sent_log.tsv"
            return send_file(mem, mimetype="text/tab-separated-values", as_attachment=True, download_name=download_name)
        else:
            csv_data = logger.generate_sent_log_csv_string(timeframe)
            mem = io.BytesIO()
            mem.write(csv_data.encode('utf-8'))
            mem.seek(0)
            download_name = f"sent_log_{timeframe}.csv" if timeframe != "all" else "sent_log.csv"
            return send_file(mem, mimetype="text/csv", as_attachment=True, download_name=download_name)

    elif file_type == "presentation":
        path = presenter.ensure_presentation_exists()
        return send_file(path, as_attachment=True, mimetype="application/pdf", download_name=os.path.basename(path) or "Candle_Holders.pdf")

    return jsonify({"error": "File not found"}), 404


@app.route("/api/presentation/upload", methods=["POST"])
def upload_presentation():
    """
    Upload a custom export catalog PDF
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files (.pdf) are supported"}), 400

    save_path = presenter.presentation_path
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    file.save(save_path)
    return jsonify({
        "status": "success",
        "message": f"Custom catalog '{file.filename}' uploaded and attached successfully.",
        "filename": os.path.basename(save_path),
        "original_name": file.filename
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"[*] Product Zone International Export Outreach Backend running on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
