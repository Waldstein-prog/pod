import os
import sys

project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ.setdefault("SESSION_COOKIE_SECURE", "1")

from db import init_db
from app import app as application

init_db()
