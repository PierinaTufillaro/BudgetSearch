from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Material, Monto, Laminado, Montado, DescuentoCantidad, Credenciales
from .. import db
from werkzeug.security import generate_password_hash
from ..helpers import login_required


admin_routes = Blueprint("admin", __name__)

@admin_routes.route("/admin_panel", methods=["GET", "POST"])
@login_required("admin")
def admin_panel():
    # ===========================
    # CREAR NUEVO MATERIAL + RANGOS
    # ===========================
    if request.method == "POST":
        nombre_material = request.form.get("material")
        if not nombre_material:
            flash("El nombre del material es obligatorio", "danger")
            return redirect(url_for("admin.admin_panel"))

        material = Material(nombre=nombre_material)
        db.session.add(material)
        db.session.commit()

        # Guardar rangos de presupuesto
        medidas_inicio = request.form.getlist("medida_inicio[]")
        medidas_fin = request.form.getlist("medida_fin[]")
        montos = request.form.getlist("monto_entre_medidas[]")
        laminados = request.form.getlist("laminado_new_new")

        for i in range(len(medidas_inicio)):
            monto_obj = Monto(
                material_id=material.id,
                desde=float(medidas_inicio[i]),
                hasta=float(medidas_fin[i]),
                monto=float(montos[i])
            )
            db.session.add(monto_obj)
            db.session.commit()

            # Laminado opcional
            laminado_val = laminados[i] if i < len(laminados) and laminados[i] else None
            if laminado_val:
                lam = Laminado(monto_id=monto_obj.id, monto_laminado=float(laminado_val))
                db.session.add(lam)

            # Montados opcionales para este rango específico
            nombres_montados_rango = request.form.getlist(f"nombre_montado_rango_{i}[]")
            montos_montados_rango = request.form.getlist(f"monto_montado_rango_{i}[]")
            
            for j in range(len(nombres_montados_rango)):
                if nombres_montados_rango[j] and j < len(montos_montados_rango) and montos_montados_rango[j]:
                    montado = Montado(
                        monto_id=monto_obj.id,
                        nombre_material_montaje=nombres_montados_rango[j],
                        monto_montado=float(montos_montados_rango[j])
                    )
                    db.session.add(montado)

        # Descuentos opcionales
        cant_inicio = request.form.getlist("cantidad_inicio[]")
        cant_fin = request.form.getlist("cantidad_fin[]")
        porc_desc = request.form.getlist("porcentaje_descuento[]")
        for i in range(len(cant_inicio)):
            descuento = DescuentoCantidad(
                material_id=material.id,
                cantidad_inicio=float(cant_inicio[i]),
                cantidad_fin=float(cant_fin[i]),
                porcentaje_descuento_por_cantidad=float(porc_desc[i])
            )
            db.session.add(descuento)

        db.session.commit()
        flash("Material y rangos guardados correctamente", "success")
        return redirect(url_for("admin.admin_panel"))

    # ===========================
    # MOSTRAR DATOS
    # ===========================
    busqueda = request.args.get("busqueda", "")
    if busqueda:
        materiales = Material.query.filter(Material.nombre.ilike(f"%{busqueda}%")).all()
    else:
        materiales = Material.query.all()

    montos = Monto.query.join(Material).all()
    descuentos = DescuentoCantidad.query.join(Material).all()
    laminados_por_monto = {l.monto_id: l for l in Laminado.query.all()}
    montados_por_monto = {}
    for monto in montos:
        montados_por_monto[monto.id] = monto.montados  # relación Montado.monto_id -> monto.id

    return render_template(
        "admin_panel.html",
        login=True,
        materiales=materiales,
        montos=montos,
        descuentos=descuentos,
        laminados_por_monto=laminados_por_monto,
        montados_por_monto=montados_por_monto
    )


@admin_routes.route("/delete_material/<int:material_id>")
@login_required("admin")
def delete_material(material_id):
    material = Material.query.get_or_404(material_id)
    db.session.delete(material)
    db.session.commit()
    flash("Material eliminado correctamente", "success")
    return redirect(url_for("admin.admin_panel"))


@admin_routes.route("/edit_material/<int:material_id>", methods=["GET", "POST"])
@login_required("admin")
def edit_material(material_id):
    material = Material.query.get_or_404(material_id)
    if request.method == "POST":
        # Actualizar nombre del material
        material.nombre = request.form.get("material", material.nombre)
        
        # Eliminar datos existentes
        # Primero eliminar Montados y Laminados (que dependen de Monto)
        montos_existentes = Monto.query.filter_by(material_id=material.id).all()
        for monto in montos_existentes:
            Montado.query.filter_by(monto_id=monto.id).delete()
            Laminado.query.filter_by(monto_id=monto.id).delete()
        
        # Luego eliminar Montos y Descuentos
        Monto.query.filter_by(material_id=material.id).delete()
        DescuentoCantidad.query.filter_by(material_id=material.id).delete()
        
        # Guardar rangos de presupuesto
        medidas_inicio = request.form.getlist("medida_inicio[]")
        medidas_fin = request.form.getlist("medida_fin[]")
        montos = request.form.getlist("monto_entre_medidas[]")
        laminados = request.form.getlist("laminado_new_new")

        for i in range(len(medidas_inicio)):
            monto_obj = Monto(
                material_id=material.id,
                desde=float(medidas_inicio[i]),
                hasta=float(medidas_fin[i]),
                monto=float(montos[i])
            )
            db.session.add(monto_obj)
            db.session.commit()

            # Laminado opcional
            laminado_val = laminados[i] if i < len(laminados) and laminados[i] else None
            if laminado_val:
                lam = Laminado(monto_id=monto_obj.id, monto_laminado=float(laminado_val))
                db.session.add(lam)

            # Montados opcionales para este rango específico
            nombres_montados_rango = request.form.getlist(f"nombre_montado_rango_{i}[]")
            montos_montados_rango = request.form.getlist(f"monto_montado_rango_{i}[]")
            
            for j in range(len(nombres_montados_rango)):
                if nombres_montados_rango[j] and j < len(montos_montados_rango) and montos_montados_rango[j]:
                    montado = Montado(
                        monto_id=monto_obj.id,
                        nombre_material_montaje=nombres_montados_rango[j],
                        monto_montado=float(montos_montados_rango[j])
                    )
                    db.session.add(montado)

        # Descuentos opcionales
        cant_inicio = request.form.getlist("cantidad_inicio[]")
        cant_fin = request.form.getlist("cantidad_fin[]")
        porc_desc = request.form.getlist("porcentaje_descuento[]")

        for i in range(len(cant_inicio)):
            if cant_inicio[i] and cant_fin[i] and porc_desc[i]:
                descuento = DescuentoCantidad(
                    material_id=material.id,
                    cantidad_inicio=float(cant_inicio[i]),
                    cantidad_fin=float(cant_fin[i]),
                    porcentaje_descuento_por_cantidad=float(porc_desc[i])
                )
                db.session.add(descuento)

        db.session.commit()
        flash("Material actualizado correctamente", "success")
        return redirect(url_for("admin.admin_panel"))
    
    # Get related data for the template
    montos = Monto.query.filter_by(material_id=material.id).all()
    descuentos = DescuentoCantidad.query.filter_by(material_id=material.id).all()
    
    return render_template("edit_material.html", material=material, montos=montos, descuentos=descuentos)


@admin_routes.route("/edit_credentials", methods=["GET", "POST"])
@login_required("admin")
def edit_credentials():
    """Editar credenciales de administrador y cliente"""
    if request.method == "POST":
        # Obtener credenciales existentes
        admin_cred = Credenciales.query.filter_by(usuario="admin").first()
        client_cred = Credenciales.query.filter_by(usuario="client").first()
        
        # Actualizar contraseña de admin si se proporcionó
        admin_password = request.form.get("admin_password", "").strip()
        if admin_password:
            if not admin_cred:
                admin_cred = Credenciales(usuario="admin")
                db.session.add(admin_cred)
            admin_cred.contrasena = generate_password_hash(admin_password)
        
        # Actualizar contraseña de cliente si se proporcionó
        client_password = request.form.get("client_password", "").strip()
        if client_password:
            if not client_cred:
                client_cred = Credenciales(usuario="client")
                db.session.add(client_cred)
            client_cred.contrasena = generate_password_hash(client_password)
        
        db.session.commit()
        flash("Credenciales actualizadas correctamente", "success")
        return redirect(url_for("admin.admin_panel"))
    
    # GET: Mostrar formulario con credenciales actuales
    admin_cred = Credenciales.query.filter_by(usuario="admin").first()
    client_cred = Credenciales.query.filter_by(usuario="client").first()
    
    return render_template("edit_credentials.html", 
                         admin_exists=admin_cred is not None,
                         client_exists=client_cred is not None)
