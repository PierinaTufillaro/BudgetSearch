from flask import render_template, request, redirect, url_for
from . import db
from .models import Material, DescuentoMedidas, PresupuestoMedidas
from flask import current_app as app

USER = "admin"
PASS = "admin123"
pwd = "mi_contraseña_segura"
logged_in = False

@app.route("/", methods=["GET", "POST"])
def client_login():
    if request.method == "POST":
        clave = request.form.get("password", "")
        if clave == pwd:
            materiales = Material.query.all()
            return render_template("client_index.html", materiales=materiales)
        else:
            return render_template("client_login.html", error="Contraseña incorrecta")
    return render_template("client_login.html")

@app.route("/client_index", methods=["GET", "POST"])
def client_index():
    materiales = Material.query.all()
    resultado = None

    if request.method == "POST":
        try:
            ancho = float(request.form["ancho"])
            alto = float(request.form["alto"])
            cantidad = int(request.form["cantidad"])
            material_id = int(request.form["material"])
            laminado = request.form.get("laminado") == "on"

            material = Material.query.get_or_404(material_id)
            area = ancho * alto

            # Buscar descuento por cantidad
            descuento_medidas = (
                DescuentoMedidas.query
                .filter(DescuentoMedidas.material_id == material.id)
                .filter(DescuentoMedidas.cantidad_inicio <= cantidad, DescuentoMedidas.cantidad_fin >= cantidad)
                .order_by(DescuentoMedidas.cantidad_inicio)
                .first()
            )
            descuento_cantidad = descuento_medidas.porcentaje_descuento_por_cantidad if descuento_medidas else 0

            # Buscar monto unitario según rango en PresupuestoMedidas
            presupuesto_medida = (
                PresupuestoMedidas.query
                .filter(PresupuestoMedidas.material_id == material.id)
                .filter(PresupuestoMedidas.medida_inicio <= area, PresupuestoMedidas.medida_fin >= area)
                .first()
            )

            if presupuesto_medida:
                base_unitario = presupuesto_medida.monto_entre_medidas
            else:
                base_unitario = material.monto_por_cm2 * area  # fallback

            if laminado:
                base_unitario *= (1 + material.porcentaje_por_laminado / 100)

            base_unitario *= (1 - descuento_cantidad / 100)

            precio_total = base_unitario * cantidad

            resultado = {
                "material": material.nombre,
                "area": area,
                "descuento_cantidad": descuento_cantidad,
                "laminado": laminado,
                "precio_unitario": round(base_unitario, 2),
                "precio_total": round(precio_total, 2)
            }

        except Exception as e:
            resultado = {"error": f"Ocurrió un error: {str(e)}"}


    return render_template("client_index.html", materiales=materiales, resultado=resultado)

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    global logged_in
    if request.method == "POST":
        if request.form.get("username") == USER and request.form.get("password") == PASS:
            logged_in = True
            return redirect(url_for("admin_panel"))
        else:
            return render_template("admin_login.html", error="Usuario o contraseña incorrectos")
    return render_template("admin_login.html")

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
        material_nombre = request.form["material"]
        monto = float(request.form["monto"])
        laminado = float(request.form["laminado"])

        material = Material.query.filter_by(nombre=material_nombre).first()
        if not material:
            material = Material(nombre=material_nombre, monto_por_cm2=monto, porcentaje_por_laminado=laminado)
            db.session.add(material)
            db.session.flush()  # Importante para que material.id no sea None
        else:
            material.monto_por_cm2 = monto
            material.porcentaje_por_laminado = laminado

        # Eliminar descuentos y presupuestos viejos asociados
        DescuentoMedidas.query.filter_by(material_id=material.id).delete()
        PresupuestoMedidas.query.filter_by(material_id=material.id).delete()

        # Agregar nuevos descuentos
        inicios = request.form.getlist("cantidad_inicio[]")
        fines = request.form.getlist("cantidad_fin[]")
        descuentos = request.form.getlist("porcentaje_descuento[]")

        for inicio, fin, desc in zip(inicios, fines, descuentos):
            if inicio and fin and desc:
                d = DescuentoMedidas(
                    cantidad_inicio=float(inicio),
                    cantidad_fin=float(fin),
                    porcentaje_descuento_por_cantidad=float(desc),
                    material_id=material.id
                )
                db.session.add(d)

        # Agregar nuevos presupuestos
        m_inicios = request.form.getlist("medida_inicio[]")
        m_fines = request.form.getlist("medida_fin[]")
        montos = request.form.getlist("monto_entre_medidas[]")

        for m_inicio, m_fin, monto_rango in zip(m_inicios, m_fines, montos):
            if m_inicio and m_fin and monto_rango:
                p = PresupuestoMedidas(
                    medida_inicio=float(m_inicio),
                    medida_fin=float(m_fin),
                    monto_entre_medidas=float(monto_rango),
                    material_id=material.id
                )
                db.session.add(p)

        db.session.commit()
        return redirect(url_for("admin_panel"))

    # GET
    filtro = request.args.get("busqueda", "")
    if filtro:
        descuentos = (
            DescuentoMedidas.query.join(Material)
            .filter(Material.nombre.ilike(f"%{filtro}%"))
            .order_by(Material.nombre.asc())
            .all()
        )
        presupuestos = (
            PresupuestoMedidas.query.join(Material)
            .filter(Material.nombre.ilike(f"%{filtro}%"))
            .order_by(Material.nombre.asc())
            .all()
        )
    else:
        descuentos = (
            DescuentoMedidas.query.join(Material)
            .order_by(Material.nombre.asc())
            .all()
        )
        presupuestos = (
            PresupuestoMedidas.query.join(Material)
            .order_by(Material.nombre.asc())
            .all()
        )

    materiales = Material.query.order_by(Material.nombre.asc()).all()

    return render_template(
        "admin_panel.html",
        login=logged_in,
        materiales=materiales,
        descuentos=descuentos,
        presupuestos=presupuestos
    )



@app.route("/delete_descuento/<int:descuento_id>")
def delete_descuento(descuento_id):
    global logged_in
    if not logged_in:
        return redirect(url_for("admin_login"))

    descuento = DescuentoMedidas.query.get_or_404(descuento_id)
    db.session.delete(descuento)
    db.session.commit()
    return redirect(url_for("admin_panel"))

@app.route("/delete_presupuesto/<int:presupuesto_id>")
def delete_presupuesto(presupuesto_id):
    global logged_in
    if not logged_in:
        return redirect(url_for("admin_login"))

    presupuesto = PresupuestoMedidas.query.get_or_404(presupuesto_id)
    db.session.delete(presupuesto)
    db.session.commit()
    return redirect(url_for("admin_panel"))


@app.route('/edit_material/<int:material_id>', methods=['GET', 'POST'])
def edit_material(material_id):
    material = Material.query.get_or_404(material_id)

    if request.method == 'POST':
        # Actualizar datos básicos del material
        material.nombre = request.form.get('material', '').strip()
        material.monto_por_cm2 = float(request.form.get('monto', 0))
        material.porcentaje_por_laminado = float(request.form.get('laminado', 0))

        # Actualizar presupuestos (rangos)
        # Primero borramos los existentes y agregamos los nuevos (podés hacer update si querés)
        PresupuestoMedidas.query.filter_by(material_id=material.id).delete()
        medida_inicio_list = request.form.getlist('medida_inicio[]')
        medida_fin_list = request.form.getlist('medida_fin[]')
        monto_entre_medidas_list = request.form.getlist('monto_entre_medidas[]')

        for inicio, fin, monto in zip(medida_inicio_list, medida_fin_list, monto_entre_medidas_list):
            if inicio and fin and monto:
                rango = PresupuestoMedidas(
                    material_id=material.id,
                    medida_inicio=float(inicio),
                    medida_fin=float(fin),
                    monto_entre_medidas=float(monto)
                )
                db.session.add(rango)

        # Actualizar descuentos (por cantidad)
        # Igual que con presupuestos, borramos y agregamos nuevos
        DescuentoMedidas.query.filter_by(material_id=material.id).delete()
        cantidad_inicio_list = request.form.getlist('cantidad_inicio[]')
        cantidad_fin_list = request.form.getlist('cantidad_fin[]')
        porcentaje_descuento_list = request.form.getlist('porcentaje_descuento[]')

        for c_inicio, c_fin, p_desc in zip(cantidad_inicio_list, cantidad_fin_list, porcentaje_descuento_list):
            if c_inicio and c_fin and p_desc:
                descuento = DescuentoMedidas(
                    material_id=material.id,
                    cantidad_inicio=float(c_inicio),
                    cantidad_fin=float(c_fin),
                    porcentaje_descuento_por_cantidad=float(p_desc)
                )
                db.session.add(descuento)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()

        return redirect(url_for('admin_panel'))

    # GET: renderizamos con los datos cargados
    presupuestos = PresupuestoMedidas.query.filter_by(material_id=material.id).all()
    descuentos = DescuentoMedidas.query.filter_by(material_id=material.id).all()

    return render_template('edit_material.html', 
                            material=material, 
                            presupuestos=presupuestos, 
                            descuentos=descuentos)

