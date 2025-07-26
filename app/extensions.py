"""Extensiones globales para la aplicación Flask."""

from flask_sqlalchemy import SQLAlchemy
import os

from dotenv import load_dotenv
load_dotenv()

db = SQLAlchemy()


