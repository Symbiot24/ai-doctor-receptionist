# 🏥 AI Doctor Appointment Agent

An AI-powered hospital assistant that lets patients **book, view, cancel, and reschedule** doctor appointments through **Telegram**, and gives the clinic a **REST admin API** to manage doctors, schedules, and appointments.

The system uses a **Groq-hosted LLM** as an AI receptionist that understands natural language ("Book an appointment with Dr. Mehta tomorrow at 5 PM", "Cancel my appointment"), extracts the intent and entities, and drives a guided booking flow with inline keyboards.

```
Telegram User → Telegram Bot → AI Agent (Groq) → Appointment Services → Neon PostgreSQL
                                          ↑
Clinic Dashboard (frontend) → FastAPI Admin API
```

---

## ✨ Features

### 🤖 AI Telegram Bot
- Natural-language appointment booking via **intent extraction** (Groq `openai/gpt-oss-120b`)
- Guided booking flow with inline doctor/slot keyboards
- View, cancel, and reschedule appointments
- Doctor directory queries answered using **real live data** from the database (never invented)
- Smart date parsing ("today", "tomorrow", "next monday", "day after tomorrow", "26th of august", …)
- Automatic **appointment reminders** — 24h and 1h before the slot
- 30-minute slot generation across morning/evening shifts

### 🗂️ Clinic Admin REST API (FastAPI)
- JWT-based admin authentication (Argon2id password hashing)
- Full doctor management (create, update, activate/deactivate)
- Weekly per-doctor schedules with morning/evening shifts
- Doctor & clinic day-offs
- Availability lookups with human-readable reasons
- Appointment management (list, cancel, reschedule, mark complete / no-show)
- Dashboard summary endpoint

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ (Docker image: 3.13-slim) |
| AI / LLM | Groq (`openai/gpt-oss-120b`) |
| Bot | python-telegram-bot (v22+) |
| Admin API | FastAPI + Uvicorn |
| Database | PostgreSQL (Neon) via SQLAlchemy 2.0 |
| Auth | PyJWT (HS256) + Argon2id (`argon2-cffi`) |
| Validation | Pydantic v2 |
| Config | python-dotenv |
| Logging | Loguru |
| HTTP | httpx |

---

## 📁 Project Structure

```
doctor-appointment-ai/
├── app/
│   ├── main.py                  # Entrypoint: starts the Telegram bot
│   ├── agent/                   # Groq LLM client, prompts, AI reply service
│   │   ├── doctor_agent.py      #   DoctorAgent — chat + intent extraction
│   │   ├── ai_service.py        #   Replies with live doctor context
│   │   └── prompts.py           #   System / doctors-context prompts
│   ├── api/                     # Clinic Admin REST API
│   │   ├── main.py              #   FastAPI app (port 8080) — separate process
│   │   ├── deps.py              #   DB session + JWT admin dependency
│   │   ├── routes/              #   auth, clinic, doctors, schedules, day-offs,
│   │   │                        #   availability, appointments, dashboard
│   │   └── schemas/             #   Pydantic request/response models
│   ├── auth/                    # JWT + Argon2id security, admin creation
│   ├── core/                    # config.py — env var loading
│   ├── database/                # SQLAlchemy engine, ORM models, init, migrations
│   ├── flows/booking/           # Guided booking state-machine + validators
│   ├── memory/                  # Per-user conversation & session memory
│   ├── repositories/            # Data-access layer (one per model)
│   ├── router/intent_extractor.py # LLM → structured intent/entities
│   ├── scripts/                 # (placeholder) helper scripts
│   ├── services/                # Business logic: appointments, slots,
│   │                            #   reminders, doctors, schedules, day-offs
│   ├── state/                   # In-memory booking state machine
│   ├── telegram/                # Bot wiring, handlers, callbacks, keyboards
│   └── utils/                   # Natural-language date parser
├── tests/                       # (test files currently not committed)
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.11+
- A [Telegram bot token](https://core.telegram.org/bots#how-do-i-create-a-bot) (from @BotFather)
- A [Groq API key](https://console.groq.com/keys)
- A Neon PostgreSQL database URL (`postgresql://...`)

### 2. Setup

```bash
# Clone & enter the project
git clone <your-repo-url> doctor-appointment-ai
cd doctor-appointment-ai

# Create a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env            # then fill in your real values (see below)
```

### 3. Environment Variables (`.env`)

```dotenv
# Bot & AI
TELEGRAM_BOT_TOKEN=123456:ABC...     # from @BotFather
GROQ_API_KEY=gsk_...                 # from console.groq.com
DATABASE_URL=postgresql://user:pass@host/db   # Neon PostgreSQL

# Admin API
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# JWT auth (generate with: python -c "import secrets; print(secrets.token_urlsafe(48))")
JWT_SECRET_KEY=your-long-random-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 4. Initialize the Database

```bash
# Create all tables
python -m app.database.init_db

# Run idempotent schema migrations & seeds (single clinic, schedules, admin table)
python -m app.database.migrations
```

### 5. Create the Admin Account

There are **no hardcoded admin accounts** — create the first one interactively:

```bash
python -m app.auth.create_admin
```

### 6. Run the Applications

The repo contains **two processes** that share the same database. Run each in its own terminal.

| Process | Command | Port |
|---|---|---|
| **Telegram bot** (+ reminder thread) | `python -m app.main` | — |
| **Clinic Admin API** | `python -m app.api.main` | `127.0.0.1:8080` |

The admin API exposes Swagger UI at `http://127.0.0.1:8080/docs`. Use the admin credentials from step 5 to authenticate (`POST /api/auth/login`).

---

## 🐳 Docker

```bash
# Build the image (runs the Telegram bot by default)
docker build -t doctor-appointment-ai .

# Run it — mount your .env
docker run --env-file .env doctor-appointment-ai
```

> The current `Dockerfile` starts the **Telegram bot**. To run the admin API in a container, override the command:
> ```bash
> docker run --env-file .env doctor-appointment-ai python -m app.api.main
> ```

---

## 🔌 Admin API Endpoints

All endpoints require a Bearer token (`Authorization: Bearer <jwt>`) except `GET /health` and `POST /api/auth/login`.

### Auth
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Login with email + password → JWT |
| `GET` | `/api/auth/me` | Current admin profile |
| `PUT` | `/api/auth/profile` | Update name/email |
| `PUT` | `/api/auth/password` | Change password |

### Clinic
| Method | Path | Description |
|---|---|---|
| `GET` / `PUT` | `/api/clinic` | Get / update the clinic record |
| `GET` | `/api/clinic/day-offs` | List clinic-wide day-offs |
| `POST` | `/api/clinic/day-offs` | Add a clinic day-off |
| `DELETE` | `/api/clinic/day-offs/{date}` | Remove a clinic day-off |

### Doctors
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/doctors` | List doctors (with today's availability) |
| `POST` | `/api/doctors` | Create doctor |
| `GET` | `/api/doctors/{id}` | Doctor + today's availability |
| `PUT` | `/api/doctors/{id}` | Update doctor |
| `PATCH` | `/api/doctors/{id}/activate` | Activate doctor |
| `PATCH` | `/api/doctors/{id}/deactivate` | Deactivate doctor |

### Schedules & Day-offs
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/doctors/{id}/schedule` | Weekly schedule (7 days) |
| `PUT` | `/api/doctors/{id}/schedule/{weekday}` | Upsert one weekday's schedule |
| `GET` | `/api/doctors/{id}/day-offs` | List doctor day-offs |
| `POST` | `/api/doctors/{id}/day-offs` | Add a doctor day-off |
| `DELETE` | `/api/doctors/{id}/day-offs/{date}` | Remove a doctor day-off |
| `GET` | `/api/doctors/{id}/availability?date=YYYY-MM-DD` | Available slots + reason |

### Appointments
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/appointments?status=...` | List appointments (BOOKED / COMPLETED / CANCELLED / NO_SHOW) |
| `POST` | `/api/appointments/{id}/cancel` | Cancel appointment |
| `POST` | `/api/appointments/{id}/reschedule` | Reschedule appointment |
| `POST` | `/api/appointments/{id}/status` | Set status to COMPLETED or NO_SHOW |

### Dashboard & Health
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/dashboard/summary` | Doctor counts, today's & upcoming appointments |
| `GET` | `/health` | Health check (public) |

---

## 💬 How the Bot Works

1. User sends `/start` → welcome message.
2. Free-text messages are run through `IntentExtractor`, which asks Groq to return structured JSON:
   `{"intent": "BOOK_APPOINTMENT", "entities": {"doctor": "Dr. Mehta", "appointment_date": "2026-08-20", ...}}`
3. Intents are routed:
   - `BOOK_APPOINTMENT` → guided `BookingFlow` (name → phone → age → gender → symptoms → doctor → date → time → confirm)
   - `VIEW_APPOINTMENTS` / `CANCEL_APPOINTMENT` / `RESCHEDULE_APPOINTMENT` → lists the user's booked appointments with **Cancel** / **Reschedule** inline buttons
   - `GENERAL_QUERY` → LLM reply grounded in **live doctor data** (specialization, fees, working hours, today's slots) from the database
4. On confirmation, the slot is re-checked against the database before booking to avoid double-booking.
5. A background thread sends Telegram reminders 24h and 1h before each appointment.

**Booking rules:** 30-minute slots; booking window is today up to **one calendar month ahead**; Indian mobile numbers (`6–9` followed by 9 digits); consultation fees in ₹.

> Note: Booking state and conversation memory are **in-memory** and reset when the bot restarts.

---

## 🗃️ Database Schema

| Table | Purpose |
|---|---|
| `clinics` | Single clinic record (enforced by DB trigger) |
| `doctors` | Doctor name, specialization, fee, split shifts, active flag |
| `doctor_schedules` | Per-day weekly schedule (morning/evening shifts) |
| `appointments` | Patient details, date/time, status, reminder flags |
| `doctor_day_offs` | Per-doctor leave days |
| `clinic_day_offs` | Clinic-wide closed days |
| `admin_users` | Admin accounts (Argon2id password hashes) |

---

## 🧪 Testing

The repo includes a `tests/` directory, but test source files are currently not committed. To run any tests added later:

```bash
pip install pytest
pytest -v
```

---

## 📝 Useful Commands

| Command | Purpose |
|---|---|
| `python -m app.main` | Start the Telegram bot |
| `python -m app.api.main` | Start the Admin API (`127.0.0.1:8080`) |
| `python -m app.auth.create_admin` | Create an admin account |
| `python -m app.database.init_db` | Create all tables |
| `python -m app.database.migrations` | Run idempotent migrations & seeds |
| `python -c "import secrets; print(secrets.token_urlsafe(48))"` | Generate a JWT secret |

---

## 🚧 Status

Under development. Highlights of the current state:

- ✅ Telegram bot: booking, view, cancel, reschedule, doctor Q&A
- ✅ Admin REST API with JWT auth & full doctor/schedule/availability management
- ✅ Reminders (24h / 1h before appointment)
- 🚧 Frontend dashboard (API is ready to serve it)
- 🚧 Persisting conversation memory across bot restarts

---

## 🔒 Security Notes

- Never commit the real `.env` — it contains secrets (it is git-ignored).
- `JWT_SECRET_KEY` must be a long random value.
- API responses never leak internal error details (global exception handler returns a generic 500).
- Admin passwords are hashed with Argon2id; there is no default admin account.
