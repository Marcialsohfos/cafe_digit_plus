"""
Café_digit — couche de données SQLite.
Rejoue fidèlement le schéma Prisma d'origine (User, Course, Module, Lesson,
Enrollment, LessonProgress, Quiz, Question, QuizAttempt, Setting,
SupportMessage, Subscription) dans une base SQLite embarquée, compatible
avec un déploiement Streamlit Community Cloud (aucun service externe requis).
"""
import json
import os
import sqlite3
import uuid
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "cafedigit.db")

SUPPORT_EMAIL_DEFAULT = "support@scsmaubmar.org"
SUPER_ADMIN_CODE_DEFAULT = "labscsm32015@10001b"

DEFAULT_SETTINGS = {
    "momo_numbers": "674 65 18 56 · 691 13 32 53",
    "om_numbers": "678 07 18 81 · 663 43 34 87 · 692 52 81 36",
    "intl_card_text": (
        "Le paiement par carte bancaire (Visa/Mastercard) pour les membres "
        "internationaux sera bientôt disponible directement en ligne. En "
        "attendant, contactez l'administration pour recevoir un lien de "
        "paiement sécurisé."
    ),
    "bank_deposit_text": (
        "Pour un dépôt bancaire, contactez directement l'administration afin "
        "d'obtenir les coordonnées bancaires (RIB) et la procédure à suivre."
    ),
    "support_email": SUPPORT_EMAIL_DEFAULT,
    "contact_phones": "674 65 18 56 / 691 13 32 53 · 678 07 18 81 / 663 43 34 87",
}

PLAN_PRICES_FCFA = {"PREMIUM": 15000, "MODULE": 60000, "B2B": 1000000}


def new_id() -> str:
    return uuid.uuid4().hex


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'STUDENT',
    city TEXT,
    organization TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    context TEXT,
    pillar TEXT NOT NULL DEFAULT 'Modélisation mathématique',
    level TEXT NOT NULL DEFAULT 'Débutant',
    price_fcfa INTEGER NOT NULL DEFAULT 0,
    is_premium_only INTEGER NOT NULL DEFAULT 0,
    cover_image_url TEXT,
    published INTEGER NOT NULL DEFAULT 0,
    author_id TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS modules (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    objective TEXT,
    position INTEGER NOT NULL DEFAULT 0,
    course_id TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS lessons (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    video_url TEXT,
    pdf_url TEXT,
    content TEXT,
    duration_sec INTEGER,
    module_id TEXT NOT NULL REFERENCES modules(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS enrollments (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    progress_pct INTEGER NOT NULL DEFAULT 0,
    enrolled_at TEXT NOT NULL,
    completed_at TEXT,
    UNIQUE(user_id, course_id)
);

CREATE TABLE IF NOT EXISTS lesson_progress (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    lesson_id TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL,
    UNIQUE(user_id, lesson_id)
);

CREATE TABLE IF NOT EXISTS quizzes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    module_id TEXT NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    pass_score_pct INTEGER NOT NULL DEFAULT 60,
    published INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    quiz_id TEXT NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    prompt TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    options TEXT,
    correct_answer TEXT NOT NULL,
    explanation TEXT,
    points INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS quiz_attempts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    quiz_id TEXT NOT NULL,
    answers TEXT,
    score_pct INTEGER NOT NULL,
    passed INTEGER NOT NULL,
    submitted_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS support_messages (
    id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    category TEXT NOT NULL DEFAULT 'GENERAL_REQUEST',
    subject TEXT,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'NEW',
    created_at TEXT NOT NULL,
    handled_at TEXT
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    plan TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    started_at TEXT NOT NULL,
    expires_at TEXT,
    amount_fcfa INTEGER NOT NULL DEFAULT 0,
    payment_ref TEXT,
    validated_by TEXT,
    validated_at TEXT
);

CREATE TABLE IF NOT EXISTS sandbox_examples (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    code TEXT NOT NULL,
    published INTEGER NOT NULL DEFAULT 1,
    author_id TEXT,
    created_at TEXT NOT NULL
);
"""

# Colonnes ajoutées après la première version du schéma : on les ajoute par
# migration légère (ALTER TABLE) pour ne pas casser les bases déjà déployées.
_MIGRATIONS = [
    "ALTER TABLE courses ADD COLUMN context TEXT",
    "ALTER TABLE modules ADD COLUMN objective TEXT",
    "ALTER TABLE quiz_attempts ADD COLUMN earned_points INTEGER",
    "ALTER TABLE quiz_attempts ADD COLUMN total_points INTEGER",
    "ALTER TABLE subscriptions ADD COLUMN validated_by TEXT",
    "ALTER TABLE subscriptions ADD COLUMN validated_at TEXT",
]


def _run_migrations(conn):
    for stmt in _MIGRATIONS:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError:
            pass  # colonne déjà présente
    conn.commit()


def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    _run_migrations(conn)

    # Paramètres publics par défaut
    for k, v in DEFAULT_SETTINGS.items():
        conn.execute("INSERT OR IGNORE INTO settings(key, value) VALUES (?,?)", (k, v))
    conn.commit()

    _seed_demo_course(conn)
    conn.close()


def _seed_demo_course(conn):
    row = conn.execute("SELECT id FROM courses WHERE slug=?", ("introduction-modeles-mathematiques",)).fetchone()
    if row:
        return
    now = datetime.utcnow().isoformat()
    course_id = new_id()
    conn.execute(
        "INSERT INTO courses(id,title,slug,description,pillar,level,price_fcfa,is_premium_only,"
        "cover_image_url,published,author_id,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            course_id,
            "Introduction aux modèles mathématiques",
            "introduction-modeles-mathematiques",
            "Cycle d'initiation : comprendre comment un modèle mathématique simple "
            "permet de décrire puis de prédire un phénomène du terrain (santé, "
            "urbanisme, démographie).",
            "Modélisation mathématique",
            "Débutant",
            0,
            0,
            None,
            1,
            None,
            now,
        ),
    )
    m1 = new_id()
    conn.execute("INSERT INTO modules(id,title,position,course_id) VALUES (?,?,?,?)",
                 (m1, "Module 1 — Poser le problème", 0, course_id))
    conn.execute(
        "INSERT INTO lessons(id,title,type,position,video_url,pdf_url,content,duration_sec,module_id) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (new_id(), "Pourquoi modéliser un phénomène du terrain ?", "TEXT", 0, None, None,
         "Un modèle mathématique traduit un phénomène observé (expansion d'un quartier, "
         "propagation d'une épidémie) en équations ou en règles simulables, afin de passer "
         "de la description à la prédiction.", None, m1),
    )
    conn.execute(
        "INSERT INTO lessons(id,title,type,position,video_url,pdf_url,content,duration_sec,module_id) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (new_id(), "Démonstration : de la donnée au modèle", "VIDEO", 1, None, None, None, 600, m1),
    )
    m2 = new_id()
    conn.execute("INSERT INTO modules(id,title,position,course_id) VALUES (?,?,?,?)",
                 (m2, "Module 2 — Simuler avec R", 1, course_id))
    conn.execute(
        "INSERT INTO lessons(id,title,type,position,video_url,pdf_url,content,duration_sec,module_id) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (new_id(), "Sandbox R : simuler une croissance logistique", "R_SANDBOX", 0, None, None,
         "# Modèle de croissance logistique d'un quartier\n"
         "K <- 10000   # capacité limite\n"
         "r <- 0.3     # taux de croissance\n"
         "N0 <- 100    # population initiale\n"
         "t <- 0:50\n"
         "N <- K / (1 + ((K - N0) / N0) * exp(-r * t))\n"
         "plot(t, N, type = 'l', col = 'darkgreen', lwd = 2,\n"
         "     main = 'Croissance logistique', xlab = 'Temps', ylab = 'Population')\n",
         None, m2),
    )
    quiz_id = new_id()
    conn.execute(
        "INSERT INTO quizzes(id,title,module_id,pass_score_pct,published,created_at) VALUES (?,?,?,?,?,?)",
        (quiz_id, "Quiz — Notions de base", m1, 60, 1, now),
    )
    conn.execute(
        "INSERT INTO questions(id,quiz_id,type,prompt,position,options,correct_answer,explanation,points) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (
            new_id(), quiz_id, "MCQ_SINGLE",
            "Que permet un modèle mathématique appliqué à un phénomène du terrain ?", 0,
            json.dumps([
                {"id": "a", "text": "Uniquement décrire le passé"},
                {"id": "b", "text": "Décrire puis prédire son évolution"},
                {"id": "c", "text": "Remplacer toute collecte de données"},
            ]),
            json.dumps(["b"]),
            "Le modèle part d'une description du phénomène observé pour ensuite en simuler "
            "l'évolution future.",
            1,
        ),
    )
    conn.commit()


def get_settings():
    conn = get_conn()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    values = dict(DEFAULT_SETTINGS)
    for r in rows:
        values[r["key"]] = r["value"]
    return values


def set_setting(key, value):
    conn = get_conn()
    conn.execute(
        "INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


# --------------------------------------------------------------- Sandbox R


def get_sandbox_examples(published_only=True):
    conn = get_conn()
    if published_only:
        rows = conn.execute(
            "SELECT * FROM sandbox_examples WHERE published=1 ORDER BY created_at DESC"
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM sandbox_examples ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows


def add_sandbox_example(title, description, code, author_id, published=True):
    conn = get_conn()
    conn.execute(
        "INSERT INTO sandbox_examples(id,title,description,code,published,author_id,created_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (new_id(), title, description, code, int(published), author_id, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def delete_sandbox_example(example_id):
    conn = get_conn()
    conn.execute("DELETE FROM sandbox_examples WHERE id=?", (example_id,))
    conn.commit()
    conn.close()


# ------------------------------------------------------ Suivi quiz / cours


def get_course_quiz_summary(user_id, course_id):
    """Nombre total de bonnes réponses trouvées par l'apprenant pour un cours
    donné, en comptant la meilleure tentative pour chaque quiz du cours."""
    conn = get_conn()
    quizzes = conn.execute(
        "SELECT q.id FROM quizzes q JOIN modules m ON q.module_id=m.id WHERE m.course_id=?",
        (course_id,),
    ).fetchall()
    total_correct, total_possible, quizzes_passed = 0, 0, 0
    for q in quizzes:
        best = conn.execute(
            "SELECT * FROM quiz_attempts WHERE user_id=? AND quiz_id=? "
            "ORDER BY score_pct DESC, submitted_at DESC LIMIT 1",
            (user_id, q["id"]),
        ).fetchone()
        if best:
            total_correct += best["earned_points"] or 0
            total_possible += best["total_points"] or 0
            if best["passed"]:
                quizzes_passed += 1
    conn.close()
    return {
        "total_correct": total_correct,
        "total_possible": total_possible,
        "quizzes_total": len(quizzes),
        "quizzes_passed": quizzes_passed,
    }


# ------------------------------------------------------ Validation manuelle


def validate_subscription_by_email(email, plan, payment_ref, amount_fcfa, admin_id, duration_days=30):
    """Utilisé par le Super Admin / Admin pour valider un abonnement (ex.
    Premium) en saisissant directement l'e-mail de l'abonné et sa référence
    de paiement. Active immédiatement l'accès à l'espace correspondant."""
    conn = get_conn()
    user_row = conn.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
    if not user_row:
        conn.close()
        return None, "Aucun compte trouvé avec cet e-mail. Vérifiez l'orthographe ou demandez à l'abonné de créer son compte."
    now = datetime.utcnow().isoformat()
    expires = (datetime.utcnow() + timedelta(days=duration_days)).isoformat() if duration_days else None
    conn.execute(
        "INSERT INTO subscriptions(id,user_id,plan,status,started_at,expires_at,amount_fcfa,payment_ref,"
        "validated_by,validated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (new_id(), user_row["id"], plan, "ACTIVE", now, expires, int(amount_fcfa), payment_ref or None,
         admin_id, now),
    )
    conn.commit()
    conn.close()
    return dict(user_row), None
