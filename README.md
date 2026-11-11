# NextGen AI POS & ERP — Cloud Multi-Tenant SaaS Platform

An enterprise-grade, offline-first, multi-tenant POS and ERP platform designed for **Retail**, **Supermarkets**, **Restaurants**, and **Wholesale & Distribution**. Built for the Nepal market with native compliance (IRD gapless billing, 13% VAT, Annex 5/7 books, eSewa, Khalti, Fonepay, Customer Khata) and designed for international scalability.

---

## 🏛 System Architecture

The platform follows a **modular monolith** backend for transactional core services paired with an autonomous **AI microservice** and **three tailored frontend web applications**:

```mermaid
graph TD
    subgraph Client Applications
        POS["React 19 POS Terminal (:3001)\nOffline Dexie.js · ESC/POS 58/80mm"]
        Dash["React 19 Business Workspace (:3000)\nERP Dashboard · Accounting · VAT Books"]
        Admin["React 19 Platform Admin (:3002)\nTenant Control Center · MRR · Telemetry"]
    end

    subgraph API Gateway / Nginx (:80)
        Nginx["Reverse Proxy · Rate Limiting · SSL"]
    end

    subgraph Core Backend (:8000)
        Django["Django 6.1.3 + DRF Modular Monolith"]
        Auth["JWT Multi-tenant Auth & RBAC"]
        Checkout["Atomic Checkout Engine & Row-Locking"]
        Inv["Immutable Stock Ledger & Transfers"]
        Acct["Double-Entry Ledger & Nepal IRD VAT"]
        Rest["Restaurant Dining, KOT & KDS Workflow"]
        Wholesale["Wholesale Price Tiers & Khata Debt"]
        SaaS["SaaS Subscriptions & Metering"]
    end

    subgraph AI Intelligence Service (:8001)
        FastAPI["FastAPI Microservice"]
        Forecast["Holt-Winters Demand Forecaster"]
        Recom["Market-Basket Recommender"]
        Copilot["Bilingual Copilot (Nepali / English)"]
    end

    subgraph Persistence & Jobs
        Postgres[(PostgreSQL 16/18)]
        Redis[(Redis 7)]
        Celery["Celery Background Workers & Beat"]
    end

    POS --> Nginx
    Dash --> Nginx
    Admin --> Nginx
    Nginx --> Django
    Nginx --> FastAPI
    Django --> Postgres
    Django --> Redis
    Django --> Celery
    FastAPI --> Postgres
```

---

## 🚀 Key Modules & Capabilities

### 1. POS Terminal (`frontend/apps/pos`) — Port `3001`
- **Offline-First Resilience**: Powered by Dexie.js (IndexedDB). Sales are queued locally if offline and automatically synchronized when connectivity resumes.
- **High-Velocity Checkout**: Barcode scanning, quick cart manipulation, hotkeys, and held carts.
- **Shift Reconciliation**: Cash float tracking, expected vs. closing cash calculation, and discrepancy recording.
- **Hardware Integration**: Real-time 58mm and 80mm ESC/POS thermal receipt formatting with ASCII fallback.
- **Customer Khata Selector**: Instant credit ledger verification and balance limit validation at the till.

### 2. Business Workspace Dashboard (`frontend/apps/dashboard`) — Port `3000`
- **Executive ERP Overview**: Daily revenue, gross margins, low stock alerts, and recent transactions.
- **Catalog & Inventory**: Multi-warehouse stock balances, batch/expiry tracking, stock transfer dispatches, and immutable stock movement audit ledger.
- **Financial Accounting & Nepal Tax**:
  - Double-entry general ledger with automatic journal posting for all sales, returns, and inventory movements.
  - Trial Balance, Profit & Loss, and Balance Sheet reports.
  - **Nepal IRD Annex 5 (Sales Book)** & **Annex 7 (Purchase Book)**.
  - **VAT Return Summary** (13% Output VAT - Input VAT reconciliation).
  - Gapless fiscal sequence enforcement and immutable **Credit Notes (फिर्ता बिल)**.
- **Restaurant KDS & Table Floor**: Table status management, Kitchen Order Ticket (KOT) generation, and multi-guest split-bill calculation.
- **Wholesale Management**: Tiered volume discount matrix and customer Khata settlement.
- **AI Copilot**: In-app business assistant supporting queries in both English and Nepali (देवनागरी).

### 3. Platform Administration (`frontend/apps/platform-admin`) — Port `3002`
- **Multi-Tenant SaaS Provisioning**: Instant onboarding of new organizations, domain slug assignment, and role configuration.
- **Subscription Billing**: Plan tiers (Starter, Professional, Enterprise), MRR/ARR analytics, and feature entitlement gating.
- **Cluster Telemetry**: Real-time monitoring of database latency, Redis cache hit rates, Celery queue depth, and security audit logs.

### 4. AI Intelligence Microservice (`ai-service`) — Port `8001`
- **Demand Forecasting (`POST /v1/forecast`)**: Holt-Winters exponential smoothing with confidence intervals and reorder alerts.
- **Market-Basket Recommendations (`POST /v1/recommendations`)**: Grocery basket co-occurrence affinity engine for cross-selling.
- **Bilingual Copilot (`POST /v1/assistant`)**: Natural language querying for store owners in Nepali and English with structured reporting tool calls.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend Monorepo** | React 19, TypeScript, Vite, Tailwind CSS, Lucide Icons, Zustand, TanStack Query |
| **Offline Engine** | Dexie.js (IndexedDB) + Custom Sync Queue |
| **Core Backend** | Django 6.1.3, Django REST Framework, SimpleJWT, Celery, Redis |
| **API Documentation** | drf-spectacular (OpenAPI 3.0 / Swagger UI) |
| **Primary Database** | PostgreSQL 16/18 (Relational integrity, UUID PKs, Row-level locking) |
| **AI Backend** | FastAPI, Uvicorn, scikit-learn, pandas, numpy |
| **Reverse Proxy** | Nginx Alpine |
| **Testing** | Pytest, pytest-django, Vitest |

---

## ⚡ Quick Start

### Option A: Local Development Setup

#### 1. Prerequisites
- Python 3.12+
- Node.js 20+ & npm 10+
- Redis (optional for background tasks; in-memory fallback available)

#### 2. Backend Setup
```bash
# Activate virtual environment
source .venv/bin/activate  # or python3 -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements/dev.txt

# Run migrations
cd backend
python manage.py migrate

# Seed realistic Nepal demo data (Namaste Supermarket)
python manage.py seed_demo_data

# Start Django development server
python manage.py runserver 0.0.0.0:8000
```

#### 3. AI Service Setup
```bash
cd ai-service
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

#### 4. Frontend Setup
```bash
cd frontend
npm install
npm run build

# To run dev servers:
npm run --workspace=@nextgen/app-dashboard dev     # http://localhost:3000
npm run --workspace=@nextgen/app-pos dev           # http://localhost:3001
npm run --workspace=@nextgen/app-platform-admin dev # http://localhost:3002
```

---

### Option B: Docker Compose Deployment

Run the entire platform with a single command:

```bash
docker-compose up --build
```

**Services Launched:**
- `nextgen_postgres`: PostgreSQL 16 database on port `5432`
- `nextgen_redis`: Redis 7 cache & broker on port `6379`
- `nextgen_django`: Core API backend on port `8000`
- `nextgen_celery`: Background asynchronous worker
- `nextgen_ai`: FastAPI AI intelligence microservice on port `8001`
- `nextgen_nginx`: API Gateway on port `80`

---

## 🔑 Demo Credentials & Test Accounts

The seeder command (`python manage.py seed_demo_data`) configures the following demo tenant:

- **Organization**: Namaste Supermarket Pvt. Ltd.
- **Tenant Slug**: `namaste-mart`
- **PAN / VAT Number**: `601234567`
- **Initial Subscription**: Active Enterprise Tier

| Account Role | Email | Password | Allowed Access |
|---|---|---|---|
| **Platform Administrator** | `admin@namaste.np` | `password123` | Platform Admin, Business Dashboard, POS |
| **Cashier / Till Operator** | `cashier1@namaste.np` | `password123` | POS Terminal Checkout |

---

## 🧪 Automated Test Suite

The test suite covers multi-tenant isolation, atomic checkout concurrency, Nepal VAT compliance, restaurant KDS, wholesale Khata, and AI forecasting:

```bash
# Run all 21 automated tests from root
source .venv/bin/activate
pytest

# Or run with coverage
pytest --cov=backend/apps
```

### Test Coverage Highlights:
- `test_tenant_isolation.py`: Cross-tenant data isolation, foreign-key reference rejection, checkout stock deduction.
- `test_milestone2_operations.py`: Cashier shift reconciliation, procurement goods receipt, stock transfers, customer Khata limits, thermal receipt ESC/POS bytes.
- `test_milestone3_operations.py`: Trial balance equation, Nepal IRD Annex 5/7 registers, VAT returns, Credit Note tax reversal, eSewa & Khalti payment verification.
- `test_milestone4_operations.py`: SaaS tier feature gates, Holt-Winters demand forecasting, market-basket recommendations.
- `test_milestone5_concurrency.py`: Concurrent checkout row-level locking, idempotent retry storm protection, Celery scheduled tasks.
- `test_restaurant_and_wholesale.py`: Restaurant table flow, KDS status transitions (`PENDING` $\to$ `SERVED`), split-bill calculations, wholesale volume price tiers.

---

## 📖 API Documentation & Endpoints

When running locally:
- **Interactive Swagger UI**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **OpenAPI Schema (YAML)**: `backend/schema.yml`
- **AI Service Health**: [http://localhost:8001/health](http://localhost:8001/health)
- **POS Terminal**: [http://localhost:3001](http://localhost:3001)
- **Business Dashboard**: [http://localhost:3000](http://localhost:3000)
- **Platform Admin Portal**: [http://localhost:3002](http://localhost:3002)

---

## 🇳🇵 Nepal Localization Features

1. **IRD Gapless Sequence**: Complies with Inland Revenue Department requirements for sequential, tamper-evident invoice numbering.
2. **Double-Entry Tax Accounting**: Automatically posts 13% Output VAT to Account `2200` upon sale and reverses it upon Credit Note issuance.
3. **Local Payment Gateways**: Server-side validation helpers for **eSewa ePay v2** (HMAC-SHA256 signature calculation) and **Khalti ePayment v2** (`pidx` lookup).
4. **Customer Khata**: Traditional credit ledger tracking with debit/credit limits, interest-free terms, and settlement journals.
5. **Multi-lingual AI**: देवनागरी Nepali and English prompts for automated sales summaries and inventory analysis.
