# 🌐 AI-Powered Export Outreach System (ExportFlow)

A modular, production-ready full-stack application built to automate the international export prospecting and marketing workflow for export businesses.

The system aggregates multi-channel prospective buyer leads, extracts structured records, validates deliverability via DNS MX queries, classifies buyers with **Google Gemini AI**, and dispatches personalized **Gmail SMTP outreach campaigns** with dynamic PDF catalog attachments and rate limiting.

---

## 🌟 Key Architecture & Features

### 1. Functional Backend Modules (Python)
- **`5.1 search_module.py` (Buyer Search Adapter)**: Scrapes and queries Google search snippets, B2B directories, LinkedIn profiles, and company websites for target product keywords.
- **`5.2 extraction_module.py` (Data Normalization)**: Converts raw text/HTML results into structured `BuyerRecord` objects with contact name, company, email, country, and website.
- **`5.3 validation_module.py` (Algorithm 12.1 Deliverability Validator)**:
  - RFC syntax validation.
  - 150+ disposable/temporary domain blocklist.
  - Live DNS MX record resolution via `dnspython`.
  - Deliverability scoring (`Valid`, `Risky`, `Invalid`).
- **`5.4 classification_module.py` (Algorithm 12.2 AI Classifier)**:
  - Uses **Google Gemini AI** to segment leads into 5 authentic commercial B2B buyer profiles.
  - Automatically generates customized commercial export pitch angles for wholesale distributors, boutique stockists, retail chains, hospitality stagers, and OEM brands.
  - Includes offline heuristic fallback.
- **`5.5 gmail_module.py` (Algorithm 12.3 Outreach Dispatcher)**:
  - Gmail SMTP (STARTTLS 587 / SSL 465) with App Password auth.
  - Automatic reconnect on dropped socket (`SMTPServerDisconnected`) and retry.
  - Delay pacing / rate-limiting jitter to prevent spam throttling.
  - Production-ready Live Gmail SMTP delivery with rate-limiting and socket recovery.
- **`5.6 presentation_module.py` (Catalog & Pitch Deck Handler)**:
  - Verifies or automatically generates a multi-page PDF catalog (*Product Zone International Metal Candle Holder Collection Catalog*) using ReportLab.
- **`5.7 logging_module.py` (Deduplication & Persistence)**:
  - Atomic JSON database (`data/leads.json` & `data/logs.json`).
  - Automatic CSV sync (`data/buyers.csv`, `data/sent_log.csv`, `data/business_emails.csv`, `data/individual_emails.csv`).
  - Idempotent deduplication ensuring zero double-contacting.

### 2. Frontend Web Interface (React + Vite)
- **Dark Glassmorphic UI**: Ultra-clean, aesthetic interface with responsive grid layout and Lucide icons.
- **Interactive 4-Step Pipeline Stepper**:
  1. Buyer Discovery & Scraping
  2. Multi-tier Email Validation
  3. AI Classification & Angle Generation
  4. Campaign Composition & SMTP Dispatch
- **Live Metrics Overview**: Real-time stats for Discovered, Validated, Business segments, Sent count, and Delivery rates.
- **Leads Table & Inspection Drawer**: Filter by audience tags (`business`, `individual`, `valid`, `risky`), search by company/country, inspect MX validation diagnostics and AI pitches.
- **One-Click CSV Upload & Download**: Export `buyers.csv` or `company_presentation.pdf` directly from the dashboard.
- **Live Activity Terminal**: Real-time event log stream and audit history.

---

## 📁 Project Directory Structure

```
API Export/
├── backend/
│   ├── modules/
│   │   ├── search_module.py          # 5.1 Buyer Search (Scraping/Querying)
│   │   ├── extraction_module.py      # 5.2 Lead Data Extraction & Normalization
│   │   ├── validation_module.py      # 5.3 Email Validation (Algorithm 12.1)
│   │   ├── classification_module.py  # 5.4 AI Lead & Content Classifier (Algorithm 12.2)
│   │   ├── gmail_module.py           # 5.5 Gmail SMTP Dispatcher & Rate Limiting (Algorithm 12.3)
│   │   ├── presentation_module.py    # 5.6 Catalog/Pitch Deck Attachment Handler
│   │   └── logging_module.py         # 5.7 Duplicate Prevention, Metrics & Logging
│   ├── data/
│   │   ├── schema.json               # 7.1 Data storage schema & file database
│   │   ├── leads.json                # Processed and deduplicated lead records
│   │   ├── logs.json                 # Campaign delivery logs & outreach queues
│   │   ├── buyers.csv                # Exported buyer records
│   │   └── sent_log.csv              # Delivery history log
│   ├── assets/
│   │   └── company_presentation.pdf  # Generated / custom catalog pitch deck
│   ├── app.py                        # Section 8 Application API Routes / Controller
│   ├── requirements.txt              # Backend dependencies
│   └── .env.example                  # Sample environment variables
├── frontend/                         # React + Vite Dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx            # Top navbar & export triggers
│   │   │   ├── StatsOverview.jsx     # Live metrics cards
│   │   │   ├── PipelineRunner.jsx    # 4-stage pipeline controller
│   │   │   ├── LeadsTable.jsx        # Searchable leads table with modal inspection
│   │   │   ├── CampaignModal.jsx     # Email composer & SMTP dispatcher
│   │   │   ├── SettingsModal.jsx     # Credentials & pacing modal
│   │   │   └── ActivityLogs.jsx      # Event logging terminal
│   │   ├── App.jsx                   # Root application container
│   │   ├── main.jsx                  # React entry point
│   │   └── index.css                 # Glassmorphic CSS design system
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── test_backend.py                   # Automated backend verification test suite
└── README.md                         # Documentation & run guide
```

---

## 🚀 Quickstart Guide

### 1. Backend Setup
```bash
# From workspace root
pip install -r backend/requirements.txt
```

### 2. Configure Credentials (Web Interface or .env)
You can configure credentials directly via the **Settings** page in the web app or by adding them to `backend/.env`:

#### A. Generating Google 16-Character App Password
1. Ensure **2-Step Verification** is enabled on your Google Account.
2. Go to **[myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)**.
3. Under **App name**, type `ExportFlow` and click **Create**.
4. Copy the generated 16-character code into `GMAIL_APP_PASSWORD`.

#### B. Generating Google Gemini API Key
1. Go to **[aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)** and sign in.
2. Click the blue **"+ Create API key"** button.
3. Select your Google Cloud project (or choose "Create in new project").
4. Copy the generated key into `GEMINI_API_KEY`.

```env
GMAIL_EMAIL=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
GEMINI_API_KEY=your_gemini_api_key
DRY_RUN_MODE=true
```

### 3. Run Automated Tests
```bash
python test_backend.py
```

### 4. Start the Application
You can run the full-stack system in two easy ways:

#### Option A: Run Backend (Serves built React frontend on port 5000)
```bash
python backend/app.py
```
Open **`http://127.0.0.1:5000`** in your browser.

#### Option B: Run with Vite Dev Server (Hot-reloading on port 3000)
- **Terminal 1 (Backend)**:
  ```bash
  python backend/app.py
  ```
- **Terminal 2 (Frontend)**:
  ```bash
  cd frontend
  npm run dev
  ```
Open **`http://localhost:3000`** in your browser.

---

## 📋 REST API Endpoints (Section 8)

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/health` | `GET` | Health check & system status |
| `/api/leads` | `GET` | Retrieve leads with optional filter queries (`category`, `status`, `q`) |
| `/api/leads/search` | `POST` | Trigger buyer discovery & extraction for given keyword |
| `/api/leads/validate`| `POST` | Execute Algorithm 12.1 (DNS MX, regex, disposable checks) |
| `/api/leads/classify`| `POST` | Execute Algorithm 12.2 (Gemini AI segmentation & pitch copy) |
| `/api/leads/upload`  | `POST` | Upload CSV of prospective buyer leads |
| `/api/leads/clear`   | `POST` | Clear lead database for fresh pipeline run |
| `/api/campaign/send` | `POST` | Execute Algorithm 12.3 (Gmail SMTP dispatch with catalog attachment) |
| `/api/metrics`       | `GET`  | Retrieve summary stats & live event logs |
| `/api/export/<type>` | `GET`  | Download `buyers.csv`, `sent_log.csv`, or `company_presentation.pdf` |
| `/api/settings`      | `GET/POST`| Get or update runtime credentials & pacing |
