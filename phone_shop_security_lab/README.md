# 📱 NexPhone — SQL Injection Security Lab

A fully functional phone shop web application with **intentional SQL Injection vulnerabilities** for cybersecurity education and academic study.

---

## Quick Start

```bash
# 1. Create & activate virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize database
python create_db.py

# 4. Run the server
python app.py

# 5. Open browser
#    http://127.0.0.1:5000
```

---

## Features

- **Real website** — product catalog, search, consultation form, login, admin dashboard
- **4 SQL injection types** — auth bypass, UNION extraction, boolean blind, time-based blind, error-based
- **Two modes** — toggle `SECURE_MODE` in `config.py` between vulnerable and defended
- **Attack guidance** — payloads shown inline in the UI for learning
- **Request logging** — all inputs logged to `logs.txt`
- **Admin analytics** — user management, consultation review, log viewer

---

## Tech Stack

| Layer    | Technology        |
|----------|-------------------|
| Backend  | Python 3.10+ / Flask |
| Database | SQLite           |
| Frontend | HTML5 + Custom CSS |
| Security | bcrypt (secure mode) |

---

## Security Modes

| Setting | Behavior |
|---------|----------|
| `SECURE_MODE = False` (default) | All SQL injections work — for attack demonstration |
| `SECURE_MODE = True` | Parameterized queries + bcrypt + input validation |

---

## Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | admin |
| user1 | pass1 | customer |
| alice | alice99 | customer |

---

## Attack Endpoints

| Endpoint | Attack Type |
|----------|-------------|
| `POST /login` | Authentication bypass |
| `GET /search?q=` | UNION, blind, error-based |
| `POST /consult` | UNION, INSERT-based |

---

## For Educational Use Only

This application intentionally contains security vulnerabilities. **Do not deploy on a public or production server.**

See `guide.md` for the full step-by-step attack and defense guide.
