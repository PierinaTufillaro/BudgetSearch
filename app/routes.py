from flask import render_template, request, redirect, url_for, session, flash
from datetime import timedelta, datetime
from werkzeug.security import check_password_hash  # si usas hashing
from . import db
import os
from .models import Material, DescuentoMedidas, PresupuestoMedidas, Credenciales
from flask import current_app as app
from dotenv import load_dotenv


# Configuramos tiempo de sesión (1 hora)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.permanent_session_lifetime = timedelta(hours=1)

# -- Helpers para sesión --
def login_required(role):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'user_type' not in session:
                return redirect(url_for('client_login'))
            if session.get('user_type') != role:
                # Redirigir según rol
                if session.get('user_type') == 'admin':
                    return redirect(url_for('admin_panel'))
                else:
                    return redirect(url_for('client_index'))
            # Check expiracion
            if 'login_time' in session:
                now = datetime.utcnow()
                login_time = session['login_time']
                if isinstance(login_time, str):
                    login_time = datetime.fromisoformat(login_time)
                if now - login_time > app.permanent_session_lifetime:
                    session.clear()
                    flash('Sesión expirada, por favor logueate de nuevo.')
                    if role == 'admin':
                        return redirect(url_for('admin_login'))
                    else:
                        return redirect(url_for('client_login'))
            else:
                session.clear()
                if role == 'admin':
                    return redirect(url_for('admin_login'))
                else:
                    return redirect(url_for('client_login'))
            return f(*args, **kwargs)
        return wrapped
    return decorator


@app.route("/", methods=["GET", "POST"])
def client_login():
    if request.method == "POST":
        clave = request.form.get("password", "").strip()
        # Buscar usuario cliente en Credenciales con usuario='cliente'
        cred = Credenciales.query.filter_by(usuario="cliente").first()
        if check_password_hash(cred.contrasena, clave):
            # Si usas hashing de contraseña, check con check_password_hash
                session.permanent = True
                session['user_type'] = 'client'
                session['login_time'] = datetime.utcnow().isoformat()
                materiales = Material.query.all()
                return render_template("client_index.html", materiales=materiales)
        return render_template("client_login.html", error="Contraseña incorrecta")
    return render_template("client_login.html")


@app.route("/client_index", methods=["GET", "POST"])
@login_required('client')
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

            descuento_medidas = (
                DescuentoMedidas.query
                .filter(DescuentoMedidas.material_id == material.id)
                .filter(DescuentoMedidas.cantidad_inicio <= cantidad, DescuentoMedidas.cantidad_fin >= cantidad)
                .order_by(DescuentoMedidas.cantidad_inicio)
                .first()
            )
            descuento_cantidad = descuento_medidas.porcentaje_descuento_por_cantidad if descuento_medidas else 0

            presupuesto_medida = (
                PresupuestoMedidas.query
                .filter(PresupuestoMedidas.material_id == material.id)
                .filter(PresupuestoMedidas.medida_inicio <= area, PresupuestoMedidas.medida_fin >= area)
                .first()
            )

            if presupuesto_medida:
                base_unitario = presupuesto_medida.monto_entre_medidas
            else:
                base_unitario = material.monto_por_cm2 * area

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
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Buscamos en la base de datos por nombre de usuario
        cred = Credenciales.query.filter_by(usuario=username).first()

        if cred and check_password_hash(cred.contrasena, password):
            session.permanent = True
            session['user_type'] = 'admin'
            session['login_time'] = datetime.utcnow().isoformat()
            return redirect(url_for("admin_panel"))
        else:
            return render_template("admin_login.html", error="Usuario o contraseña incorrectos")

    return render_template("admin_login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("client_login"))


@app.route("/admin_panel", methods=["GET", "POST"])
@login_required('admin')
def admin_panel():
    # El resto de tu código actual para admin_panel queda igual,
    # ya que esta ruta solo se puede acceder si está logueado admin
    if request.method == "POST":
        material_nombre = request.form["material"]
        monto = float(request.form["monto"])
        laminado = float(request.form["laminado"])

        material = Material.query.filter_by(nombre=material_nombre).first()
        if not material:
            material = Material(nombre=material_nombre, monto_por_cm2=monto, porcentaje_por_laminado=laminado)
            db.session.add(material)
            db.session.flush()
        else:
            material.monto_por_cm2 = monto
            material.porcentaje_por_laminado = laminado

        DescuentoMedidas.query.filter_by(material_id=material.id).delete()
        PresupuestoMedidas.query.filter_by(material_id=material.id).delete()

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
    credenciales = Credenciales.query.all()

    return render_template(
        "admin_panel.html",
        login=True,
        materiales=materiales,
        descuentos=descuentos,
        presupuestos=presupuestos,
        credenciales=credenciales
    )


@app.route("/delete_descuento/<int:descuento_id>")
@login_required('admin')
def delete_descuento(descuento_id):
    descuento = DescuentoMedidas.query.get_or_404(descuento_id)
    db.session.delete(descuento)
    db.session.commit()
    return redirect(url_for("admin_panel"))


@app.route("/delete_presupuesto/<int:presupuesto_id>")
@login_required('admin')
def delete_presupuesto(presupuesto_id):
    presupuesto = PresupuestoMedidas.query.get_or_404(presupuesto_id)
    db.session.delete(presupuesto)
    db.session.commit()
    return redirect(url_for("admin_panel"))


@app.route('/edit_material/<int:material_id>', methods=['GET', 'POST'])
@login_required('admin')
def edit_material(material_id):
    material = Material.query.get_or_404(material_id)

    if request.method == 'POST':
        material.nombre = request.form.get('material', '').strip()
        material.monto_por_cm2 = float(request.form.get('monto', 0))
        material.porcentaje_por_laminado = float(request.form.get('laminado', 0))

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

    presupuestos = PresupuestoMedidas.query.filter_by(material_id=material.id).all()
    descuentos = DescuentoMedidas.query.filter_by(material_id=material.id).all()

    return render_template('edit_material.html',
                           material=material,
                           presupuestos=presupuestos,
                           descuentos=descuentos)

@app.route('/edit_credenciales', methods=['POST'])
def edit_credenciales():
    credenciales = Credenciales.query.all()
    for cred in credenciales:
        nueva_contrasena = request.form.get(f'contrasena_{cred.id}')
        print(f'Usuario: {cred.usuario}, nueva contrasena: {nueva_contrasena}')
        if nueva_contrasena:
            cred.contrasena = nueva_contrasena
    try:
        db.session.commit()
        print("Credenciales actualizadas correctamente.", "success")
        credenciales_actualizadas = Credenciales.query.all()
        for c in credenciales_actualizadas:
            print(f"Usuario: {c.usuario}, contraseña: {c.contrasena}")
    except Exception as e:
        db.session.rollback()
        print(f"Error al guardar: {str(e)}", "danger")
    return redirect(url_for('client_index'))
