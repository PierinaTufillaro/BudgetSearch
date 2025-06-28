from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Contraseña simple para la pantalla inicial
pwd = "mi_contraseña_segura"

# Usuario y contraseña para login avanzado
USER = "admin"
PASS = "admin123"
MATERIALES = ["Madera", "Metal", "Plástico", "Vidrio"]

logged_in = False  # Estado login avanzado

presupuestos = []

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
def logout():
    global logged_in
    logged_in = False
    return redirect(url_for("client_login"))

@app.route("/admin_panel", methods=["GET"])
def admin_panel():
    global logged_in
    if not logged_in:
        return redirect(url_for("admin_login"))
    return render_template("admin_panel.html", presupuestos=presupuestos, login=logged_in)

@app.route("/admin_panel", methods=["POST"])
def agregar_presupuesto():
    global logged_in
    if not logged_in:
        return redirect(url_for("admin_login"))

    medida_alto = request.form["medida_alto"]
    medida_ancho = request.form["medida_ancho"]
    material = request.form["material"]
    monto = request.form["monto"]

    presupuestos.append({
        "id": len(presupuestos),
        "medida_alto": medida_alto,
        "medida_ancho": medida_ancho,
        "material": material,
        "monto": monto
    })
    return redirect(url_for("admin_panel"))

# Editar y eliminar igual que antes, pero con ruta /admin_panel para consistencia

@app.route("/delete/<int:presupuesto_id>")
def delete(presupuesto_id):
    global logged_in
    if not logged_in:
        return redirect(url_for("admin_login"))

    global presupuestos
    presupuestos = [p for p in presupuestos if p["id"] != presupuesto_id]
    for idx, p in enumerate(presupuestos):
        p["id"] = idx
    return redirect(url_for("admin_panel"))

@app.route("/edit_budget/<int:presupuesto_id>", methods=["GET", "POST"])
def edit_budget(presupuesto_id):
    global logged_in
    if not logged_in:
        return redirect(url_for("admin_login"))

    presupuesto = next((p for p in presupuestos if p["id"] == presupuesto_id), None)
    if not presupuesto:
        return redirect(url_for("admin_panel"))

    if request.method == "POST":
        presupuesto["medida_alto"] = request.form["medida_alto"]
        presupuesto["medida_ancho"] = request.form["medida_ancho"]
        presupuesto["material"] = request.form["material"]
        presupuesto["monto"] = request.form["monto"]
        return redirect(url_for("admin_panel"))

    return render_template("edit_budget.html", presupuesto=presupuesto, login=logged_in)

if __name__ == "__main__":
    app.run(debug=True)
