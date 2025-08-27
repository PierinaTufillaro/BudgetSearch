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
            # Verificar si existe la sesión
            if 'user_type' not in session:
                return redirect(url_for(f'auth.{role}_login'))

            # Verificar si el rol coincide
            if session['user_type'] != role:
                session.clear()
                flash('No tienes permisos para acceder a esta página.', 'danger')
                return redirect(url_for(f'auth.{role}_login'))

            # Verificar expiración de sesión
            if 'login_time' in session:
                try:
                    now = datetime.utcnow()
                    login_time = datetime.fromisoformat(session['login_time'])
                    session_lifetime = app.permanent_session_lifetime
                    
                    if now - login_time > session_lifetime:
                        session.clear()
                        flash(f'Sesión expirada después de {session_lifetime.total_seconds() / 3600:.1f} horas. Por favor, inicia sesión nuevamente.', 'warning')
                        return redirect(url_for(f'auth.{role}_login'))
                except (ValueError, TypeError):
                    # Si hay error en el formato de fecha, limpiar sesión
                    session.clear()
                    flash('Error en la sesión. Por favor, inicia sesión nuevamente.', 'danger')
                    return redirect(url_for(f'auth.{role}_login'))

            return f(*args, **kwargs)
        return wrapped
    return decorator


def cleanup_expired_sessions():
    """Función para limpiar sesiones expiradas (puede ser llamada periódicamente)"""
    # Esta función puede ser llamada por un cron job o scheduler
    # Por ahora, la limpieza se hace en cada request a través del decorator
    pass


def get_session_remaining_time():
    """Obtiene el tiempo restante de la sesión actual en formato legible"""
    if 'login_time' not in session:
        return None
    
    try:
        now = datetime.utcnow()
        login_time = datetime.fromisoformat(session['login_time'])
        session_lifetime = app.permanent_session_lifetime
        remaining = session_lifetime - (now - login_time)
        
        if remaining.total_seconds() <= 0:
            return "Expirada"
        
        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except (ValueError, TypeError):
        return "Error"

