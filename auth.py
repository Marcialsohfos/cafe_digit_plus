"""
Café_digit — authentification.
Hachage de mot de passe en PBKDF2-HMAC-SHA256 (aucune dépendance compilée,
compatible Streamlit Community Cloud). Gestion de session via st.session_state.
"""
import hashlib
import os
from datetime import datetime, timedelta

import streamlit as st

from db import get_conn, new_id, PLAN_PRICES_FCFA

try:
    SUPER_ADMIN_CODE = st.secrets.get("SUPER_ADMIN_CODE", "labscsm32015@10001b")
except Exception:
    SUPER_ADMIN_CODE = "labscsm32015@10001b"

SUPER_ADMIN_EMAIL = "superadmin@cafedigit.cm"


def hash_password(password: str, salt: str | None = None):
    if salt is None:
        salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 120_000).hex()
    return digest, salt


def verify_password(password: str, digest: str, salt: str) -> bool:
    check, _ = hash_password(password, salt)
    return check == digest


def current_user():
    return st.session_state.get("user")


def is_logged_in() -> bool:
    return current_user() is not None


def is_admin() -> bool:
    u = current_user()
    return bool(u) and u["role"] in ("ADMIN", "SUPER_ADMIN")


def is_super_admin() -> bool:
    u = current_user()
    return bool(u) and u["role"] == "SUPER_ADMIN"


def logout():
    st.session_state.pop("user", None)


def register_user(email, password, full_name, city="", organization=""):
    email = email.strip().lower()
    if not email or not password or not full_name:
        return None, "Nom, e-mail et mot de passe sont requis."
    if len(password) < 8:
        return None, "Le mot de passe doit contenir au moins 8 caractères."

    conn = get_conn()
    existing = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if existing:
        conn.close()
        return None, "Un compte existe déjà avec cet e-mail."

    digest, salt = hash_password(password)
    uid = new_id()
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO users(id,email,password_hash,salt,full_name,role,city,organization,created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (uid, email, digest, salt, full_name, "STUDENT", city, organization, now),
    )
    conn.execute(
        "INSERT INTO subscriptions(id,user_id,plan,status,started_at,expires_at,amount_fcfa,payment_ref) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (new_id(), uid, "FREE", "ACTIVE", now, None, 0, None),
    )
    conn.commit()
    conn.close()
    return {"id": uid, "email": email, "fullName": full_name, "role": "STUDENT"}, None


def login_user(email, password):
    email = email.strip().lower()
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    if not row or not verify_password(password, row["password_hash"], row["salt"]):
        return None, "Identifiants incorrects."
    user = {"id": row["id"], "email": row["email"], "fullName": row["full_name"], "role": row["role"]}
    return user, None


def super_admin_login(code: str):
    if not code or code != SUPER_ADMIN_CODE:
        return None, "Code d'accès Super Admin invalide."

    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE email=?", (SUPER_ADMIN_EMAIL,)).fetchone()
    now = datetime.utcnow().isoformat()
    if not row:
        digest, salt = hash_password(os.urandom(24).hex())
        uid = new_id()
        conn.execute(
            "INSERT INTO users(id,email,password_hash,salt,full_name,role,city,organization,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (uid, SUPER_ADMIN_EMAIL, digest, salt, "Super Administrateur — SCSM Group / Lab_Math",
             "SUPER_ADMIN", None, None, now),
        )
        conn.commit()
        user = {"id": uid, "email": SUPER_ADMIN_EMAIL,
                "fullName": "Super Administrateur — SCSM Group / Lab_Math", "role": "SUPER_ADMIN"}
    else:
        if row["role"] != "SUPER_ADMIN":
            conn.execute("UPDATE users SET role='SUPER_ADMIN' WHERE id=?", (row["id"],))
            conn.commit()
        user = {"id": row["id"], "email": row["email"], "fullName": row["full_name"], "role": "SUPER_ADMIN"}
    conn.close()
    return user, None
