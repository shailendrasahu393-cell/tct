from mangum import Mangum

from backend.firebase_app import app

handler = Mangum(app)