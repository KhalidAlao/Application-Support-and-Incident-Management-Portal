from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from backend.extensions import db, jwt, swagger, migrate


# absolute imports using the 'backend' package root
from backend.config import DevelopmentConfig, TestingConfig, ProductionConfig
from backend.extensions import db, jwt, swagger

def create_app(config_class=None):
    if config_class is None:
        config_class = DevelopmentConfig

    # Validation fires ONLY when ProductionConfig is actually used
    if config_class is ProductionConfig and not config_class.SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL must be set when using ProductionConfig")

    app = Flask(__name__)
    app.config.from_object(config_class)
    

    # Init extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)
    swagger.init_app(app)
    migrate.init_app(app, db) 
    
    with app.app_context():
        from backend.app import models  # noqa: F401 — triggers model registration with db.metadata

    # Register blueprints
    from backend.app.routes.health import health_bp
    app.register_blueprint(health_bp, url_prefix='/api')

    return app