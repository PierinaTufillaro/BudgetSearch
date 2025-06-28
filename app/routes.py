from flask import render_template, request, redirect, url_for
from . import db
from .models import Budget

# Usa current_app si necesitás app
from flask import current_app as app

logged_in = False
USER = "admin"
PASS = "admin123"
pwd = "mi_contraseña_segura"
MATERIALES = ["Madera", "Metal", "Plástico", "Vidrio"]

logged_in = False

@app.route("/", methods=["GET", "POST"])
def client_login():
    if request.method == "POST":
        clave = request.form.get("password", "")
        if clave == pwd:
            return render_template("client_index.html", materiales=MATERIALES)
        else:
            error = "Contraseña incorrecta"
            return render_template("client_login.html", error=error)
    return render_template("client_login.html", error=None)

@app.route("/client_index")
def client_index():
    return render_template("client_index.html")

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    global logged_in
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == USER and password == PASS:
            logged_in = True
            return redirect(url_for("admin_panel"))
        else:
            error = "Usuario o contraseña incorrectos"
    return render_template("admin_login.html", error=error)

@app.route("/logout")
def admin_logout():
    global logged_in
    logged_in = False
    return redirect(url_for("client_login"))

@app.route("/admin_panel", methods=["GET", "POST"])
def admin_panel():
    global logged_in
    if not logged_in:
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        material = request.form["material"]
        monto = float(request.form["monto"])

        altos = request.form.getlist("medida_alto[]")
        anchos = request.form.getlist("medida_ancho[]")
        descuentos = request.form.getlist("descuento[]")

        for alto, ancho, descuento in zip(altos, anchos, descuentos):
            budget = Budget(
                medida_alto=float(alto),
                medida_ancho=float(ancho),
                descuento=float(descuento),
                material=material,
                monto=monto
            )
            db.session.add(budget)
        db.session.commit()
        return redirect(url_for("admin_panel"))

    budgets = Budget.query.all()
    return render_template("admin_panel.html", budgets=budgets, login=logged_in, materiales=MATERIALES)

@app.route("/delete/<int:budget_id>")
def delete(budget_id):
    global logged_in
    if not logged_in:
        return redirect(url_for("admin_login"))

    budget = Budget.query.get_or_404(budget_id)
    db.session.delete(budget)
    db.session.commit()
    return redirect(url_for("admin_panel"))

@app.route("/edit_budget/<int:budget_id>", methods=["GET", "POST"])
def edit_budget(budget_id):
    global logged_in
    if not logged_in:
        return redirect(url_for("admin_login"))

    budget = Budget.query.get_or_404(budget_id)

    if request.method == "POST":
        budget.medida_alto = float(request.form["medida_alto"])
        budget.medida_ancho = float(request.form["medida_ancho"])
        budget.descuento = float(request.form.get("descuento", "0"))
        budget.material = request.form["material"]
        budget.monto = float(request.form["monto"])
        db.session.commit()
        return redirect(url_for("admin_panel"))

    return render_template("edit_budget.html", budget=budget, login=logged_in, materiales=MATERIALES)
