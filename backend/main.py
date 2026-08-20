"""Production entrypoint for the Firebase-backed API."""

from firebase_app import app

__all__ = ["app"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
