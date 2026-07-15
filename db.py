"""
Café_digit — couche de données SQLite.
Rejoue fidèlement le schéma Prisma d'origine (User, Course, Module, Lesson,
Enrollment, LessonProgress, Quiz, Question, QuizAttempt, Setting,
SupportMessage, Subscription) dans une base SQLite embarquée, compatible
avec un déploiement Streamlit Community Cloud (aucun service externe requis).
"""
import base64
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

# 📦 Formats acceptés pour le dépôt de ressources/datasets par l'administration
RESOURCE_ALLOWED_EXT = {
    "csv", "xlsx", "zip", "pdf", "shp", "geojson", "gpkg",
    "sav", "rds", "tif", "tiff", "jpg", "jpeg", "png", "docx", "pptx",
}


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

CREATE TABLE IF NOT EXISTS submissions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    module_id TEXT REFERENCES modules(id) ON DELETE CASCADE,
    lesson_id TEXT REFERENCES lessons(id) ON DELETE CASCADE,
    kind TEXT NOT NULL DEFAULT 'LAB',
    title TEXT NOT NULL,
    file_name TEXT,
    file_content TEXT,
    comment TEXT,
    status TEXT NOT NULL DEFAULT 'SUBMITTED',
    grade TEXT,
    feedback TEXT,
    created_at TEXT NOT NULL,
    reviewed_at TEXT,
    reviewed_by TEXT
);

CREATE TABLE IF NOT EXISTS resources (
    id TEXT PRIMARY KEY,
    course_id TEXT REFERENCES courses(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    file_name TEXT NOT NULL,
    file_ext TEXT NOT NULL,
    file_size INTEGER NOT NULL DEFAULT 0,
    file_data TEXT NOT NULL,
    is_premium_only INTEGER NOT NULL DEFAULT 1,
    uploaded_by TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    sender_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
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
    # 🎓 Évaluation, accompagnement & certification (au niveau du cours)
    "ALTER TABLE courses ADD COLUMN final_project_text TEXT",
    "ALTER TABLE courses ADD COLUMN certification_text TEXT",
    "ALTER TABLE courses ADD COLUMN mentoring_text TEXT",
    # 📶 Suivi de progression (Drip Content) au niveau du module
    "ALTER TABLE modules ADD COLUMN requires_prior_quiz INTEGER NOT NULL DEFAULT 0",
    # 📦 Ressource téléchargeable (script .R/.py/.do) attachée à une leçon
    "ALTER TABLE lessons ADD COLUMN resource_url TEXT",
    # 🇬🇧 Cours bilingue : version anglaise éditable du contenu pédagogique
    "ALTER TABLE courses ADD COLUMN title_en TEXT",
    "ALTER TABLE courses ADD COLUMN description_en TEXT",
    "ALTER TABLE courses ADD COLUMN context_en TEXT",
    "ALTER TABLE courses ADD COLUMN final_project_text_en TEXT",
    "ALTER TABLE courses ADD COLUMN certification_text_en TEXT",
    "ALTER TABLE courses ADD COLUMN mentoring_text_en TEXT",
    "ALTER TABLE modules ADD COLUMN title_en TEXT",
    "ALTER TABLE modules ADD COLUMN objective_en TEXT",
    "ALTER TABLE lessons ADD COLUMN title_en TEXT",
    "ALTER TABLE lessons ADD COLUMN content_en TEXT",
    # 🧪🐍 Sandbox R / Python : chaque exemple est rattaché à un langage, pour
    # que les deux modes fonctionnent indépendamment
    "ALTER TABLE sandbox_examples ADD COLUMN language TEXT NOT NULL DEFAULT 'R'",
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


def get_sandbox_examples(published_only=True, language=None):
    """language: 'R', 'PYTHON', ou None pour tous les langages confondus.
    Les exemples enregistrés apparaissent automatiquement dans la Sandbox
    correspondante, sans autre action que de les avoir publiés."""
    conn = get_conn()
    q = "SELECT * FROM sandbox_examples WHERE 1=1"
    params = []
    if published_only:
        q += " AND published=1"
    if language:
        q += " AND language=?"
        params.append(language)
    q += " ORDER BY created_at DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return rows


def add_sandbox_example(title, description, code, author_id, published=True, language="R"):
    conn = get_conn()
    conn.execute(
        "INSERT INTO sandbox_examples(id,title,description,code,published,author_id,created_at,language) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (new_id(), title, description, code, int(published), author_id, datetime.utcnow().isoformat(), language),
    )
    conn.commit()
    conn.close()


def delete_sandbox_example(example_id):
    conn = get_conn()
    conn.execute("DELETE FROM sandbox_examples WHERE id=?", (example_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------- Dépôts (submissions)


def add_submission(user_id, course_id, title, kind="LAB", module_id=None, lesson_id=None,
                    file_name=None, file_content=None, comment=None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO submissions(id,user_id,course_id,module_id,lesson_id,kind,title,file_name,"
        "file_content,comment,status,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (new_id(), user_id, course_id, module_id, lesson_id, kind, title, file_name,
         file_content, comment, "SUBMITTED", datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_submissions(course_id=None, user_id=None, status=None):
    conn = get_conn()
    q = (
        "SELECT s.*, u.full_name, u.email, c.title as course_title FROM submissions s "
        "JOIN users u ON s.user_id=u.id JOIN courses c ON s.course_id=c.id WHERE 1=1"
    )
    params = []
    if course_id:
        q += " AND s.course_id=?"
        params.append(course_id)
    if user_id:
        q += " AND s.user_id=?"
        params.append(user_id)
    if status:
        q += " AND s.status=?"
        params.append(status)
    q += " ORDER BY s.created_at DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return rows


def review_submission(submission_id, status, grade, feedback, admin_id):
    conn = get_conn()
    conn.execute(
        "UPDATE submissions SET status=?, grade=?, feedback=?, reviewed_at=?, reviewed_by=? WHERE id=?",
        (status, grade or None, feedback or None, datetime.utcnow().isoformat(), admin_id, submission_id),
    )
    conn.commit()
    conn.close()


def is_module_unlocked(user_id, course_id, module_position):
    """Suivi de progression (Drip Content) : un module verrouillé n'est
    accessible qu'après réussite du quiz du module précédent."""
    if module_position <= 0:
        return True
    conn = get_conn()
    current = conn.execute(
        "SELECT requires_prior_quiz FROM modules WHERE course_id=? AND position=?",
        (course_id, module_position),
    ).fetchone()
    if not current or not current["requires_prior_quiz"]:
        conn.close()
        return True
    prev_module = conn.execute(
        "SELECT id FROM modules WHERE course_id=? AND position=?",
        (course_id, module_position - 1),
    ).fetchone()
    if not prev_module:
        conn.close()
        return True
    prev_quizzes = conn.execute(
        "SELECT id FROM quizzes WHERE module_id=? AND published=1", (prev_module["id"],)
    ).fetchall()
    if not prev_quizzes:
        conn.close()
        return True
    for q in prev_quizzes:
        passed = conn.execute(
            "SELECT 1 FROM quiz_attempts WHERE user_id=? AND quiz_id=? AND passed=1 LIMIT 1",
            (user_id, q["id"]),
        ).fetchone()
        if not passed:
            conn.close()
            return False
    conn.close()
    return True


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


# --------------------------------------------- Accès direct cours Premium


def get_active_subscription_plan(user_id):
    """Renvoie le plan payant actif le plus récent de l'utilisateur (ex.
    PREMIUM, MODULE, B2B, ou toute nouvelle formule ajoutée plus tard), ou
    None si aucun abonnement payant n'est actif. Sert à déterminer si un
    membre doit avoir un accès direct aux cours Premium."""
    conn = get_conn()
    row = conn.execute(
        "SELECT plan FROM subscriptions WHERE user_id=? AND status='ACTIVE' AND plan!='FREE' "
        "ORDER BY started_at DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    conn.close()
    return row["plan"] if row else None


def get_premium_courses():
    """Liste des cours Premium publiés (is_premium_only=1)."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM courses WHERE published=1 AND is_premium_only=1 ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return rows


def ensure_premium_access(user_id):
    """Si l'utilisateur dispose d'un abonnement payant actif (quelle que soit
    la formule — PREMIUM, MODULE, B2B, ou une future offre Standard/Gold…),
    l'inscrit automatiquement à tous les cours Premium publiés. Cela permet un
    accès direct depuis « Mon espace » ou le catalogue, sans avoir à cliquer
    manuellement sur « Débloquer ce cours » pour chacun d'eux."""
    plan = get_active_subscription_plan(user_id)
    if not plan:
        return plan
    conn = get_conn()
    courses = conn.execute(
        "SELECT id FROM courses WHERE published=1 AND is_premium_only=1"
    ).fetchall()
    now = datetime.utcnow().isoformat()
    for c in courses:
        existing = conn.execute(
            "SELECT id FROM enrollments WHERE user_id=? AND course_id=?", (user_id, c["id"])
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO enrollments(id,user_id,course_id,progress_pct,enrolled_at,completed_at) "
                "VALUES (?,?,?,?,?,?)",
                (new_id(), user_id, c["id"], 0, now, None),
            )
    conn.commit()
    conn.close()
    return plan


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


# ---------------------------------------------------- Ressources (datasets)


def human_size(num_bytes):
    """Formate une taille en octets en chaîne lisible (Ko, Mo, Go...)."""
    n = num_bytes or 0
    for unit in ("o", "Ko", "Mo", "Go"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "o" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} To"


def add_resource(course_id, title, description, file_name, file_bytes, uploaded_by, is_premium_only=True):
    """Enregistre une ressource/dataset déposée par l'administration. Le contenu
    binaire est stocké encodé en base64 (compatible avec tout type de fichier :
    csv, xlsx, zip, pdf, shp, geojson, gpkg, sav, rds, tif, jpg, png, docx, pptx…)."""
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    conn = get_conn()
    conn.execute(
        "INSERT INTO resources(id,course_id,title,description,file_name,file_ext,file_size,"
        "file_data,is_premium_only,uploaded_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            new_id(), course_id, title, description, file_name, ext, len(file_bytes),
            base64.b64encode(file_bytes).decode("ascii"), int(is_premium_only), uploaded_by,
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_resources(course_id=None, premium_only=None):
    """Liste des ressources/datasets déposés (avec le titre du cours associé,
    le cas échéant). Inclut le contenu binaire encodé, prêt pour un
    téléchargement via get_resource_bytes()."""
    conn = get_conn()
    q = (
        "SELECT r.*, c.title as course_title FROM resources r "
        "LEFT JOIN courses c ON r.course_id=c.id WHERE 1=1"
    )
    params = []
    if course_id:
        q += " AND r.course_id=?"
        params.append(course_id)
    if premium_only is not None:
        q += " AND r.is_premium_only=?"
        params.append(int(premium_only))
    q += " ORDER BY r.created_at DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return rows


def get_resource_bytes(resource_row):
    """Décode le contenu binaire d'une ressource pour un st.download_button."""
    return base64.b64decode(resource_row["file_data"])


def delete_resource(resource_id):
    conn = get_conn()
    conn.execute("DELETE FROM resources WHERE id=?", (resource_id,))
    conn.commit()
    conn.close()


# --------------------------------------------------------- Café Chat (12)


def add_chat_message(sender_id, body, recipient_id=None):
    """Envoie un message dans le salon général (recipient_id=None) ou en
    message privé à un membre donné (recipient_id=id du destinataire)."""
    body = (body or "").strip()
    if not body:
        return
    conn = get_conn()
    conn.execute(
        "INSERT INTO chat_messages(id,sender_id,recipient_id,body,created_at) VALUES (?,?,?,?,?)",
        (new_id(), sender_id, recipient_id, body, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_channel_messages(limit=200):
    """Messages du salon général « ☕ Café Chat », visibles par tous les
    membres connectés, du plus ancien au plus récent."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT m.*, u.full_name as sender_name, u.role as sender_role FROM chat_messages m "
        "JOIN users u ON m.sender_id=u.id WHERE m.recipient_id IS NULL "
        "ORDER BY m.created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return list(reversed(rows))


def get_direct_messages(user_id, other_id, limit=200):
    """Fil de discussion privé entre deux membres, du plus ancien au plus récent."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT m.*, u.full_name as sender_name FROM chat_messages m JOIN users u ON m.sender_id=u.id "
        "WHERE (m.sender_id=? AND m.recipient_id=?) OR (m.sender_id=? AND m.recipient_id=?) "
        "ORDER BY m.created_at DESC LIMIT ?",
        (user_id, other_id, other_id, user_id, limit),
    ).fetchall()
    conn.close()
    return list(reversed(rows))


def search_members(query, exclude_user_id, limit=20):
    """Recherche un membre par nom ou e-mail, pour démarrer une conversation privée."""
    query = (query or "").strip()
    if not query:
        return []
    conn = get_conn()
    like = f"%{query}%"
    rows = conn.execute(
        "SELECT id, full_name, email, role FROM users WHERE id!=? AND "
        "(full_name LIKE ? OR email LIKE ?) ORDER BY full_name LIMIT ?",
        (exclude_user_id, like, like, limit),
    ).fetchall()
    conn.close()
    return rows


def get_recent_dm_partners(user_id, limit=15):
    """Liste des membres avec qui l'utilisateur a échangé des messages privés,
    triée par date du dernier message (le plus récent en premier)."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT CASE WHEN sender_id=? THEN recipient_id ELSE sender_id END as partner_id, "
        "MAX(created_at) as last_at FROM chat_messages "
        "WHERE (sender_id=? OR recipient_id=?) AND recipient_id IS NOT NULL "
        "GROUP BY partner_id ORDER BY last_at DESC LIMIT ?",
        (user_id, user_id, user_id, limit),
    ).fetchall()
    partners = []
    for r in rows:
        u = conn.execute(
            "SELECT id, full_name, email, role FROM users WHERE id=?", (r["partner_id"],)
        ).fetchone()
        if u:
            partners.append({
                "id": u["id"], "full_name": u["full_name"], "email": u["email"],
                "role": u["role"], "last_at": r["last_at"],
            })
    conn.close()
    return partners
