from flask import Flask, redirect, send_from_directory
from flask_cors import CORS
import os

from backend.config import DevelopmentConfig, TestingConfig, ProductionConfig
from backend.extensions import db, jwt, swagger, migrate
from backend.seed import seed_db

def create_app(config_class=None):
    if config_class is None:
        config_class = DevelopmentConfig

    if config_class is ProductionConfig and not config_class.SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL must be set when using ProductionConfig")

    # Static folder for frontend assets (CSS, JS)
    app = Flask(
        __name__,
        static_folder='../../frontend/static',
        static_url_path='/static'
    )
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app)
    swagger.init_app(app)
    migrate.init_app(app, db)

    from backend.app import models  # noqa: F401

    # Register API blueprints
    from backend.app.routes import (
        health_bp, auth_bp, incidents_bp,
        applications_bp, knowledge_bp, reports_bp, users_bp
    )
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(auth_bp)
    app.register_blueprint(incidents_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(knowledge_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(users_bp)

    # Path to the frontend/ folder (repo root)
    frontend_dir = os.path.join(app.root_path, '..', '..', 'frontend')
    print(f"Serving frontend from: {frontend_dir}")

    # Root route
    @app.route('/')
    def index():
        return redirect('/login.html')

    # Frontend HTML routes
    @app.route('/login.html')
    def login_page():
        return send_from_directory(frontend_dir, 'login.html')

    @app.route('/dashboard.html')
    def dashboard_page():
        return send_from_directory(frontend_dir, 'dashboard.html')

    @app.route('/incident-detail.html')
    def incident_detail_page():
        return send_from_directory(frontend_dir, 'incident-detail.html')

    # Register CLI commands
    app.cli.add_command(seed_db)

    return app