"""Rutas de autenticación para clientes y administradores."""

from flask import Blueprint, request, render_template, redirect, url_for, session
from app.models import Material, Credenciales, MaterialMontado
from datetime import datetime
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
            session["login_time"] = datetime.utcnow().isoformat()
            materiales = Material.query.all()
            materiales_montados = {}
            for mat in materiales:
                montajes = MaterialMontado.query.filter_by(material_id=mat.id).all()
                materiales_montados[str(mat.id)] = [
                    {
                        "id": m.id,
                        "nombre": m.nombre,
                        "porcentaje": m.porcentaje_por_montado,
                    }
                    for m in montajes
                ]
            return render_template(
                "client_index.html",
                materiales=materiales,
                materiales_montados=materiales_montados,
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
            session["login_time"] = datetime.utcnow().isoformat()
            return redirect(url_for("admin.admin_panel"))
        else:
            return render_template(
                "admin_login.html", error="Usuario o contraseña incorrectos"
            )

    return render_template("admin_login.html")


@auth_routes.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("client_login"))
