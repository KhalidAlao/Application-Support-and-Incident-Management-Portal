from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flasgger import Swagger

db = SQLAlchemy()
jwt = JWTManager()
swagger = Swagger()