"""Extensiones globales para la aplicación Flask."""

from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet
import os

# Cargamos dotenv acá, ya que fernet depende de variables de entorno
from dotenv import load_dotenv
load_dotenv()

db = SQLAlchemy()

# Instancia global de Fernet
fernet = Fernet(os.getenv("ENCRYPTION_KEY").encode())
