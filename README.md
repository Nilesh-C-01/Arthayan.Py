<div align="center">

<img src="https://img.shields.io/badge/₹-Arthayan.Py-1D9E75?style=for-the-badge&labelColor=0F6E56&color=1D9E75" height="40"/>

# Arthayan.Py

**Enterprise Finance & Analytics Portal**

Multi-role access control · Real-time anomaly detection · Chart.js dashboards · JWT auth

[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-arthayan--py.onrender.com-1D9E75?style=for-the-badge)](https://arthayan-py.onrender.com)

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python%203.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-D71F00?style=flat-square)](https://sqlalchemy.org)
[![JWT](https://img.shields.io/badge/JWT-Auth-000000?style=flat-square&logo=jsonwebtokens)](https://jwt.io)
[![Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7?style=flat-square)](https://render.com)

</div>

---

## What is Arthayan?

**Arthayan** (अर्थयन — *"the journey of money"*) is a full-stack finance management platform with multi-role access control, intelligent anomaly detection, and a real-time analytics dashboard. It's not just an expense tracker — it's a platform where different classes of users (Admin, Analyst, Viewer) interact with financial data at distinct privilege levels, enforced server-side on every route.

Built to answer a real engineering question: *"How do you design a secure, multi-tenant financial system with clean architecture and zero bloat?"*

---

## Stats

| Metric | Value |
|--------|-------|
| Access roles | 3 (Admin · Analyst · Viewer) |
| Analytics charts | 8+ (pie, line, bar, heatmap) |
| API endpoints | 14 |
| Anomaly threshold | 3× global average |
| Database | SQLite (dev) · PostgreSQL-ready (prod) |
| Deployment | Render (live) |

---

## Features

### 🔐 JWT Authentication
Stateless auth via **HTTP-only secure cookies**. JWT payload carries `sub` (username) + `role`. 24-hour token expiry. Every sensitive route re-validates from the token — client-side role claims are never trusted.

### 👥 3-Tier Role-Based Access Control (RBAC)

| Permission | Admin | Analyst | Viewer |
|---|:---:|:---:|:---:|
| View all transactions | ✅ | ✅ | ❌ |
| View own transactions | ✅ | ✅ | ✅ |
| Create / edit / delete | ✅ | ❌ | ✅ (own only) |
| CSV export | ✅ | ✅ | ❌ |
| Global analytics dashboard | ✅ | ✅ | ❌ |
| Provision / purge users | ✅ | ❌ | ❌ |

### 📊 Analytics Engine
All metrics computed server-side in Python on every request, injected via Jinja2 into Chart.js:

- **Balance Summary** — Total income vs. expense vs. net balance
- **Month-over-Month Variance** — % change in spend vs. last calendar month
- **Category Breakdown** — Separate pie charts for expense and income
- **Net Cash Flow Timeline** — Daily net flow as a line chart
- **Monthly Aggregates** — Bar chart across rolling months
- **Weekly Heatmap** — Day-of-week spending intensity (Mon–Sun)
- **Top Spenders & Earners** — Leaderboard (Admin/Analyst view)
- **Average Transaction Value by Category** — Top 5 highest-spend categories

### 🚨 Anomaly Detection
Any transaction exceeding **3× the global expense average** is automatically flagged on the dashboard. No configuration required — it just works on every load.

### 📁 CSV Export
One-click full dataset download for Admin and Analyst roles. Streams directly from SQLite — no temp files written.

### 🔍 Smart Filtering
Filter by transaction type, category, or month. Free-text search across description and category fields simultaneously (`ILIKE` on both columns).

---

## Architecture

```
Arthayan.Py/
├── app/
│   ├── main.py                  # FastAPI app entrypoint, DB init
│   ├── core/
│   │   └── config.py            # Centralized settings (env-ready)
│   ├── models/
│   │   ├── database.py          # SQLAlchemy engine + session factory
│   │   └── domain.py            # ORM models: User, Transaction
│   ├── schemas/
│   │   └── schemas.py           # Pydantic v2 I/O validation
│   ├── api/
│   │   ├── dependencies.py      # DB session + auth dependencies
│   │   └── routes/
│   │       └── api.py           # All 14 endpoints
│   └── templates/
│       ├── login.html           # Role-selector login UI
│       ├── signup.html          # Self-registration portal
│       └── dashboard.html       # Full analytics + CRUD panel
└── requirements.txt
```

**Design principle:** Flat and readable. One router, one config, clean separation of models from schemas. Swapping SQLite for PostgreSQL is a one-line change in `config.py`.

---

## API Reference

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| `GET` | `/` | Public | Login page |
| `POST` | `/login` | Public | Authenticate + issue JWT cookie |
| `GET` | `/signup` | Public | Registration page |
| `POST` | `/signup` | Public | Create Viewer account |
| `GET` | `/dashboard` | Auth | Analytics + CRUD dashboard |
| `POST` | `/transaction` | Admin, Viewer | Create transaction |
| `POST` | `/transaction/update/{id}` | Admin, Owner | Edit transaction |
| `POST` | `/transaction/delete/{id}` | Admin, Owner | Delete transaction |
| `POST` | `/admin/create_user` | Admin | Provision new user |
| `POST` | `/admin/purge_user` | Admin | Wipe a user's ledger |
| `POST` | `/change_password` | Auth | Update own password |
| `GET` | `/export_csv` | Admin, Analyst | Download full CSV |
| `GET` | `/logout` | Auth | Clear session cookie |
| `GET` | `/health` | Public | Service health check |

---

## Running Locally

**Prerequisites:** Python 3.11+

```bash
# Clone
git clone https://github.com/Nilesh-C-01/Arthayan.Py.git
cd Arthayan.Py

# Install
pip install -r requirements.txt

# Run
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`

**Seeded accounts** (auto-created on first run):

| Username | Password | Role |
|----------|----------|------|
| `Admin` | `password` | Admin |
| `Analyst` | `password` | Analyst |

Or register a new **Viewer** account from the signup page.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| ORM | SQLAlchemy |
| Database | SQLite (dev) · PostgreSQL-ready (prod) |
| Auth | PyJWT · HTTP-only secure cookies |
| Validation | Pydantic v2 |
| Templating | Jinja2 |
| Charts | Chart.js |
| Deployment | Render |

---

## Roadmap

- [ ] Password hashing with `bcrypt` (currently plaintext — dev mode)
- [ ] PostgreSQL migration for persistent Render deployment
- [ ] Budget targets with real-time progress tracking
- [ ] PDF statement export
- [ ] Anomaly alert emails
- [ ] REST API + Swagger UI for external integrations

---

<div align="center">

Built by **[Nilesh Choudhury](https://linkedin.com/in/nilesh01)** · [GitHub](https://github.com/Nilesh-C-01)

*"Finance is just data. Data deserves structure. Structure deserves code."*

</div>
