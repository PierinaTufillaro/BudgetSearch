"""Rutas para administración."""

from flask import Blueprint, request, render_template, redirect, url_for, flash
from app.models import Material, DescuentoCantidad, PresupuestoMedidas, Credenciales
from ..helpers import login_required
from .. import db
from werkzeug.security import generate_password_hash, check_password_hash

admin_routes = Blueprint('admin', __name__)


@admin_routes.route("/admin_panel", methods=["GET", "POST"])
@login_required('admin')
def admin_panel():
    """Panel principal del administrador con ABMs de materiales y credenciales."""
    if request.method == "POST":
        material_nombre = request.form["material"]
        laminado = float(request.form["laminado"])

        material = Material.query.filter_by(nombre=material_nombre).first()
        if not material:
            material = Material(nombre=material_nombre, porcentaje_por_laminado=laminado)
            db.session.add(material)
            db.session.flush()
        else:
            material.porcentaje_por_laminado = laminado

        DescuentoCantidad.query.filter_by(material_id=material.id).delete()
        PresupuestoMedidas.query.filter_by(material_id=material.id).delete()

        inicios = request.form.getlist("cantidad_inicio[]")
        fines = request.form.getlist("cantidad_fin[]")
        descuentos = request.form.getlist("porcentaje_descuento[]")

        for inicio, fin, desc in zip(inicios, fines, descuentos):
            if inicio and fin and desc:
                d = DescuentoCantidad(
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
        return redirect(url_for("admin.admin_panel"))

    filtro = request.args.get("busqueda", "")
    if filtro:
        descuentos = (
            DescuentoCantidad.query.join(Material)
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
            DescuentoCantidad.query.join(Material)
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
        credenciales=credenciales,
    )

@admin_routes.route("/delete_descuento/<int:descuento_id>")
@login_required('admin')
def delete_descuento(descuento_id):
    descuento = DescuentoCantidad.query.get_or_404(descuento_id)
    db.session.delete(descuento)
    db.session.commit()
    return redirect(url_for("admin.admin_panel"))

@admin_routes.route("/delete_presupuesto/<int:presupuesto_id>")
@login_required('admin')
def delete_presupuesto(presupuesto_id):
    presupuesto = PresupuestoMedidas.query.get_or_404(presupuesto_id)
    db.session.delete(presupuesto)
    db.session.commit()
    return redirect(url_for("admin.admin_panel"))

@admin_routes.route('/edit_material/<int:material_id>', methods=['GET', 'POST'])
@login_required('admin')
def edit_material(material_id):
    material = Material.query.get_or_404(material_id)

    if request.method == 'POST':
        material.nombre = request.form.get('material', '').strip()
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

        DescuentoCantidad.query.filter_by(material_id=material.id).delete()
        cantidad_inicio_list = request.form.getlist('cantidad_inicio[]')
        cantidad_fin_list = request.form.getlist('cantidad_fin[]')
        porcentaje_descuento_list = request.form.getlist('porcentaje_descuento[]')

        for c_inicio, c_fin, p_desc in zip(cantidad_inicio_list, cantidad_fin_list, porcentaje_descuento_list):
            if c_inicio and c_fin and p_desc:
                descuento = DescuentoCantidad(
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

        return redirect(url_for('admin.admin_panel'))

    presupuestos = PresupuestoMedidas.query.filter_by(material_id=material.id).all()
    descuentos = DescuentoCantidad.query.filter_by(material_id=material.id).all()

    return render_template('edit_material.html',
                           material=material,
                           presupuestos=presupuestos,
                           descuentos=descuentos)

@admin_routes.route('/edit_credenciales', methods=['GET', 'POST'])
@login_required('admin')
def edit_credenciales():
    if request.method == 'GET':
        credenciales = Credenciales.query.all()
        return render_template('admin_panel.html', credenciales=credenciales)

    credenciales = Credenciales.query.all()
    cambios_realizados = False

    for cred in credenciales:
        nuevo_usuario = request.form.get(f'usuario_{cred.id}', '').strip()
        actual = request.form.get(f'contrasena_actual_{cred.id}', '').strip()
        nueva = request.form.get(f'contrasena_nueva_{cred.id}', '').strip()

        # Validar cambio de usuario
        if nuevo_usuario and nuevo_usuario != cred.usuario:
            # Opcional: asegurarse de que no exista otro usuario igual
            existente = Credenciales.query.filter_by(usuario=nuevo_usuario).first()
            if existente and existente.id != cred.id:
                flash(f'❌ El usuario "{nuevo_usuario}" ya está en uso.', 'danger')
                return redirect(url_for('admin.admin_panel'))

            cred.usuario = nuevo_usuario
            cambios_realizados = True

        # Validar cambio de contraseña
        if actual and nueva:
            if check_password_hash(cred.contrasena, actual):
                cred.contrasena = generate_password_hash(nueva)
                cambios_realizados = True
            else:
                flash(f'❌ Contraseña actual incorrecta para el usuario "{cred.usuario}". No se actualizó.', 'danger')
                return redirect(url_for('admin.admin_panel'))

        elif actual or nueva:
            flash(f'⚠️ Debes completar ambos campos de contraseña para cambiar la credencial de "{cred.usuario}".', 'warning')
            return redirect(url_for('admin.admin_panel'))

    try:
        if cambios_realizados:
            db.session.commit()
            flash('✅ Credenciales actualizadas correctamente.', 'success')
        else:
            flash('ℹ️ No se realizaron cambios.', 'info')
    except Exception as e:
        db.session.rollback()
        flash('❌ Ocurrió un error al guardar los cambios.', 'danger')

    return redirect(url_for('admin.admin_panel'))


@admin_routes.route('/create_credencial', methods=['GET', 'POST'])
def create_credencial():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            usuario = data.get('usuario', '').strip()
            contrasena_plana = data.get('contrasena', '').strip()
        else:
            usuario = request.form.get('usuario', '').strip()
            contrasena_plana = request.form.get('contrasena', '').strip()

        if not usuario or not contrasena_plana:
            flash('Usuario y contraseña son requeridos.', 'danger')
            return redirect(url_for('create_credencial'))

        existente = Credenciales.query.filter_by(usuario=usuario).first()
        if existente:
            flash('El usuario ya existe.', 'warning')
            return redirect(url_for('create_credencial'))

        contrasena_encriptada = generate_password_hash(contrasena_plana)

        nueva_cred = Credenciales(usuario=usuario, contrasena=contrasena_encriptada)
        db.session.add(nueva_cred)
        db.session.commit()
        flash('Credencial creada correctamente.', 'success')
        return redirect(url_for('admin.admin_panel'))

    return render_template('create_credencial.html')
