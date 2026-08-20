import os
import secrets
import json
from datetime import datetime, timezone
from typing import Any

import firebase_admin
from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import FieldFilter
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pwdlib import PasswordHash
from pydantic import BaseModel


def _firebase_client():
    if not firebase_admin._apps:
        credential_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        options = {"projectId": os.getenv("FIREBASE_PROJECT_ID")}
        if credential_path and os.path.isfile(credential_path):
            credential = credentials.Certificate(credential_path)
        elif credential_path:
            credential = credentials.Certificate(json.loads(credential_path))
        else:
            credential = credentials.ApplicationDefault()
        firebase_admin.initialize_app(credential, options)
    return firestore.client()


db = _firebase_client()
app = FastAPI(title="TCT Lab Portal Backend")
cors_origins = [origin.strip() for origin in os.getenv("TCT_CORS_ORIGINS", "").split(",") if origin.strip()]
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


class AdminCreate(BaseModel):
    username: str
    name: str
    password: str
    lab_name: str
    class_name: str


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


def hash_password(value: str) -> str:
    return password_hash.hash(value)


def verify_password(value: str, hashed: str) -> bool:
    try:
        return password_hash.verify(value, hashed)
    except Exception:
        return False


def doc(collection: str, key: str):
    return db.collection(collection).document(key)


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
def delete_lab(lab_id: str, user=Depends(require_admin)):
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
    if not doc("labs", link.lab_id).get().exists:
        raise HTTPException(404, "Lab not found.")
    reference = db.collection("links").document()
    reference.set(link.model_dump())
    return link_json(reference.get())


@app.put("/links/{link_id}")
def update_link(link_id: str, link: Link, user=Depends(require_admin)):
    reference = doc("links", link_id)
    if not reference.get().exists:
        raise HTTPException(404, "Link not found.")
    reference.set(link.model_dump())
    return link_json(reference.get())


@app.delete("/links/{link_id}")
def delete_link(link_id: str, user=Depends(require_admin)):
    reference = doc("links", link_id)
    if not reference.get().exists:
        raise HTTPException(404, "Link not found.")
    reference.delete()
    return {"message": "Link successfully deleted."}


@app.post("/admin")
def create_admin(admin: AdminCreate, response: Response, _super_admin=Depends(require_super_admin)):
    username = admin.username.strip()
    if not username.startswith("@"):
        raise HTTPException(422, "User ID must start with @.")
    if len(admin.password) < 8 or not any(c.isupper() for c in admin.password) or not any(c.islower() for c in admin.password) or not any(c.isdigit() for c in admin.password):
        raise HTTPException(422, "Password must be at least 8 characters with uppercase, lowercase, and a number.")
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
    response.set_cookie(SESSION_COOKIE, serializer.dumps(user.username), max_age=SESSION_MAX_AGE, httponly=True, secure=SECURE_COOKIE, samesite="lax")
    login_attempts.pop(client_key, None)
    return {"message": f"{user.username} has been successfully logged in.", "user": public_user(data)}


@app.post("/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE)
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
    reference = doc("users", username)
    snapshot = reference.get()
    if not snapshot.exists:
        raise HTTPException(404, "Faculty not found.")
    if not verify_password(password_data.old_password, snapshot.to_dict().get("password", "")):
        raise HTTPException(401, "Old password is incorrect.")
    reference.update({"password": hash_password(password_data.new_password)})
    return {"message": "Password successfully updated."}


@app.post("/problems")
def create_problem(problem: Problem, _admin=Depends(require_admin)):
    if not doc("users", problem.username).get().exists:
        raise HTTPException(404, "Faculty username does not exist.")
    reference = db.collection("problems").document()
    reference.set(problem.model_dump())
    return {"message": "Problem successfully created.", "problem_id": reference.id}


@app.get("/problems/{username}")
def get_problems_by_faculty(username: str, _admin=Depends(require_admin)):
    problems = [problem_json(item) for item in db.collection("problems").where(filter=FieldFilter("username", "==", username)).stream()]
    return {"username": username, "problems": problems}


@app.get("/problems")
def get_all_problems(_admin=Depends(require_admin)):
    return {"problems": [problem_json(item) for item in db.collection("problems").stream()]}


@app.put("/problems/{problem_id}")
def update_problem(problem_id: str, problem: Problem, _admin=Depends(require_admin)):
    reference = doc("problems", problem_id)
    if not reference.get().exists:
        raise HTTPException(404, "Problem not found.")
    if not doc("users", problem.username).get().exists:
        raise HTTPException(404, "Faculty username does not exist.")
    reference.set(problem.model_dump())
    return {"message": "Problem successfully updated.", "problem_id": problem_id}


@app.delete("/problems/{problem_id}")
def delete_problem(problem_id: str, _admin=Depends(require_admin)):
    reference = doc("problems", problem_id)
    if not reference.get().exists:
        raise HTTPException(404, "Problem not found.")
    reference.delete()
    return {"message": "Problem successfully deleted.", "problem_id": problem_id}
