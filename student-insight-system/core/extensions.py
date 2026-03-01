"""
Centralised Flask extension instances.

Every extension is created here *without* an app, then bound later
inside the application factory via ``init_app()``.

Import from here — never instantiate extensions elsewhere:
    from core.extensions import db, jwt, migrate, cors
"""

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
cors = CORS()
