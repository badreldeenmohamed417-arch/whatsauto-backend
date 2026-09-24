import sys
import os

# Add the app directory to the system path
sys.path.insert(0, os.path.dirname(__file__))

from app.main import app as fastapi_app
from a2wsgi import ASGIMiddleware

# Hostinger uses Passenger which requires a WSGI application named "application"
application = ASGIMiddleware(fastapi_app)
