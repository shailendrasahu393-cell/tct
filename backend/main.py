import os
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import sqlite3
from pwdlib import PasswordHash
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="TCT Lab Portal Backend")

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "TCT_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE = os.getenv("TCT_DATABASE_PATH", "my_database.db")
SESSION_COOKIE = "tct_session"
SESSION_SECRET = os.getenv("TCT_SESSION_SECRET") or secrets.token_urlsafe(32)
SECURE_COOKIE = os.getenv("TCT_SECURE_COOKIE", "false").lower() == "true"
BOOTSTRAP_USERNAME = os.getenv("TCT_BOOTSTRAP_USERNAME", "@vivekshukla26")
BOOTSTRAP_PASSWORD_HASH = os.getenv("TCT_BOOTSTRAP_PASSWORD_HASH")
session_serializer = URLSafeTimedSerializer(SESSION_SECRET)
SESSION_MAX_AGE = int(os.getenv("TCT_SESSION_MAX_AGE", str(60 * 60 * 8)))
LOGIN_ATTEMPT_WINDOW = 60
LOGIN_ATTEMPT_LIMIT = 5
login_attempts = {}

# Password hashing
password_hash = PasswordHash.recommended()


# ============================================================
# DATABASE SETUP
# ============================================================

def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


connection = get_connection()
cursor = connection.cursor()

# Users table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        name TEXT NOT NULL DEFAULT '',
        role TEXT NOT NULL DEFAULT 'ADMIN',
        lab_id TEXT
    )
""")

for column, definition in (("name", "TEXT NOT NULL DEFAULT ''"), ("role", "TEXT NOT NULL DEFAULT 'ADMIN'"), ("lab_id", "TEXT")):
    try:
        cursor.execute(f"ALTER TABLE users ADD COLUMN {column} {definition}")
    except sqlite3.OperationalError:
        pass

# Problems table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS problems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        type TEXT NOT NULL,
        title TEXT NOT NULL,
        problem TEXT NOT NULL,
        data TEXT NOT NULL,
        description TEXT,
        FOREIGN KEY (username) REFERENCES users(username)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS labs (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        faculty_name TEXT NOT NULL,
        class_name TEXT NOT NULL,
        description TEXT NOT NULL,
        color TEXT NOT NULL
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lab_id TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        url TEXT NOT NULL,
        category TEXT NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Active',
        FOREIGN KEY (lab_id) REFERENCES labs(id)
    )
""")

cursor.executemany(
    """
    INSERT OR IGNORE INTO labs(id, name, faculty_name, class_name, description, color)
    VALUES (?, ?, ?, ?, ?, ?)
    """,
    [("lab-001", "Vivek Sir's Lab", "Vivek Sir", "CSE-A", "Problem-solving practice and weekly coding challenges.", "violet")],
)

if BOOTSTRAP_PASSWORD_HASH:
    cursor.execute(
        """
        INSERT INTO users(username, password)
        VALUES (?, ?)
        ON CONFLICT(username) DO NOTHING
        """,
        (BOOTSTRAP_USERNAME, BOOTSTRAP_PASSWORD_HASH),
    )

cursor.execute(
    "UPDATE users SET name = ?, role = ?, lab_id = ? WHERE username = ?",
    ("Vivek Sir", "SUPER_ADMIN", "lab-001", BOOTSTRAP_USERNAME),
)

if not cursor.execute("SELECT 1 FROM users WHERE username = ?", (BOOTSTRAP_USERNAME,)).fetchone():
    connection.close()
    raise RuntimeError("Bootstrap admin is missing. Set TCT_BOOTSTRAP_PASSWORD_HASH before starting the backend.")

connection.commit()
connection.close()


# ============================================================
# PYDANTIC MODELS
# ============================================================

class Faculty(BaseModel):
    username: str
    password: str


class AdminCreate(BaseModel):
    username: str
    name: str
    password: str
    lab_name: str
    class_name: str


class SessionUser(BaseModel):
    username: str
    name: str
    role: str
    lab_id: str | None = None


class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str


class Problem(BaseModel):
    username: str
    type: str
    title: str
    problem: str
    data: str
    description: str | None = None


class Link(BaseModel):
    lab_id: str
    title: str
    description: str | None = None
    url: str
    category: str
    date: str
    status: str = "Active"


# ============================================================
# PASSWORD FUNCTIONS
# ============================================================

def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def public_user(row):
    return {
        "id": row["username"],
        "name": row["name"],
        "role": row["role"],
        "labId": row["lab_id"],
        "labName": "Vivek Sir's Lab" if row["lab_id"] == "lab-001" else None,
    }


def get_authenticated_user(tct_session: str | None = Cookie(default=None)):
    if not tct_session:
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        username = session_serializer.loads(tct_session, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")

    connection = get_connection()
    user = connection.execute(
        "SELECT username, name, role, lab_id FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    connection.close()
    if not user:
        raise HTTPException(status_code=401, detail="User account not found.")
    return user


def require_admin(user=Depends(get_authenticated_user)):
    if user["role"] not in ("ADMIN", "SUPER_ADMIN"):
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user


def require_super_admin(user=Depends(get_authenticated_user)):
    if user["role"] != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Super admin access required.")
    return user


# ============================================================
# HOME
# ============================================================

@app.get("/labs")
async def get_labs():
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT id, name, faculty_name, class_name, description, color
        FROM labs
        ORDER BY CAST(SUBSTR(id, INSTR(id, '-') + 1) AS INTEGER) DESC, id DESC
        """
    ).fetchall()
    connection.close()
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "facultyName": row["faculty_name"],
            "className": row["class_name"],
            "description": row["description"],
            "color": row["color"],
        }
        for row in rows
    ]


@app.get("/labs/{lab_id}")
async def get_lab(lab_id: str):
    connection = get_connection()
    row = connection.execute(
        "SELECT id, name, faculty_name, class_name, description, color FROM labs WHERE id = ?",
        (lab_id,),
    ).fetchone()
    connection.close()
    if not row:
        raise HTTPException(status_code=404, detail="Lab not found.")
    return {
        "id": row["id"],
        "name": row["name"],
        "facultyName": row["faculty_name"],
        "className": row["class_name"],
        "description": row["description"],
        "color": row["color"],
    }


@app.delete("/labs/{lab_id}")
async def delete_lab(lab_id: str, user=Depends(require_admin)):
    if lab_id == "lab-001":
        raise HTTPException(status_code=400, detail="The bootstrap lab cannot be deleted.")

    connection = get_connection()
    try:
        lab = connection.execute("SELECT id FROM labs WHERE id = ?", (lab_id,)).fetchone()
        if not lab:
            raise HTTPException(status_code=404, detail="Lab not found.")

        connection.execute("DELETE FROM links WHERE lab_id = ?", (lab_id,))
        connection.execute("DELETE FROM users WHERE lab_id = ?", (lab_id,))
        connection.execute("DELETE FROM labs WHERE id = ?", (lab_id,))
        connection.commit()
    except HTTPException:
        connection.rollback()
        raise
    except sqlite3.Error:
        connection.rollback()
        raise HTTPException(status_code=500, detail="Lab could not be deleted.")
    finally:
        connection.close()

    return {"message": "Lab deleted successfully."}


def serialize_link(row):
    return {
        "id": row["id"],
        "labId": row["lab_id"],
        "title": row["title"],
        "description": row["description"],
        "url": row["url"],
        "category": row["category"],
        "date": row["date"],
        "status": row["status"],
    }


@app.get("/links")
async def get_links(lab_id: str | None = None):
    connection = get_connection()
    if lab_id:
        rows = connection.execute(
            """
            SELECT * FROM links
            WHERE lab_id = ?
            ORDER BY CASE WHEN lower(title) LIKE 'lab-%'
                THEN CAST(SUBSTR(title, INSTR(title, '-') + 1) AS INTEGER)
                ELSE -1 END DESC, date DESC, id DESC
            """,
            (lab_id,),
        ).fetchall()
    else:
        rows = connection.execute(
            """
            SELECT * FROM links
            ORDER BY CASE WHEN lower(title) LIKE 'lab-%'
                THEN CAST(SUBSTR(title, INSTR(title, '-') + 1) AS INTEGER)
                ELSE -1 END DESC, date DESC, id DESC
            """
        ).fetchall()
    connection.close()
    return [serialize_link(row) for row in rows]


@app.post("/links")
async def create_link(link: Link, user=Depends(require_admin)):
    lab_id = link.lab_id
    connection = get_connection()
    lab = connection.execute("SELECT id FROM labs WHERE id = ?", (lab_id,)).fetchone()
    if not lab:
        connection.close()
        raise HTTPException(status_code=404, detail="Lab not found.")
    cursor = connection.execute(
        """
        INSERT INTO links(lab_id, title, description, url, category, date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (lab_id, link.title, link.description, link.url, link.category, link.date, link.status),
    )
    connection.commit()
    row = connection.execute("SELECT * FROM links WHERE id = ?", (cursor.lastrowid,)).fetchone()
    connection.close()
    return serialize_link(row)


@app.put("/links/{link_id}")
async def update_link(link_id: int, link: Link, user=Depends(require_admin)):
    connection = get_connection()
    existing = connection.execute("SELECT id, lab_id FROM links WHERE id = ?", (link_id,)).fetchone()
    if not existing:
        connection.close()
        raise HTTPException(status_code=404, detail="Link not found.")
    lab_id = link.lab_id
    connection.execute(
        """
        UPDATE links
        SET lab_id = ?, title = ?, description = ?, url = ?, category = ?, date = ?, status = ?
        WHERE id = ?
        """,
        (lab_id, link.title, link.description, link.url, link.category, link.date, link.status, link_id),
    )
    connection.commit()
    row = connection.execute("SELECT * FROM links WHERE id = ?", (link_id,)).fetchone()
    connection.close()
    return serialize_link(row)


@app.delete("/links/{link_id}")
async def delete_link(link_id: int, user=Depends(require_admin)):
    connection = get_connection()
    existing = connection.execute("SELECT lab_id FROM links WHERE id = ?", (link_id,)).fetchone()
    if not existing:
        connection.close()
        raise HTTPException(status_code=404, detail="Link not found.")
    cursor = connection.execute("DELETE FROM links WHERE id = ?", (link_id,))
    connection.commit()
    connection.close()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Link not found.")
    return {"message": "Link successfully deleted."}

@app.get("/")
async def home():
    return {
        "message": "TCT Lab Portal Backend is running"
    }


# ============================================================
# REGISTER FACULTY
# ============================================================

@app.post("/register")
async def register(user: Faculty, _super_admin=Depends(require_super_admin)):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # Hash password before storing it
        hashed_password = hash_password(user.password)

        cursor.execute(
            """
            INSERT INTO users(username, password)
            VALUES(?, ?)
            """,
            (user.username, hashed_password)
        )

        connection.commit()

        return {
            "message": "You have been successfully registered."
        }

    except sqlite3.IntegrityError:

        raise HTTPException(
            status_code=409,
            detail="Username already exists."
        )

    finally:
        connection.close()


# ============================================================
# LOGIN
# ============================================================

@app.post("/admin")
async def create_admin(admin: AdminCreate, response: Response, _super_admin=Depends(require_super_admin)):
    username = admin.username.strip()
    if not username or not username.startswith("@"):
        raise HTTPException(status_code=422, detail="User ID must start with @.")
    if len(admin.password) < 8 or not any(character.isupper() for character in admin.password) or not any(character.islower() for character in admin.password) or not any(character.isdigit() for character in admin.password):
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters with uppercase, lowercase, and a number.")

    connection = get_connection()
    try:
        lab_id = f"lab-{username.lstrip('@').lower().replace(' ', '-')[:24]}"
        connection.execute(
            "INSERT INTO labs(id, name, faculty_name, class_name, description, color) VALUES (?, ?, ?, ?, ?, ?)",
            (lab_id, admin.lab_name, admin.name, admin.class_name, "Faculty lab resources.", "cyan"),
        )
        connection.execute(
            "INSERT INTO users(username, password, name, role, lab_id) VALUES (?, ?, ?, ?, ?)",
            (username, hash_password(admin.password), admin.name, "ADMIN", lab_id),
        )
        connection.commit()
    except sqlite3.IntegrityError:
        connection.rollback()
        raise HTTPException(status_code=409, detail="User ID or lab already exists.")
    finally:
        connection.close()
    return {"message": "Admin created successfully.", "user": {"id": username, "name": admin.name, "role": "ADMIN", "labId": lab_id, "labName": admin.lab_name}}


@app.get("/admin")
async def list_admins(_super_admin=Depends(require_super_admin)):
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT username, name, role, lab_id
        FROM users
        WHERE role IN ('ADMIN', 'SUPER_ADMIN')
        ORDER BY CASE WHEN role = 'SUPER_ADMIN' THEN 0 ELSE 1 END, name COLLATE NOCASE
        """
    ).fetchall()
    connection.close()
    return {
        "activeAdmins": len(rows),
        "admins": [
            {"id": row["username"], "name": row["name"], "role": row["role"], "labId": row["lab_id"]}
            for row in rows
        ],
    }


@app.delete("/admin/{username}")
async def delete_admin(username: str, user=Depends(require_super_admin)):
    if username == BOOTSTRAP_USERNAME or username == user["username"]:
        raise HTTPException(status_code=400, detail="The bootstrap or current super admin cannot be deleted.")

    connection = get_connection()
    try:
        admin = connection.execute(
            "SELECT username, role, lab_id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not admin or admin["role"] != "ADMIN":
            raise HTTPException(status_code=404, detail="Admin not found.")
        if admin["lab_id"]:
            connection.execute("DELETE FROM links WHERE lab_id = ?", (admin["lab_id"],))
            connection.execute("DELETE FROM labs WHERE id = ?", (admin["lab_id"],))
        connection.execute("DELETE FROM users WHERE username = ?", (username,))
        connection.commit()
    except HTTPException:
        connection.rollback()
        raise
    except sqlite3.Error:
        connection.rollback()
        raise HTTPException(status_code=500, detail="Admin could not be deleted.")
    finally:
        connection.close()
    return {"message": "Admin deleted successfully."}


@app.post("/login")
async def login(user: Faculty, request: Request, response: Response):
    client_key = request.client.host if request.client else "unknown"
    now = datetime.now(timezone.utc).timestamp()
    recent_attempts = [timestamp for timestamp in login_attempts.get(client_key, []) if now - timestamp < LOGIN_ATTEMPT_WINDOW]
    if len(recent_attempts) >= LOGIN_ATTEMPT_LIMIT:
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again in one minute.")
    recent_attempts.append(now)
    login_attempts[client_key] = recent_attempts

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT username, password
        FROM users
        WHERE username = ?
        """,
        (user.username,)
    )

    result = cursor.fetchone()

    connection.close()

    if not result:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password."
        )

    stored_hash = result["password"]

    if not verify_password(user.password, stored_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password."
        )

    response.set_cookie(
        SESSION_COOKIE,
        session_serializer.dumps(user.username),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=SECURE_COOKIE,
        samesite="lax",
    )
    user_connection = get_connection()
    user_row = user_connection.execute(
        "SELECT username, name, role, lab_id FROM users WHERE username = ?",
        (user.username,),
    ).fetchone()
    user_connection.close()
    login_attempts.pop(client_key, None)
    return {
        "message": f"{user.username} has been successfully logged in.",
        "user": {
            **public_user(user_row),
        },
    }


@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE)
    return {"message": "Logged out successfully."}


@app.get("/me")
async def current_user(user=Depends(get_authenticated_user)):
    return {"user": public_user(user)}


# ============================================================
# UPDATE FACULTY PASSWORD
# ============================================================

@app.put("/faculty/{username}/password")
async def update_password(
    username: str,
    password_data: PasswordUpdate,
    user=Depends(require_admin),
):
    if user["role"] != "SUPER_ADMIN" and user["username"] != username:
        raise HTTPException(status_code=403, detail="You can only update your own password.")

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # Find faculty
        cursor.execute(
            """
            SELECT password
            FROM users
            WHERE username = ?
            """,
            (username,)
        )

        result = cursor.fetchone()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Faculty not found."
            )

        stored_hash = result["password"]

        # Verify old password
        if not verify_password(
            password_data.old_password,
            stored_hash
        ):
            raise HTTPException(
                status_code=401,
                detail="Old password is incorrect."
            )

        # Hash new password
        new_hashed_password = hash_password(
            password_data.new_password
        )

        # Update password
        cursor.execute(
            """
            UPDATE users
            SET password = ?
            WHERE username = ?
            """,
            (new_hashed_password, username)
        )

        connection.commit()

        return {
            "message": "Password successfully updated."
        }

    finally:
        connection.close()


# ============================================================
# CREATE PROBLEM
# ============================================================

@app.post("/problems")
async def create_problem(problem: Problem, _admin=Depends(require_admin)):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # Check whether faculty exists
        cursor.execute(
            """
            SELECT username
            FROM users
            WHERE username = ?
            """,
            (problem.username,)
        )

        faculty = cursor.fetchone()

        if not faculty:
            raise HTTPException(
                status_code=404,
                detail="Faculty username does not exist."
            )

        cursor.execute(
            """
            INSERT INTO problems
            (
                username,
                type,
                title,
                problem,
                data,
                description
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                problem.username,
                problem.type,
                problem.title,
                problem.problem,
                problem.data,
                problem.description
            )
        )

        connection.commit()

        problem_id = cursor.lastrowid

        return {
            "message": "Problem successfully created.",
            "problem_id": problem_id
        }

    finally:
        connection.close()


# ============================================================
# GET ALL PROBLEMS BY FACULTY
# ============================================================

@app.get("/problems/{username}")
async def get_problems_by_faculty(username: str, _admin=Depends(require_admin)):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            username,
            type,
            title,
            problem,
            data,
            description
        FROM problems
        WHERE username = ?
        """,
        (username,)
    )

    rows = cursor.fetchall()

    connection.close()

    problems = []

    for row in rows:
        problems.append({
            "id": row["id"],
            "username": row["username"],
            "type": row["type"],
            "title": row["title"],
            "problem": row["problem"],
            "data": row["data"],
            "description": row["description"]
        })

    return {
        "username": username,
        "problems": problems
    }


# ============================================================
# GET ALL PROBLEMS
# ============================================================

@app.get("/problems")
async def get_all_problems(_admin=Depends(require_admin)):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            username,
            type,
            title,
            problem,
            data,
            description
        FROM problems
        """
    )

    rows = cursor.fetchall()

    connection.close()

    problems = []

    for row in rows:
        problems.append({
            "id": row["id"],
            "username": row["username"],
            "type": row["type"],
            "title": row["title"],
            "problem": row["problem"],
            "data": row["data"],
            "description": row["description"]
        })

    return {
        "problems": problems
    }


# ============================================================
# UPDATE PROBLEM
# ============================================================

@app.put("/problems/{problem_id}")
async def update_problem(
    problem_id: int,
    problem: Problem,
    _admin=Depends(require_admin),
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # Check whether problem exists
        cursor.execute(
            """
            SELECT id
            FROM problems
            WHERE id = ?
            """,
            (problem_id,)
        )

        existing_problem = cursor.fetchone()

        if not existing_problem:
            raise HTTPException(
                status_code=404,
                detail="Problem not found."
            )

        # Check whether faculty exists
        cursor.execute(
            """
            SELECT username
            FROM users
            WHERE username = ?
            """,
            (problem.username,)
        )

        faculty = cursor.fetchone()

        if not faculty:
            raise HTTPException(
                status_code=404,
                detail="Faculty username does not exist."
            )

        cursor.execute(
            """
            UPDATE problems
            SET
                username = ?,
                type = ?,
                title = ?,
                problem = ?,
                data = ?,
                description = ?
            WHERE id = ?
            """,
            (
                problem.username,
                problem.type,
                problem.title,
                problem.problem,
                problem.data,
                problem.description,
                problem_id
            )
        )

        connection.commit()

        return {
            "message": "Problem successfully updated.",
            "problem_id": problem_id
        }

    finally:
        connection.close()


# ============================================================
# DELETE PROBLEM
# ============================================================

@app.delete("/problems/{problem_id}")
async def delete_problem(problem_id: int, _admin=Depends(require_admin)):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # Check whether problem exists
        cursor.execute(
            """
            SELECT id
            FROM problems
            WHERE id = ?
            """,
            (problem_id,)
        )

        existing_problem = cursor.fetchone()

        if not existing_problem:
            raise HTTPException(
                status_code=404,
                detail="Problem not found."
            )

        cursor.execute(
            """
            DELETE FROM problems
            WHERE id = ?
            """,
            (problem_id,)
        )

        connection.commit()

        return {
            "message": "Problem successfully deleted.",
            "problem_id": problem_id
        }

    finally:
        connection.close()


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        port=8000,
        reload=True
    )