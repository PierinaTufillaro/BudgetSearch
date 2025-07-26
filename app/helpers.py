"""Funciones auxiliares para encriptación y sesión."""

from flask import session, redirect, url_for, flash, current_app as app
from functools import wraps
from datetime import datetime
import os


def login_required(role):
    """Protege rutas según el rol de usuario y controla expiración de sesión."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'user_type' not in session:
                # Siempre manda al login del rol requerido
                return redirect(url_for(f'auth.{role}_login'))

            if session.get('user_type') != role:
                session.clear()
                flash('Por favor, iniciá sesión correctamente.', 'danger')
                return redirect(url_for(f'auth.{role}_login'))

            if 'login_time' in session:
                now = datetime.utcnow()
                login_time = datetime.fromisoformat(session['login_time'])
                if now - login_time > app.permanent_session_lifetime:
                    session.clear()
                    flash('Sesión expirada, por favor logueate de nuevo.', 'warning')
                    return redirect(url_for(f'auth.{role}_login'))

            return f(*args, **kwargs)
        return wrapped
    return decorator

