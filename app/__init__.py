"""Inicialización principal de la aplicación Flask."""

from flask import Flask
from .extensions import db
from .routes.client_routes import client_routes
from .routes.admin_routes import admin_routes
from .routes.auth_routes import auth_routes
from datetime import timedelta
import os
from dotenv import load_dotenv

from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

load_dotenv()

def create_app():
    """Crea y configura la aplicación Flask."""
    app = Flask(__name__, template_folder="templates", instance_relative_config=True)

    # Configuración básica
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/presupuestos.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.getenv("FLASK_SECRET_KEY")
    app.permanent_session_lifetime = timedelta(hours=1)

    # Inicialización de extensiones
    db.init_app(app)

    # Activar foreign keys en SQLite
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, sqlite3.Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()

    # Registro de blueprints
    app.register_blueprint(auth_routes)
    app.register_blueprint(client_routes)
    app.register_blueprint(admin_routes)

    # Creación de tablas
    with app.app_context():
        from . import models
        db.create_all()

    return app
