# =============================================================================
# config.py — Security Lab Configuration
# =============================================================================
# Toggle this to switch between VULNERABLE and SECURE mode.
#
# SECURE_MODE = False  → SQL injection vulnerabilities are ACTIVE
# SECURE_MODE = True   → Defenses are ACTIVE (parameterized queries, bcrypt)
# =============================================================================

SECURE_MODE = True          # ← Change to True to enable all defenses

SECRET_KEY   = "super-secret-lab-key-do-not-use-in-production"
DATABASE     = "shop.db"
LOG_FILE     = "logs.txt"
