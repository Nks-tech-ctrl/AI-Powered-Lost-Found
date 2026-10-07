# FindBack — AI-Powered Lost & Found Platform

[![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-89%20Passing-success?style=for-the-badge&logo=pytest&logoColor=white)](#running-tests)


**FindBack** is an intelligent, privacy-first community lost-and-found recovery platform built with Django. It bridges the gap between individuals who have lost valuable personal items and honest finders who wish to return them. By combining rich item reporting, public search and catalog browsing, AI-driven similarity matching, and a multi-stage ownership claim verification workflow, FindBack ensures secure, confidential, and verified item recovery.

---

## Table of Contents

- [Overview & Architecture](#overview--architecture)
- [Key Features](#key-features)
  - [1. Authentication & User Profiles](#1-authentication--user-profiles)
  - [2. Lost & Found Item Reporting](#2-lost--found-item-reporting)
  - [3. Public Catalog & Smart Search](#3-public-catalog--smart-search)
  - [4. AI-Powered Matching](#4-ai-powered-matching)
  - [5. Ownership Verification & Claim Workflow](#5-ownership-verification--claim-workflow)
  - [6. Real-Time Dashboard](#6-real-time-dashboard)
- [Privacy & Security Model](#privacy--security-model)
- [Technology Stack](#technology-stack)
- [Directory Structure](#directory-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Database Setup](#database-setup)
  - [Running the Development Server](#running-the-development-server)
- [Running Tests](#running-tests)
- [URL Routing Reference](#url-routing-reference)
- [Contributing & Code Standards](#contributing--code-standards)

---

## Overview & Architecture

FindBack is built on a clean, modular Django architecture separated into focused applications:

- **`core/`**: Landing page, shared base templates, header/footer components, dynamic navigation, and global static assets.
- **`accounts/`**: User registration, session-based authentication, user profile management with custom avatars, contact details, and preferences.
- **`items/`**: Core Lost & Found domain logic, report creation workflows, owner management, public catalog browsing, faceted filtering, keyword search, and the main user dashboard.
- **`matches/`**: AI-powered potential match suggestions between reported lost and found items.
- **`claims/`**: Ownership claim submission, anti-abuse validations, claim lifecycle management (`PENDING`, `APPROVED`, `REJECTED`, `CANCELLED`), reviewer questionnaires, and atomic claim approval transactions.

---

## Key Features

### 1. Authentication & User Profiles
- **Secure Authentication**: Built on Django's standard session-based authentication system with CSRF protection on all forms.
- **User Profiles**: Custom `UserProfile` model linked one-to-one with Django's `User`, supporting avatar uploads, phone numbers, contact preferences, and address/location metadata.
- **Granular Permissions**: Strict role and ownership checks—only report owners can edit or delete their reports; only finders can review claims on items they discovered.

### 2. Lost & Found Item Reporting
- **Dedicated Reporting Flows**: Tailored forms for **Report Lost** and **Report Found** items.
- **Rich Metadata Capture**: Title, category, date lost/found, primary location, detailed description, tags, and image upload.
- **Confidential Identification Details**: Reporters can store private distinguishing marks, serial numbers, lock codes, or secret identifiers that remain completely invisible to the public and are used exclusively for verification.

### 3. Public Catalog & Smart Search
- **Public Item Catalog**: Clean grid and list views for exploring active community reports.
- **Multi-Faceted Filtering**: Filter items by type (Lost / Found), category, status, date ranges, and locations.
- **Full-Text Keyword Search**: Query item titles, descriptions, and categories.
- **Pagination & Sorting**: Fast server-side pagination with options to sort by newest, oldest, or relevance.
- **Sanitized Public Details**: Public item detail views protect sensitive reporter information and hide private verification markers.

### 4. AI-Powered Matching
- **Automated Match Suggestions**: Compares newly filed lost reports against existing found items (and vice-versa) based on title, description semantics, categories, dates, and locations.
- **Human-in-the-Loop Verification**: AI recommendations are treated as potential matches; final ownership must always be validated through the claim verification workflow.

### 5. Ownership Verification & Claim Workflow
- **Claim Submission**: Logged-in users who identify their lost property in a public found report can submit an ownership claim with a justification and answers to verification questions.
- **Anti-Abuse Protections**:
  - Users cannot submit claims on their own reports.
  - Users cannot file duplicate pending claims on the same item.
  - Claims can only be submitted on active `FOUND` items.
- **Reporter Review Interface**: Finders receive incoming claim notifications and review claimant statements and proof answers side-by-side with their private item details.
- **Website-Based Admin Claim Moderation**:
  - Staff and administrators have access to a dedicated frontend moderation portal (`/claims/admin-review/`) without visiting the Django `/admin/` panel.
  - Global moderation queue to inspect, filter by status, and search all claims across the platform.
  - Admins can inspect confidential verification details, approve claims, or reject claims directly from the website.
- **Atomic Approval & Resolution**:
  - Approving a claim updates its status to `APPROVED`, changes the item status to `CLAIMED`, and atomically auto-rejects all other pending claims on that item with audit notes.
  - Rejecting a claim marks it `REJECTED` with optional feedback while leaving the item `ACTIVE` for other claimants.
- **Claimant Management ("My Claims")**: Claimants can track their submitted claims across pending, approved, and rejected tabs, and cancel pending claims if submitted in error.

### 6. Real-Time Dashboard
- **Live Metrics**: Real-time counters for active reports, resolved items, pending claims to review, submitted claims, and potential matches.
- **Quick Action Bar**: One-click access to report items, view matches, search the catalog, and inspect claims.
- **Recent Activity Stream**: Instant snapshot of recent community activity and personal report updates.

---

## Privacy & Security Model

FindBack enforces strict data privacy rules at both the ORM and template layers:

1. **Identification Details Confidentiality**:
   - `Item.identification_details` is never rendered in public search results, public cards, or public item detail templates.
   - It is only viewable by the item reporter in their private edit/review views.
2. **Contact Privacy**:
   - Direct personal phone numbers and emails are not broadcast publicly; contact is mediated through the platform verification flow.
3. **Atomic Verification Transactions**:
   - Claim approval transitions are wrapped inside `django.db.transaction.atomic` to prevent race conditions or double-approvals when multiple claims are pending simultaneously.

---

## Technology Stack

- **Backend Framework**: [Django 5.2](https://www.djangoproject.com/)
- **Programming Language**: [Python 3.11+](https://www.python.org/)
- **Database**: SQLite (default for development; easily swappable with PostgreSQL/MySQL via `DATABASES` setting)
- **Image Processing**: [Pillow 12.3](https://python-pillow.org/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) with custom glassmorphism, responsive breakpoints, and curated color palettes
- **Icons**: [Font Awesome 6 (Free)](https://fontawesome.com/)
- **Typography**: Google Fonts ([Outfit](https://fonts.google.com/specimen/Outfit) & [Plus Jakarta Sans](https://fonts.google.com/specimen/Plus+Jakarta+Sans))
- **Frontend Interactivity**: Vanilla JavaScript ES6 modules (no bulky frontend frameworks required)

---

## Directory Structure

```text
FindBack/
├── manage.py                     # Django management script
├── requirements.txt              # Python project dependencies
├── db.sqlite3                    # SQLite development database
├── config/                       # Project root configuration
│   ├── settings.py               # Django settings, apps, context processors
│   ├── urls.py                   # Root URL routing & media handlers
│   └── wsgi.py                   # WSGI application entrypoint
├── core/                         # Core UI & site-wide layouts
│   ├── templates/                # Base layouts & reusable components
│   │   ├── base.html             # Main master template
│   │   ├── components/           # Navbar, footer, item-card, messages, sidebar
│   │   └── core/                 # Landing page (index.html)
│   ├── urls.py                   # Core URL routing
│   └── views.py                  # Home view & general handlers
├── accounts/                     # Authentication & User Management
│   ├── models.py                 # UserProfile model
│   ├── forms.py                  # Register, Login, Profile forms
│   ├── urls.py                   # /accounts/ routing
│   ├── views.py                  # Login, register, profile views
│   └── templates/accounts/       # Login, register, profile templates
├── items/                        # Lost & Found items domain
│   ├── models.py                 # Item model & status/category choices
│   ├── forms.py                  # Item creation, editing, and filter forms
│   ├── urls.py                   # /items/ routing & /dashboard/
│   ├── views.py                  # Dashboard, report lost/found, search, details
│   └── templates/items/          # Dashboard, reporting, search, detail templates
├── matches/                      # AI Matching engine
│   ├── urls.py                   # /matches/ routing
│   ├── views.py                  # Matches overview and suggestions
│   └── templates/matches/        # Matches list and comparison templates
├── claims/                       # Ownership verification & claims
│   ├── models.py                 # Claim model with UniqueConstraint & statuses
│   ├── forms.py                  # ClaimForm, RejectClaimForm
│   ├── urls.py                   # /claims/ routing
│   ├── views.py                  # Submit, review, approve, reject, cancel views
│   ├── context_processors.py     # Dynamic claim notification badges
│   └── templates/claims/         # Submit, review, my-claims templates
├── static/                       # Static assets
│   ├── css/                      # Custom stylesheets
│   ├── js/                       # Client-side scripts
│   └── images/                   # Static branding & illustrations
└── media/                        # User-uploaded files (avatars, item photos)
```

> **Template Structure Note**: In alignment with Django best practices, all application templates are organized strictly within their respective app directories (`<app>/templates/<app>/`). The root directory does not contain a top-level `templates/` folder.

---

## Getting Started

### Prerequisites

Ensure you have the following installed on your machine:
- **Python 3.11** or higher
- **Git**

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Nks-tech-ctrl/AI-Powered-Lost-Found.git
   cd AI-Powered-Lost-Found
   ```

2. **Create and activate a virtual environment**:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Database Setup

1. **Apply database migrations**:
   ```bash
   python manage.py migrate
   ```

2. **Create an administrative superuser** (optional, for Django admin access):
   ```bash
   python manage.py createsuperuser
   ```

### Running the Development Server

1. **Start the local server**:
   ```bash
   python manage.py runserver
   ```

2. **Open in browser**:
   Navigate to [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your web browser.

---

## Running Tests

FindBack includes a comprehensive automated test suite covering authentication, permissions, item workflows, atomic claim resolution, search filters, and context processors.

To execute all tests:

```bash
python manage.py test
```

To run tests for a specific application:

```bash
python manage.py test claims
python manage.py test items
python manage.py test accounts
```

All 83 tests run and pass without errors.

---

## URL Routing Reference

| URL Pattern | App | View Name | Description |
| :--- | :--- | :--- | :--- |
| `/` | `core` | `home` | Landing page showcasing features and stats |
| `/dashboard/` | `items` | `dashboard` | User dashboard with metrics, claims, and reports |
| `/accounts/register/` | `accounts` | `register` | New user account creation |
| `/accounts/login/` | `accounts` | `login` | Authenticated user sign-in |
| `/accounts/logout/` | `accounts` | `logout` | Session sign-out |
| `/accounts/profile/` | `accounts` | `profile` | User profile, avatar upload, and settings |
| `/items/report-lost/` | `items` | `report-lost` | File a new lost item report |
| `/items/report-found/` | `items` | `report-found` | File a new found item report |
| `/items/my-reports/` | `items` | `my-reports` | List of items reported by the current user |
| `/items/search/` | `items` | `search` | Public catalog with filters and pagination |
| `/items/public/<id>/` | `items` | `public-item-detail`| Public item view with claim submission CTA |
| `/matches/` | `matches` | `matches` | AI-suggested potential matches |
| `/claims/` | `claims` | `my-claims` | User's submitted claims dashboard |
| `/claims/item/<id>/submit/` | `claims` | `submit-claim` | Submit ownership claim on a found item |
| `/claims/review/` | `claims` | `claims-to-review` | Incoming claims on items reported by user |
| `/claims/admin-review/` | `claims` | `admin-claims` | Staff moderation queue to review and manage all claims |
| `/claims/review/<id>/` | `claims` | `review-claim` | Detailed verification review interface |
| `/claims/<id>/approve/` | `claims` | `approve-claim` | Approve claim and mark item claimed (POST) |
| `/claims/<id>/reject/` | `claims` | `reject-claim` | Reject claim with reviewer note (POST) |
| `/claims/<id>/cancel/` | `claims` | `cancel-claim` | Cancel pending claim (POST) |
| `/admin/` | `admin` | `admin:index` | Django administrative interface |

---

## Contributing & Code Standards

- **PEP 8**: Follow standard Python and Django conventions for naming and code organization.
- **Data Privacy**: Never render `identification_details` in public templates or endpoints.
- **Template Encapsulation**: Keep all templates in `<app>/templates/<app>/`. Do not create a root `templates/` folder.
- **Test Integrity**: Ensure all tests pass (`python manage.py test`) before submitting pull requests.
