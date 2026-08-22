import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import firebase_admin
from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import FieldFilter
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pwdlib import PasswordHash
from pydantic import BaseModel, field_validator


BACKEND_DIR = Path(__file__).resolve().parent


def load_backend_env():
    env_path = BACKEND_DIR / ".env"
    if not env_path.exists():
        return
    current_key = None
    current_value: list[str] = []

    def flush():
        nonlocal current_key, current_value
        if current_key and current_key not in os.environ:
            os.environ[current_key] = "\n".join(current_value).strip()
        current_key = None
        current_value = []

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line and line.split("=", 1)[0].replace("_", "").isalnum():
            flush()
            current_key, value = line.split("=", 1)
            current_key = current_key.strip()
            current_value = [value.strip()]
        elif current_key == "FIREBASE_SERVICE_ACCOUNT_JSON":
            current_value.append(raw_line)
    flush()


load_backend_env()


def _firebase_client():
    """Initialize Firebase Admin using a local JSON file or Render env JSON."""
    if firebase_admin._apps:
        return firestore.client()

    credential_value = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    project_id = os.getenv("FIREBASE_PROJECT_ID", "").strip()

    if not credential_value:
        raise RuntimeError(
            "FIREBASE_SERVICE_ACCOUNT_JSON is required. "
            "Set it to the local service-account JSON path for local development "
            "or the complete service-account JSON object on Render."
        )

    # Local development: allow a relative/absolute path to the JSON file.
    credential_path = Path(credential_value)
    if not credential_path.is_absolute():
        credential_path = BACKEND_DIR / credential_path

    if credential_path.is_file():
        credential = credentials.Certificate(str(credential_path))
    else:
        # Render: the complete service-account JSON is stored in an env variable.
        try:
            service_account_info = json.loads(credential_value)
        except json.JSONDecodeError:
            raise RuntimeError(
                "FIREBASE_SERVICE_ACCOUNT_JSON must be either a valid path to "
                "a service-account JSON file or a valid JSON object."
            ) from None

        if not isinstance(service_account_info, dict):
            raise RuntimeError(
                "FIREBASE_SERVICE_ACCOUNT_JSON must contain a JSON object."
            )

        credential = credentials.Certificate(service_account_info)

    options = {"projectId": project_id} if project_id else {}
    firebase_admin.initialize_app(credential, options)
    return firestore.client()


db = _firebase_client()
app = FastAPI(title="TCT Lab Portal Backend")
cors_origins = [origin.strip() for origin in os.getenv("TCT_CORS_ORIGINS", "").split(",") if origin.strip()]
if "*" in cors_origins:
    raise RuntimeError("TCT_CORS_ORIGINS cannot include '*' when credentialed cookies are enabled")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)
password_hash = PasswordHash.recommended()
SESSION_COOKIE = "tct_session"
SESSION_SECRET = os.getenv("TCT_SESSION_SECRET")
if not SESSION_SECRET:
    raise RuntimeError("TCT_SESSION_SECRET must be set in production")
serializer = URLSafeTimedSerializer(SESSION_SECRET)
SESSION_MAX_AGE = int(os.getenv("TCT_SESSION_MAX_AGE", str(60 * 60 * 8)))
SECURE_COOKIE = os.getenv("TCT_SECURE_COOKIE", "true").lower() == "true"
COOKIE_SAMESITE = os.getenv("TCT_COOKIE_SAMESITE", "lax").lower()
if COOKIE_SAMESITE not in {"lax", "strict", "none"}:
    raise RuntimeError("TCT_COOKIE_SAMESITE must be one of: lax, strict, none")
if COOKIE_SAMESITE == "none" and not SECURE_COOKIE:
    raise RuntimeError("TCT_COOKIE_SAMESITE=none requires TCT_SECURE_COOKIE=true")
BOOTSTRAP_USERNAME = os.getenv("TCT_BOOTSTRAP_USERNAME", "@vivekshukla26")
BOOTSTRAP_PASSWORD_HASH = os.getenv("TCT_BOOTSTRAP_PASSWORD_HASH")
LOGIN_ATTEMPT_WINDOW = 60
LOGIN_ATTEMPT_LIMIT = 5
login_attempts: dict[str, list[float]] = {}


def ensure_bootstrap_admin():
    if not BOOTSTRAP_PASSWORD_HASH:
        return
    lab_ref = doc("labs", "lab-001")
    user_ref = doc("users", BOOTSTRAP_USERNAME)
    if not lab_ref.get().exists:
        lab_ref.set({"name": "Vivek Sir's Lab", "faculty_name": "Vivek Sir", "class_name": "CSE-A", "description": "Problem-solving practice and weekly coding challenges.", "color": "violet"})
    if not user_ref.get().exists:
        user_ref.set({"username": BOOTSTRAP_USERNAME, "name": "Vivek Sir", "role": "SUPER_ADMIN", "lab_id": "lab-001"})


class Faculty(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Username is required.")
        return value


class AdminCreate(BaseModel):
    username: str
    name: str
    password: str
    lab_name: str
    class_name: str

    @field_validator("username", "name", "password", "lab_name", "class_name")
    @classmethod
    def required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field is required.")
        return value


class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

    @field_validator("old_password", "new_password")
    @classmethod
    def required_password(cls, value: str) -> str:
        if not value:
            raise ValueError("Password is required.")
        return value


class Problem(BaseModel):
    username: str
    type: str
    title: str
    problem: str
    data: str
    description: str | None = None

    @field_validator("username", "type", "title", "problem", "data")
    @classmethod
    def required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field is required.")
        return value


class Link(BaseModel):
    lab_id: str
    title: str
    description: str | None = None
    url: str
    category: str
    date: str
    status: str = "Active"

    @field_validator("lab_id", "title", "url", "category", "date", "status")
    @classmethod
    def required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field is required.")
        return value


def hash_password(value: str) -> str:
    return password_hash.hash(value)


def verify_password(value: str, hashed: str) -> bool:
    try:
        return password_hash.verify(value, hashed)
    except Exception:
        return False


def doc(collection: str, key: str):
    return db.collection(collection).document(key)


def validate_password_strength(value: str):
    if len(value) < 8 or not any(c.isupper() for c in value) or not any(c.islower() for c in value) or not any(c.isdigit() for c in value):
        raise HTTPException(422, "Password must be at least 8 characters with uppercase, lowercase, and a number.")


def can_manage_lab(user: dict[str, Any], lab_id: str | None) -> bool:
    return user.get("role") == "SUPER_ADMIN" or (lab_id is not None and user.get("lab_id") == lab_id)


def require_lab_access(user: dict[str, Any], lab_id: str | None):
    if not can_manage_lab(user, lab_id):
        raise HTTPException(403, "You cannot manage resources for this lab.")


def set_session_cookie(response: Response, username: str):
    response.set_cookie(
        SESSION_COOKIE,
        serializer.dumps(username),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=SECURE_COOKIE,
        samesite=COOKIE_SAMESITE,
        path="/",
    )


def clear_session_cookie(response: Response):
    response.delete_cookie(SESSION_COOKIE, path="/", secure=SECURE_COOKIE, httponly=True, samesite=COOKIE_SAMESITE)


ensure_bootstrap_admin()


def public_user(data: dict[str, Any]):
    lab_id = data.get("lab_id")
    lab = doc("labs", lab_id).get() if lab_id else None
    return {
        "id": data["username"], "name": data.get("name", ""),
        "role": data.get("role", "ADMIN"), "labId": lab_id,
        "labName": lab.to_dict().get("name") if lab and lab.exists else None,
    }


def authenticated_user(tct_session: str | None = Cookie(default=None)):
    if not tct_session:
        raise HTTPException(401, "Authentication required.")
    try:
        username = serializer.loads(tct_session, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        raise HTTPException(401, "Session expired. Please log in again.")
    snapshot = doc("users", username).get()
    if not snapshot.exists:
        raise HTTPException(401, "User account not found.")
    return snapshot.to_dict()


def require_admin(user=Depends(authenticated_user)):
    if user.get("role") not in ("ADMIN", "SUPER_ADMIN"):
        raise HTTPException(403, "Admin access required.")
    return user


def require_super_admin(user=Depends(authenticated_user)):
    if user.get("role") != "SUPER_ADMIN":
        raise HTTPException(403, "Super admin access required.")
    return user


def lab_json(snapshot):
    data = snapshot.to_dict()
    return {"id": snapshot.id, "name": data.get("name", ""), "facultyName": data.get("faculty_name", ""),
            "className": data.get("class_name", ""), "description": data.get("description", ""), "color": data.get("color", "")}


def link_json(snapshot):
    data = snapshot.to_dict()
    return {"id": snapshot.id, "labId": data["lab_id"], "title": data["title"], "description": data.get("description"),
            "url": data["url"], "category": data["category"], "date": data["date"], "status": data.get("status", "Active")}


def problem_json(snapshot):
    data = snapshot.to_dict()
    return {"id": snapshot.id, **{key: data.get(key) for key in ("username", "type", "title", "problem", "data", "description")}}


@app.get("/")
def home():
    return {"message": "TCT Lab Portal Backend is running"}


@app.get("/labs")
def get_labs():
    snapshots = list(db.collection("labs").stream())
    snapshots.sort(key=lambda item: item.id, reverse=True)
    return [lab_json(item) for item in snapshots]


@app.get("/labs/{lab_id}")
def get_lab(lab_id: str):
    snapshot = doc("labs", lab_id).get()
    if not snapshot.exists:
        raise HTTPException(404, "Lab not found.")
    return lab_json(snapshot)


@app.delete("/labs/{lab_id}")
def delete_lab(lab_id: str, user=Depends(require_super_admin)):
    if lab_id == "lab-001":
        raise HTTPException(400, "The bootstrap lab cannot be deleted.")
    lab = doc("labs", lab_id).get()
    if not lab.exists:
        raise HTTPException(404, "Lab not found.")
    batch = db.batch()
    for collection in ("links", "users"):
        for item in db.collection(collection).where(filter=FieldFilter("lab_id", "==", lab_id)).stream():
            batch.delete(item.reference)
    batch.delete(doc("labs", lab_id))
    batch.commit()
    return {"message": "Lab deleted successfully."}


@app.get("/links")
def get_links(lab_id: str | None = None):
    query = db.collection("links")
    if lab_id:
        query = query.where(filter=FieldFilter("lab_id", "==", lab_id))
    links = [link_json(item) for item in query.stream()]
    return sorted(links, key=lambda item: (item["date"], str(item["id"])), reverse=True)


@app.post("/links")
def create_link(link: Link, user=Depends(require_admin)):
    require_lab_access(user, link.lab_id)
    if not doc("labs", link.lab_id).get().exists:
        raise HTTPException(404, "Lab not found.")
    reference = db.collection("links").document()
    reference.set(link.model_dump())
    return link_json(reference.get())


@app.put("/links/{link_id}")
def update_link(link_id: str, link: Link, user=Depends(require_admin)):
    reference = doc("links", link_id)
    snapshot = reference.get()
    if not snapshot.exists:
        raise HTTPException(404, "Link not found.")
    require_lab_access(user, snapshot.to_dict().get("lab_id"))
    require_lab_access(user, link.lab_id)
    if not doc("labs", link.lab_id).get().exists:
        raise HTTPException(404, "Lab not found.")
    reference.set(link.model_dump())
    return link_json(reference.get())


@app.delete("/links/{link_id}")
def delete_link(link_id: str, user=Depends(require_admin)):
    reference = doc("links", link_id)
    snapshot = reference.get()
    if not snapshot.exists:
        raise HTTPException(404, "Link not found.")
    require_lab_access(user, snapshot.to_dict().get("lab_id"))
    reference.delete()
    return {"message": "Link successfully deleted."}


@app.post("/admin")
def create_admin(admin: AdminCreate, _super_admin=Depends(require_super_admin)):
    username = admin.username.strip()
    if not username.startswith("@"):
        raise HTTPException(422, "User ID must start with @.")
    validate_password_strength(admin.password)
    lab_id = f"lab-{username.lstrip('@').lower().replace(' ', '-')[:24]}"
    user_ref, lab_ref = doc("users", username), doc("labs", lab_id)
    if user_ref.get().exists or lab_ref.get().exists:
        raise HTTPException(409, "User ID or lab already exists.")
    batch = db.batch()
    batch.set(lab_ref, {"name": admin.lab_name, "faculty_name": admin.name, "class_name": admin.class_name, "description": "Faculty lab resources.", "color": "cyan"})
    batch.set(user_ref, {"username": username, "password": hash_password(admin.password), "name": admin.name, "role": "ADMIN", "lab_id": lab_id})
    batch.commit()
    return {"message": "Admin created successfully.", "user": {"id": username, "name": admin.name, "role": "ADMIN", "labId": lab_id, "labName": admin.lab_name}}


@app.post("/register")
def register(user: Faculty, _super_admin=Depends(require_super_admin)):
    username = user.username.strip()
    if not username.startswith("@"):
        raise HTTPException(422, "User ID must start with @.")
    validate_password_strength(user.password)
    reference = doc("users", username)
    if reference.get().exists:
        raise HTTPException(409, "Username already exists.")
    reference.set({"username": username, "password": hash_password(user.password), "name": "", "role": "ADMIN", "lab_id": None})
    return {"message": "You have been successfully registered."}


@app.get("/admin")
def list_admins(_super_admin=Depends(require_super_admin)):
    admins = [item.to_dict() for item in db.collection("users").stream()]
    admins = [item for item in admins if item.get("role") in ("ADMIN", "SUPER_ADMIN")]
    admins.sort(key=lambda item: (item.get("role") != "SUPER_ADMIN", item.get("name", "").lower()))
    return {"activeAdmins": len(admins), "admins": [{"id": item["username"], "name": item.get("name", ""), "role": item.get("role"), "labId": item.get("lab_id")} for item in admins]}


@app.delete("/admin/{username}")
def delete_admin(username: str, user=Depends(require_super_admin)):
    if username in (BOOTSTRAP_USERNAME, user["username"]):
        raise HTTPException(400, "The bootstrap or current super admin cannot be deleted.")
    snapshot = doc("users", username).get()
    if not snapshot.exists or snapshot.to_dict().get("role") != "ADMIN":
        raise HTTPException(404, "Admin not found.")
    lab_id = snapshot.to_dict().get("lab_id")
    batch = db.batch()
    for link in db.collection("links").where(filter=FieldFilter("lab_id", "==", lab_id)).stream():
        batch.delete(link.reference)
    if lab_id:
        batch.delete(doc("labs", lab_id))
    batch.delete(doc("users", username))
    batch.commit()
    return {"message": "Admin deleted successfully."}


@app.post("/login")
def login(user: Faculty, request: Request, response: Response):
    client_key = request.client.host if request.client else "unknown"
    now = datetime.now(timezone.utc).timestamp()
    recent = [stamp for stamp in login_attempts.get(client_key, []) if now - stamp < LOGIN_ATTEMPT_WINDOW]
    if len(recent) >= LOGIN_ATTEMPT_LIMIT:
        raise HTTPException(429, "Too many login attempts. Try again in one minute.")
    login_attempts[client_key] = recent + [now]
    snapshot = doc("users", user.username).get()
    data = snapshot.to_dict() if snapshot.exists else None
    stored_hash = BOOTSTRAP_PASSWORD_HASH if user.username == BOOTSTRAP_USERNAME else data.get("password", "") if data else ""
    if not data or not stored_hash or not verify_password(user.password, stored_hash):
        raise HTTPException(401, "Invalid username or password.")
    set_session_cookie(response, user.username)
    login_attempts.pop(client_key, None)
    return {"message": f"{user.username} has been successfully logged in.", "user": public_user(data)}


@app.post("/logout")
def logout(response: Response):
    clear_session_cookie(response)
    return {"message": "Logged out successfully."}


@app.get("/me")
def current_user(user=Depends(authenticated_user)):
    return {"user": public_user(user)}


@app.put("/faculty/{username}/password")
def update_password(username: str, password_data: PasswordUpdate, user=Depends(require_admin)):
    if username == BOOTSTRAP_USERNAME:
        raise HTTPException(400, "The super admin password is managed by the environment configuration.")
    if user["role"] != "SUPER_ADMIN" and user["username"] != username:
        raise HTTPException(403, "You can only update your own password.")
    validate_password_strength(password_data.new_password)
    reference = doc("users", username)
    snapshot = reference.get()
    if not snapshot.exists:
        raise HTTPException(404, "Faculty not found.")
    if not verify_password(password_data.old_password, snapshot.to_dict().get("password", "")):
        raise HTTPException(401, "Old password is incorrect.")
    reference.update({"password": hash_password(password_data.new_password)})
    return {"message": "Password successfully updated."}


@app.post("/problems")
def create_problem(problem: Problem, user=Depends(require_admin)):
    if user.get("role") != "SUPER_ADMIN" and user.get("username") != problem.username:
        raise HTTPException(403, "You can only create problems for your own account.")
    faculty = doc("users", problem.username).get()
    if not faculty.exists:
        raise HTTPException(404, "Faculty username does not exist.")
    if user.get("role") != "SUPER_ADMIN" and faculty.to_dict().get("lab_id") != user.get("lab_id"):
        raise HTTPException(403, "You cannot manage another lab's problems.")
    reference = db.collection("problems").document()
    reference.set(problem.model_dump())
    return {"message": "Problem successfully created.", "problem_id": reference.id}


@app.get("/problems/{username}")
def get_problems_by_faculty(username: str, user=Depends(require_admin)):
    if user.get("role") != "SUPER_ADMIN" and user.get("username") != username:
        raise HTTPException(403, "You can only view your own problems.")
    problems = [problem_json(item) for item in db.collection("problems").where(filter=FieldFilter("username", "==", username)).stream()]
    return {"username": username, "problems": problems}


@app.get("/problems")
def get_all_problems(_admin=Depends(require_super_admin)):
    return {"problems": [problem_json(item) for item in db.collection("problems").stream()]}


@app.put("/problems/{problem_id}")
def update_problem(problem_id: str, problem: Problem, user=Depends(require_admin)):
    reference = doc("problems", problem_id)
    snapshot = reference.get()
    if not snapshot.exists:
        raise HTTPException(404, "Problem not found.")
    existing_username = snapshot.to_dict().get("username")
    if user.get("role") != "SUPER_ADMIN" and (user.get("username") != existing_username or user.get("username") != problem.username):
        raise HTTPException(403, "You can only update your own problems.")
    faculty = doc("users", problem.username).get()
    if not faculty.exists:
        raise HTTPException(404, "Faculty username does not exist.")
    if user.get("role") != "SUPER_ADMIN" and faculty.to_dict().get("lab_id") != user.get("lab_id"):
        raise HTTPException(403, "You cannot move a problem to another lab.")
    reference.set(problem.model_dump())
    return {"message": "Problem successfully updated.", "problem_id": problem_id}


@app.delete("/problems/{problem_id}")
def delete_problem(problem_id: str, user=Depends(require_admin)):
    reference = doc("problems", problem_id)
    snapshot = reference.get()
    if not snapshot.exists:
        raise HTTPException(404, "Problem not found.")
    if user.get("role") != "SUPER_ADMIN" and snapshot.to_dict().get("username") != user.get("username"):
        raise HTTPException(403, "You can only delete your own problems.")
    reference.delete()
    return {"message": "Problem successfully deleted.", "problem_id": problem_id}
