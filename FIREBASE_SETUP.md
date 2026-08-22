# TCT Firebase Deployment Guide

This project uses Firestore through the FastAPI backend. The browser never
connects directly to Firestore and never receives a service-account key.
FastAPI uses Firebase Admin SDK, Argon2 password hashes, and an HttpOnly
session cookie.

## 1. Firebase project

1. Create a Firebase project at https://console.firebase.google.com.
2. Create a Firestore database in production mode and choose its region.
3. Enable billing if required by your selected Firestore plan.
4. Create a dedicated service account with the minimum Firestore access needed
   by the API. Download its JSON key as `backend/firebase-service-account.json`.
5. Install the Firebase CLI, then authenticate and select the project:

```powershell
npm install -g firebase-tools
firebase login
firebase use --add
```

Do not commit the service-account JSON or any `.env` file.

## 2. Backend configuration

From the repository root:

```powershell
Copy-Item backend\.env.example backend\.env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

Edit `backend/.env`:

```env
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_SERVICE_ACCOUNT_JSON=./firebase-service-account.json
TCT_SESSION_SECRET=use-a-long-random-secret
TCT_BOOTSTRAP_USERNAME=@vivekshukla26
TCT_BOOTSTRAP_PASSWORD_HASH=your-argon2-hash
TCT_SESSION_MAX_AGE=28800
TCT_SECURE_COOKIE=true
TCT_COOKIE_SAMESITE=lax
TCT_CORS_ORIGINS=https://your-frontend-domain.web.app
```

Generate a session secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Generate an Argon2 hash using the project environment:

```powershell
python -c "from pwdlib import PasswordHash; print(PasswordHash.recommended().hash('ChangeThisStrongPassword1'))"
```

Replace the example password immediately. The bootstrap hash is stored in an
environment variable and is never returned to the frontend.

## 3. Migrate existing SQLite data

Keep a backup of `backend/my_database.db` before migration. Run this once from
`backend`:

```powershell
cd backend
python migrate_sqlite_to_firestore.py --sqlite my_database.db
```

The migration is repeatable: document IDs are preserved, so rerunning it
updates the same Firestore documents instead of creating duplicates. Verify
login, labs, links, admin creation, password update, and problem CRUD in a
staging deployment before removing the SQLite backup.

## 4. Deploy Firestore rules

From the repository root:

```powershell
firebase deploy --only firestore:rules,firestore:indexes
```

The rules intentionally deny all browser access:

```javascript
match /{document=**} {
  allow read, write: if false;
}
```

This is correct for the current architecture because Firebase Admin SDK calls
from FastAPI bypass client rules. Authorization is enforced by FastAPI's
session and role dependencies. Never put the service-account key in `frontend`.

## 5. Render deployment

Deploy the backend and frontend as separate Render services. This repository
includes `render.yaml` for a Python FastAPI web service and a Vite static site.

Backend service settings:

```text
Root directory: backend
Build command: pip install -r requirements.txt
Start command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Backend environment variables:

```text
FIREBASE_PROJECT_ID=tctlab
FIREBASE_SERVICE_ACCOUNT_JSON=<complete service-account JSON>
TCT_SESSION_SECRET=<long random secret>
TCT_BOOTSTRAP_USERNAME=@vivekshukla26
TCT_BOOTSTRAP_PASSWORD_HASH=<Argon2 hash>
TCT_SESSION_MAX_AGE=28800
TCT_SECURE_COOKIE=true
TCT_COOKIE_SAMESITE=none
TCT_CORS_ORIGINS=https://<your-frontend-service>.onrender.com
```

Frontend static site settings:

```text
Root directory: frontend
Build command: npm ci && npm run build
Publish directory: dist
```

Frontend environment variables:

```text
VITE_API_BASE_URL=https://<your-backend-service>.onrender.com
VITE_API_TIMEOUT_MS=10000
```

`FIREBASE_SERVICE_ACCOUNT_JSON` is parsed as JSON by the backend. Paste the
complete downloaded service-account JSON into the Render backend environment;
never put it in Git or in a `VITE_*` variable. `TCT_CORS_ORIGINS` must be the
exact final frontend URL. Do not use `*` because the app authenticates with an
HttpOnly credentialed cookie. Use `TCT_COOKIE_SAMESITE=none` with
`TCT_SECURE_COOKIE=true` when the frontend and backend are on different HTTPS
origins, such as separate Render services.

Password changes use the authenticated username and current password. Normal
admin password hashes are stored in Firestore and replaced after the old
password is verified. The super-admin hash is read only from
`TCT_BOOTSTRAP_PASSWORD_HASH`; the super-admin password cannot be changed from
the UI. Update that environment variable and redeploy when it must change.

After both services deploy, verify:

```text
https://<your-frontend-service>.onrender.com/
https://<your-backend-service>.onrender.com/
```

The second URL should return `{"message":"TCT Lab Portal Backend is running"}`.

## 6. Run or deploy the backend

For a local smoke test:

```powershell
cd backend
. ..\.venv\Scripts\Activate.ps1
uvicorn main:app --host 127.0.0.1 --port 8000
```

For Render production, the backend must listen on `0.0.0.0` and use Render's
dynamic `$PORT`. Configure all values from `backend/.env` as platform
secrets/environment variables and expose the API through HTTPS. Set
`TCT_CORS_ORIGINS` to the exact deployed frontend URL.

The backend must have:

- Python 3.10 or newer
- `pip install -r requirements.txt`
- `FIREBASE_PROJECT_ID`
- `FIREBASE_SERVICE_ACCOUNT_JSON`
- `TCT_SESSION_SECRET`
- `TCT_CORS_ORIGINS`
- `TCT_SECURE_COOKIE=true`
- `TCT_COOKIE_SAMESITE=none` for separate frontend/backend HTTPS origins

## 7. Deploy the frontend separately

Set the production API URL in `frontend/.env.production`:

```env
VITE_API_BASE_URL=https://your-api-domain.example
VITE_API_TIMEOUT_MS=10000
```

Build the frontend:

```powershell
cd frontend
npm ci
npm run build
```

The generated `frontend/dist` directory is what Render serves. The `render.yaml`
static-site route rewrites client-side routes to `/index.html`, so React Router
paths such as `/admin/login` and `/lab/:labId` work after refresh.

The Firebase Hosting config is retained for Firestore project artifacts and as
an optional static-hosting fallback. For Firebase Hosting, initialize Hosting
once, choose `frontend/dist` as the public directory, and configure it as a
single-page app:

```powershell
firebase init hosting
firebase deploy --only hosting
```

After deployment, update `TCT_CORS_ORIGINS` with the final hosting URL and
restart the backend.

## 8. Production verification

Check these flows over HTTPS:

1. Open the frontend and confirm public labs and links load.
2. Log in with the bootstrap admin and confirm `/me` succeeds.
3. Create and delete a test link.
4. Create a test admin and confirm the new lab appears.
5. Verify a normal admin cannot access super-admin operations.
6. Verify logout removes the session and direct Firestore browser access fails.
7. Confirm browser developer tools contain no service-account credentials.

## Cleanup after verification

Do not delete `backend/my_database.db` until the migration and rollback window
is over. After a verified backup, it is no longer used at runtime and may be
archived or removed. Keep `migrate_sqlite_to_firestore.py` for disaster recovery
or future data imports.

The repository intentionally keeps these Firebase deployment artifacts:
`firebase.json`, `firestore.rules`, and `firestore.indexes.json`.
