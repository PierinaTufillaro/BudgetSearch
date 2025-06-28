from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configuración DB SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budgets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Contraseña simple para la pantalla inicial
pwd = "mi_contraseña_segura"

# Usuario y contraseña para login avanzado
USER = "admin"
PASS = "admin123"
MATERIALES = ["Madera", "Metal", "Plástico", "Vidrio"]

logged_in = False  # Estado login avanzado

# Modelo Budget
class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medida_alto = db.Column(db.Float, nullable=False)
    medida_ancho = db.Column(db.Float, nullable=False)
    descuento = db.Column(db.Float, default=0)
    material = db.Column(db.String(50), nullable=False)
    monto = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Budget {self.id} {self.material}>'

# Crear tablas si no existen
with app.app_context():
    db.create_all()

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

@app.route("/admin_panel", methods=["GET"])
def admin_panel():
    if not logged_in:
        return redirect(url_for("admin_login"))
    budgets = Budget.query.all()
    return render_template("admin_panel.html", budgets=budgets, login=logged_in, materiales=MATERIALES)

@app.route("/admin_panel", methods=["POST"])
def add_budget():
    if not logged_in:
        return redirect(url_for("admin_login"))

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

@app.route("/delete/<int:budget_id>")
def delete(budget_id):
    if not logged_in:
        return redirect(url_for("admin_login"))

    budget = Budget.query.get_or_404(budget_id)
    db.session.delete(budget)
    db.session.commit()

    return redirect(url_for("admin_panel"))

@app.route("/edit_budget/<int:budget_id>", methods=["GET", "POST"])
def edit_budget(budget_id):
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

if __name__ == "__main__":
    app.run(debug=True)
