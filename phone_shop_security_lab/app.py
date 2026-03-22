"""
app.py — Phone Shop Security Lab
=================================
A fully functional Flask web application that intentionally contains SQL
Injection vulnerabilities (when SECURE_MODE = False) for educational purposes.

Toggle SECURE_MODE in config.py to switch between vulnerable and defended modes.
"""

import os
import sqlite3
import datetime
import traceback

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, g
)

# ── Local imports ─────────────────────────────────────────────────────────────
from config import SECURE_MODE, SECRET_KEY, DATABASE, LOG_FILE

# Optional bcrypt — only used in SECURE_MODE
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

# =============================================================================
# Flask app setup
# =============================================================================
app = Flask(__name__)
app.secret_key = SECRET_KEY

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, DATABASE)
LOG_PATH = os.path.join(BASE_DIR, LOG_FILE)


# =============================================================================
# Database helpers
# =============================================================================
def get_db():
    """Return a per-request SQLite connection (stored in Flask g)."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row   # dict-like rows
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# =============================================================================
# Logging helpers
# =============================================================================
def log_request(endpoint: str, data: dict):
    """Append a request log entry to logs.txt."""
    ts   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] ENDPOINT={endpoint} | DATA={data}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)


def read_last_logs(n: int = 5) -> list:
    """Return the last n lines from logs.txt."""
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return [l.strip() for l in lines[-n:]]


# =============================================================================
# Auth helpers
# =============================================================================
def check_password(plain: str, stored: str) -> bool:
    """
    SECURE_MODE  → bcrypt comparison (stored may be plain for demo users).
    VULNERABLE   → plain-text comparison only.
    """
    if SECURE_MODE and BCRYPT_AVAILABLE:
        try:
            return bcrypt.checkpw(plain.encode(), stored.encode())
        except Exception:
            # Fall back to plain compare if hash is malformed (demo seed)
            return plain == stored
    return plain == stored


def login_required(f):
    """Decorator: redirect to /login if not authenticated."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator: redirect if user is not admin."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated


# =============================================================================
# ▌ ROUTE: Homepage  /
# =============================================================================
@app.route("/")
def index():
    db       = get_db()
    products = db.execute("SELECT * FROM products").fetchall()
    log_request("/", {})
    return render_template("index.html",
                           products=products,
                           secure_mode=SECURE_MODE)


# =============================================================================
# ▌ ROUTE: Product Detail  /product/<id>
# =============================================================================
@app.route("/product/<int:product_id>")
def product_detail(product_id):
    db      = get_db()
    product = db.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    log_request(f"/product/{product_id}", {"id": product_id})

    if not product:
        flash("Product not found.", "warning")
        return redirect(url_for("index"))

    return render_template("product.html",
                           product=product,
                           secure_mode=SECURE_MODE)


# =============================================================================
# ▌ ROUTE: Search  /search
# =============================================================================
@app.route("/search")
def search():
    query   = request.args.get("q", "").strip()
    results = []
    error   = None
    raw_sql = None

    log_request("/search", {"q": query})

    if query:
        db = get_db()

        # ── VULNERABLE MODE ─────────────────────────────────────────────────
        if not SECURE_MODE:
            # ⚠ Intentionally unsafe: raw string concatenation
            raw_sql = f"SELECT * FROM products WHERE name LIKE '%{query}%'"
            try:
                results = db.execute(raw_sql).fetchall()
            except Exception as e:
                # ⚠ Error exposed intentionally (error-based injection demo)
                error = f"SQL Error: {str(e)}"

        # ── SECURE MODE ─────────────────────────────────────────────────────
        else:
            # ✔ Parameterized query — injection impossible
            try:
                results = db.execute(
                    "SELECT * FROM products WHERE name LIKE ?",
                    (f"%{query}%",)
                ).fetchall()
            except Exception:
                error = "An error occurred. Please try again."

    return render_template("search.html",
                           query=query,
                           results=results,
                           error=error,
                           raw_sql=raw_sql,
                           secure_mode=SECURE_MODE)


# =============================================================================
# ▌ ROUTE: Login  /login
# =============================================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    error   = None
    raw_sql = None

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        log_request("/login", {"username": username, "password": password})

        db = get_db()

        # ── VULNERABLE MODE ─────────────────────────────────────────────────
        if not SECURE_MODE:
            # ⚠ Classic auth-bypass injection: ' OR '1'='1
            raw_sql = (
                f"SELECT * FROM users WHERE username = '{username}' "
                f"AND password = '{password}'"
            )
            try:
                user = db.execute(raw_sql).fetchone()
                if user:
                    session["user_id"]  = user["id"]
                    session["username"] = user["username"]
                    session["role"]     = user["role"]
                    flash(f"Welcome, {user['username']}!", "success")
                    return redirect(
                        url_for("admin") if user["role"] == "admin"
                        else url_for("index")
                    )
                else:
                    error = "Invalid username or password."
            except Exception as e:
                error = f"SQL Error: {str(e)}"

        # ── SECURE MODE ─────────────────────────────────────────────────────
        else:
            try:
                user = db.execute(
                    "SELECT * FROM users WHERE username = ?", (username,)
                ).fetchone()
                if user and check_password(password, user["password"]):
                    session["user_id"]  = user["id"]
                    session["username"] = user["username"]
                    session["role"]     = user["role"]
                    flash(f"Welcome, {user['username']}!", "success")
                    return redirect(
                        url_for("admin") if user["role"] == "admin"
                        else url_for("index")
                    )
                else:
                    error = "Invalid username or password."
            except Exception:
                error = "An error occurred. Please try again."

    return render_template("login.html",
                           error=error,
                           raw_sql=raw_sql,
                           secure_mode=SECURE_MODE)


# =============================================================================
# ▌ ROUTE: Logout  /logout
# =============================================================================
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# =============================================================================
# ▌ ROUTE: Consultation  /consult
# =============================================================================
@app.route("/consult", methods=["GET", "POST"])
def consult():
    success = False
    error   = None
    raw_sql = None

    if request.method == "POST":
        name    = request.form.get("name",    "").strip()
        phone   = request.form.get("phone",   "").strip()
        message = request.form.get("message", "").strip()

        log_request("/consult", {"name": name, "phone": phone, "message": message})

        db = get_db()

        # ── VULNERABLE MODE ─────────────────────────────────────────────────
        if not SECURE_MODE:
            # ⚠ UNION-based injection demo target
            # Payload: ' UNION SELECT 1, username, password, role FROM users --
            raw_sql = (
                f"INSERT INTO consultations (name, phone, message) "
                f"VALUES ('{name}', '{phone}', '{message}')"
            )
            try:
                db.execute(raw_sql)
                db.commit()
                success = True
            except Exception as e:
                # ⚠ Error exposed intentionally
                error = f"SQL Error: {str(e)}"

            # ── Separate SELECT to demonstrate UNION exfiltration ──────────
            # The search endpoint is a better target; we also add a readable
            # "echo" query on the name field so UNION injections are visible.
            read_sql = f"SELECT * FROM consultations WHERE name = '{name}'"
            raw_sql  = read_sql          # show the read query in the UI
            try:
                leaked = db.execute(read_sql).fetchall()
            except Exception as e:
                if not error:
                    error = f"SQL Error (read): {str(e)}"
                leaked = []

        # ── SECURE MODE ─────────────────────────────────────────────────────
        else:
            # ✔ Basic input validation
            if not name or not phone or not message:
                error = "All fields are required."
            elif len(message) > 1000:
                error = "Message is too long (max 1000 characters)."
            else:
                try:
                    db.execute(
                        "INSERT INTO consultations (name, phone, message) "
                        "VALUES (?, ?, ?)",
                        (name, phone, message)
                    )
                    db.commit()
                    success = True
                except Exception:
                    error = "Could not save your request. Please try again."

    return render_template("consult.html",
                           success=success,
                           error=error,
                           raw_sql=raw_sql,
                           secure_mode=SECURE_MODE)


# =============================================================================
# ▌ ROUTE: Admin Dashboard  /admin
# =============================================================================
@app.route("/admin")
@login_required
@admin_required
def admin():
    db = get_db()

    users         = db.execute("SELECT * FROM users").fetchall()
    consultations = db.execute("SELECT * FROM consultations").fetchall()
    total_users   = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_consult = db.execute("SELECT COUNT(*) FROM consultations").fetchone()[0]
    last_logs     = read_last_logs(5)

    log_request("/admin", {"user": session.get("username")})

    return render_template("admin.html",
                           users=users,
                           consultations=consultations,
                           total_users=total_users,
                           total_consult=total_consult,
                           last_logs=last_logs,
                           secure_mode=SECURE_MODE)


# =============================================================================
# Run
# =============================================================================
if __name__ == "__main__":
    # Ensure logs file exists
    if not os.path.exists(LOG_PATH):
        open(LOG_PATH, "w").close()

    print()
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║       Phone Shop SQL Injection Lab               ║")
    print(f"  ║       Mode: {'SECURE  ✔' if SECURE_MODE else 'VULNERABLE ⚠ '}                         ║")
    print("  ║       URL : http://127.0.0.1:5000               ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print()

    app.run(debug=True, host="127.0.0.1", port=5000)
