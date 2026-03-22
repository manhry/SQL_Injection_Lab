"""
create_db.py — Database initializer for Phone Shop Security Lab
Run once before starting the server:  python create_db.py
"""

import sqlite3
import os
import sys

# Allow importing config from the same directory
sys.path.insert(0, os.path.dirname(__file__))
from config import DATABASE, SECURE_MODE

# Optional: bcrypt is only needed for SECURE_MODE seeding
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False


def hash_password(plain: str) -> str:
    """Return bcrypt hash if bcrypt is available, else plain text."""
    if BCRYPT_AVAILABLE:
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()
    return plain


def create_database():
    db_path = os.path.join(os.path.dirname(__file__), DATABASE)

    # Remove old DB so we always start fresh
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"[*] Removed old database: {db_path}")

    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    # ── Table: users ──────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL,
            role     TEXT    NOT NULL DEFAULT 'customer'
        )
    """)

    # ── Table: products ───────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            price       REAL    NOT NULL,
            description TEXT
        )
    """)

    # ── Table: consultations ──────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS consultations (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT,
            phone   TEXT,
            message TEXT
        )
    """)

    # ── Seed: users ───────────────────────────────────────────────────────────
    # We always store plain-text passwords in the DB for demo visibility.
    # SECURE_MODE login will hash-compare at runtime.
    seed_users = [
        ("admin",  "admin123", "admin"),
        ("user1",  "pass1",    "customer"),
        ("alice",  "alice99",  "customer"),
        ("bob",    "bobpass",  "customer"),
    ]
    cur.executemany(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        seed_users
    )

    # ── Seed: products ────────────────────────────────────────────────────────
    seed_products = [
        ("iPhone 15 Pro",
         1299.00,
         "Apple A17 Pro chip, 48MP camera system, titanium design, USB-C. "
         "Available in Natural, Blue, White, and Black Titanium."),

        ("Samsung Galaxy S24 Ultra",
         1199.00,
         "200MP camera, built-in S Pen, 6.8-inch QHD+ Dynamic AMOLED display, "
         "Snapdragon 8 Gen 3 processor."),

        ("Xiaomi 14 Pro",
         899.00,
         "Leica optics co-engineering, Snapdragon 8 Gen 3, 120W HyperCharge, "
         "6.73-inch LTPO AMOLED screen."),

        ("Google Pixel 8 Pro",
         999.00,
         "Google Tensor G3 chip, 50MP camera with AI photo enhancements, "
         "7 years of OS updates, 6.7-inch Super Actua display."),

        ("OnePlus 12",
         799.00,
         "Hasselblad camera system, 100W SUPERVOOC charging, Snapdragon 8 Gen 3, "
         "6.82-inch 2K ProXDR display."),

        ("Sony Xperia 1 VI",
         1299.00,
         "Professional cinema camera DNA, 4K 120fps video, 6.5-inch 4K HDR OLED, "
         "Snapdragon 8 Gen 3, 5000 mAh battery."),
    ]
    cur.executemany(
        "INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
        seed_products
    )

    # ── Seed: consultations ───────────────────────────────────────────────────
    seed_consults = [
        ("John Doe",   "+84901234567", "Interested in iPhone 15 Pro trade-in options."),
        ("Jane Smith", "+84912345678", "Would like a bulk quote for 10 Galaxy S24 devices."),
    ]
    cur.executemany(
        "INSERT INTO consultations (name, phone, message) VALUES (?, ?, ?)",
        seed_consults
    )

    conn.commit()
    conn.close()

    print(f"[+] Database created: {db_path}")
    print("[+] Tables: users, products, consultations")
    print("[+] Sample data inserted successfully.")
    print()
    print("  ┌─────────────────────────────────────────────┐")
    print("  │          SEEDED CREDENTIALS (DEMO)          │")
    print("  │  admin  / admin123  → role: admin           │")
    print("  │  user1  / pass1     → role: customer        │")
    print("  │  alice  / alice99   → role: customer        │")
    print("  └─────────────────────────────────────────────┘")
    print()
    print("[+] Ready! Run:  python app.py")


if __name__ == "__main__":
    create_database()
