# Render Setup Guide

This repository is ready for Render with two services:

- `tct-backend`: FastAPI backend from `backend`
- `tct-frontend`: Vite React static site from `frontend`

The browser talks only to the FastAPI backend. Firebase Admin credentials stay
on the backend service and must never be added to any `VITE_*` variable.

## 1. Before Deploying

Confirm these files are present:

```text
render.yaml
backend/main.py
backend/firebase_app.py
backend/requirements.txt
frontend/package.json
frontend/package-lock.json
```

Generate or prepare these secret values:

```text
FIREBASE_PROJECT_ID
FIREBASE_SERVICE_ACCOUNT_JSON
TCT_SESSION_SECRET
TCT_BOOTSTRAP_USERNAME
TCT_BOOTSTRAP_PASSWORD_HASH
```

Useful local commands:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "from pwdlib import PasswordHash; print(PasswordHash.recommended().hash('ChangeThisStrongPassword1'))"
```

Replace `ChangeThisStrongPassword1` with the real bootstrap admin password
before generating the Argon2 hash.

## 2. Create Render Blueprint

1. Push this repository to GitHub.
2. In Render, choose **New > Blueprint**.
3. Select this repository.
4. Render will read `render.yaml` and create both services.
5. Enter all `sync: false` environment variables when prompted.

The backend service uses:

```text
Root directory: backend
Build command: pip install -r requirements.txt
Start command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

The frontend static site uses:

```text
Root directory: frontend
Build command: npm ci && npm run build
Publish directory: dist
```

## 3. Backend Environment Variables

Set these on the Render backend service:

```text
FIREBASE_PROJECT_ID=tctlab
FIREBASE_SERVICE_ACCOUNT_JSON=<complete Firebase service-account JSON>
TCT_SESSION_SECRET=<long random secret>
TCT_BOOTSTRAP_USERNAME=@vivekshukla26
TCT_BOOTSTRAP_PASSWORD_HASH=<Argon2 password hash>
TCT_SESSION_MAX_AGE=28800
TCT_SECURE_COOKIE=true
TCT_COOKIE_SAMESITE=none
TCT_CORS_ORIGINS=https://<your-frontend-service>.onrender.com
```

Important:

- Paste the complete Firebase service-account JSON into
  `FIREBASE_SERVICE_ACCOUNT_JSON`.
- Do not use `*` for `TCT_CORS_ORIGINS`.
- Use `TCT_COOKIE_SAMESITE=none` with `TCT_SECURE_COOKIE=true` because the
  frontend and backend are on different Render origins.

## 4. Frontend Environment Variables

Set these on the Render frontend static site:

```text
VITE_API_BASE_URL=https://<your-backend-service>.onrender.com
VITE_API_TIMEOUT_MS=10000
```

After changing `VITE_API_BASE_URL`, redeploy the frontend. Vite reads this value
at build time and bakes it into the generated assets.

## 5. First Deploy Order

1. Deploy the Blueprint once.
2. Copy the final backend URL from Render.
3. Set frontend `VITE_API_BASE_URL` to the backend URL.
4. Copy the final frontend URL from Render.
5. Set backend `TCT_CORS_ORIGINS` to the frontend URL.
6. Redeploy backend.
7. Redeploy frontend with clear build cache.

## 6. Smoke Test

Open these URLs:

```text
https://<your-backend-service>.onrender.com/
https://<your-frontend-service>.onrender.com/
```

The backend root should return:

```json
{"message":"TCT Lab Portal Backend is running"}
```

Then verify:

1. Public labs and links load.
2. Bootstrap admin login works.
3. `/me` succeeds after login.
4. Create and delete a test link.
5. Logout removes the session.

## 7. Troubleshooting

If login succeeds but the app acts logged out:

- Check `TCT_CORS_ORIGINS` exactly matches the frontend origin.
- Check `TCT_COOKIE_SAMESITE=none`.
- Check `TCT_SECURE_COOKIE=true`.
- Check the frontend uses `withCredentials: true`.

If the frontend still calls the wrong backend:

- Update `VITE_API_BASE_URL` on the frontend service.
- Redeploy the frontend with clear build cache.

If Firebase fails at startup:

- Confirm `FIREBASE_PROJECT_ID` matches the Firebase project.
- Confirm `FIREBASE_SERVICE_ACCOUNT_JSON` is complete valid JSON.
- Confirm the service account has Firestore access.

## References

- Render Blueprint spec: https://render.com/docs/blueprint-spec
- Render monorepo support: https://render.com/docs/monorepo-support
- Render static site guide: https://render.com/tutorials/web-service-vs-static-site/static-sites
