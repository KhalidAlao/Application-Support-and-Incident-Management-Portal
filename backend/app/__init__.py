from flask import Flask
from flask_cors import CORS
import os

from backend.config import DevelopmentConfig, TestingConfig, ProductionConfig
from backend.extensions import db, jwt, swagger, migrate
from backend.app.routes import health_bp, auth_bp, incidents_bp, applications_bp, knowledge_bp, reports_bp

def create_app(config_class=None):
    if config_class is None:
        config_class = DevelopmentConfig

    if config_class is ProductionConfig and not config_class.SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL must be set when using ProductionConfig")

    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app)
    swagger.init_app(app)
    migrate.init_app(app, db)

    # Import models to register with db.metadata
    from backend.app import models  # noqa: F401

    from backend.app.routes import health_bp, auth_bp, incidents_bp, applications_bp
    # Register blueprints
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(auth_bp)
    app.register_blueprint(incidents_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(knowledge_bp)
    app.register_blueprint(reports_bp)

    return app