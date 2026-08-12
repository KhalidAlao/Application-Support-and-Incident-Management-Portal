from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from flask_migrate import Migrate

db = SQLAlchemy()
jwt = JWTManager()
swagger = Swagger()
migrate = Migrate()

from backend.app.models import User, Priority, Application