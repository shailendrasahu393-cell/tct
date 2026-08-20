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

## 5. Netlify deployment

This repository includes `netlify.toml` and a Netlify Function wrapper for the
FastAPI app. Netlify serves the Vite build and proxies `/api/*` to that
function, so the frontend uses the same-origin `/api` URL automatically.

1. Push this repository to GitHub and import it into Netlify.
2. Netlify will read `netlify.toml`; no manual build command is required.
3. Add these variables under Netlify Site configuration > Environment variables
  > Production:

```text
FIREBASE_PROJECT_ID=tctlab
FIREBASE_SERVICE_ACCOUNT_JSON=<complete service-account JSON>
TCT_SESSION_SECRET=<long random secret>
TCT_BOOTSTRAP_USERNAME=@vivekshukla26
TCT_BOOTSTRAP_EMAIL=admin@example.com
TCT_BOOTSTRAP_PASSWORD_HASH=<Argon2 hash>
TCT_SESSION_MAX_AGE=28800
TCT_SECURE_COOKIE=true
TCT_CORS_ORIGINS=https://<your-site>.netlify.app
TCT_FRONTEND_URL=https://<your-site>.netlify.app
RESEND_API_KEY=<Resend API key>
EMAIL_FROM=TCT Lab <noreply@your-domain.example>
```

`FIREBASE_SERVICE_ACCOUNT_JSON` is parsed as JSON by the function. Paste the
complete downloaded service-account JSON into the Netlify variable; never put
it in Git or in a `VITE_*` variable. `TCT_CORS_ORIGINS` must be the exact final
Netlify URL. No `VITE_API_BASE_URL` is needed because `/api` is same-origin.

Password recovery uses Resend. Verify your sending domain in Resend, then set
`RESEND_API_KEY` and a verified `EMAIL_FROM`. New admins must have a recovery
email. Existing Firestore users need an `email` field before they can use
forgot-password recovery; otherwise they can still change their password while
logged in.

4. Trigger a deploy. Then verify:

```text
https://<your-site>.netlify.app/
https://<your-site>.netlify.app/api/
```

The second URL should return `{"message":"TCT Lab Portal Backend is running"}`.

## 6. Run or deploy the backend

For a local smoke test:

```powershell
cd backend
. ..\.venv\Scripts\Activate.ps1
uvicorn main:app --host 127.0.0.1 --port 8000
```

For production, deploy the `backend` directory to a Python host that supports
FastAPI (Cloud Run, Render, Railway, or an equivalent service). Configure all
values from `backend/.env` as platform secrets/environment variables, upload
the service-account JSON through the platform secret manager, and expose the
API through HTTPS. Set `TCT_CORS_ORIGINS` to the exact deployed frontend URL.

The backend must have:

- Python 3.10 or newer
- `pip install -r requirements.txt`
- `FIREBASE_PROJECT_ID`
- `FIREBASE_SERVICE_ACCOUNT_JSON`
- `TCT_SESSION_SECRET`
- `TCT_CORS_ORIGINS`
- `TCT_SECURE_COOKIE=true`

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

The generated `frontend/dist` directory can be deployed to Firebase Hosting or
any static HTTPS host. For Firebase Hosting, initialize Hosting once, choose
`frontend/dist` as the public directory, and configure it as a single-page app:

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

The repository intentionally keeps only these Firebase deployment artifacts:
`firebase.json`, `firestore.rules`, and `firestore.indexes.json`.

Netlify Functions are serverless. For heavy or long-running backend traffic,
Cloud Run remains the better FastAPI host; the Netlify setup above is suitable
for this portal's normal CRUD and authentication traffic.
