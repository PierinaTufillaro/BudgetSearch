"""Rutas de autenticación para clientes y administradores."""

from flask import Blueprint, request, render_template, redirect, url_for, session
from app.models import Material, Credenciales, Montado, Monto
from datetime import datetime, timezone
from werkzeug.security import check_password_hash


auth_routes = Blueprint("auth", __name__)


@auth_routes.route("/", methods=["GET", "POST"])
def client_login():
    """
    Maneja el login del cliente solo con contraseña.

    - En POST verifica la contraseña contra el usuario 'cliente' en la base.
    - Si es correcta, inicia sesión y muestra la página principal de cliente.
    - Si es incorrecta, vuelve a mostrar el login con error.
    - En GET simplemente muestra el formulario de login.
    """
    if request.method == "POST":
        clave = request.form.get("contrasena", "").strip()
        cred = Credenciales.query.filter_by(usuario="client").first()
        if cred and check_password_hash(cred.contrasena, clave):
            session.permanent = True
            session["user_type"] = "client"
            session["login_time"] = datetime.now(timezone.utc).isoformat()
            
            materiales = Material.query.all()
            materiales_montados = {}
            materiales_laminado = {}
            
            for mat in materiales:
                montajes = (
                    Montado.query
                    .join(Monto, Montado.monto_id == Monto.id)
                    .filter(Monto.material_id == mat.id)
                    .all()
                )
                
                # Crear diccionario para evitar duplicados por nombre
                montados_unicos = {}
                for m in montajes:
                    nombre = m.nombre_material_montaje
                    if nombre not in montados_unicos:
                        montados_unicos[nombre] = {
                            "id": m.id,
                            "nombre": nombre,
                            "monto": m.monto_montado,
                        }
                
                materiales_montados[str(mat.id)] = list(montados_unicos.values())
                
                # Verificar si hay laminado disponible para este material
                from app.models import Laminado
                montos_con_laminado = (
                    Monto.query
                    .join(Laminado, Monto.id == Laminado.monto_id)
                    .filter(Monto.material_id == mat.id)
                    .all()
                )
                materiales_laminado[str(mat.id)] = len(montos_con_laminado) > 0
            
            return render_template(
                "client_index.html",
                materiales=materiales,
                materiales_montados=materiales_montados,
                materiales_laminado=materiales_laminado,
            )
        return render_template("client_login.html", error="Contraseña incorrecta")
    return render_template("client_login.html")


@auth_routes.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        cred = Credenciales.query.filter_by(usuario=username).first()
        if cred and check_password_hash(cred.contrasena, password):
            session.permanent = True
            session["user_type"] = "admin"
            session["login_time"] = datetime.now(timezone.utc).isoformat()
            return redirect(url_for("admin.admin_panel"))
        else:
            return render_template(
                "admin_login.html", error="Usuario o contraseña incorrectos"
            )

    return render_template("admin_login.html")


@auth_routes.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.client_login"))
