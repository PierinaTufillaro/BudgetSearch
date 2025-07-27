"""Rutas para funcionalidades del cliente."""

from flask import Blueprint, request, render_template
from app.models import Material, DescuentoCantidad, PresupuestoMedidas, MaterialMontado
from ..helpers import login_required

client_routes = Blueprint('client', __name__)

@client_routes.route("/client_index", methods=["GET", "POST"])
@login_required('client')
def client_index():
    """Pantalla principal para clientes, permite cotizar productos."""

    materiales = Material.query.all()
    materiales_montados = {}

    # Construir dict de materiales montados como lista de dicts
    for mat in materiales:
        montajes = MaterialMontado.query.filter_by(material_id=mat.id).all()
        materiales_montados[str(mat.id)] = [
            {"id": m.id, "nombre": m.nombre, "porcentaje": m.porcentaje_por_montado}
            for m in montajes
        ]

    resultado = None

    if request.method == "POST":
        material_id = request.form.get("material")

        # No sobrescribas materiales_montados con objetos SQLAlchemy
        # Opcional: filtrar dict para solo el material seleccionado
        if material_id:
            materiales_montados = {
                material_id: materiales_montados.get(material_id, [])
            }

        try:
            ancho = float(request.form["ancho"])
            alto = float(request.form["alto"])
            cantidad = int(request.form["cantidad"])
            material_id = int(request.form["material"])
            laminado = request.form.get("laminado") == "on"
            material_montado_id = request.form.get("material_montado")

            material = Material.query.get_or_404(material_id)
            area = ancho * alto

            # Descuento por cantidad
            descuento_cantidad = (
                DescuentoCantidad.query
                .filter_by(material_id=material.id)
                .filter(DescuentoCantidad.cantidad_inicio <= cantidad,
                        DescuentoCantidad.cantidad_fin >= cantidad)
                .order_by(DescuentoCantidad.cantidad_inicio)
                .first()
            )
            descuento_cantidad = descuento_cantidad.porcentaje_descuento_por_cantidad if descuento_cantidad else 0

            # Presupuesto según medida
            presupuesto_medida = (
                PresupuestoMedidas.query
                .filter_by(material_id=material.id)
                .filter(PresupuestoMedidas.medida_inicio <= area,
                        PresupuestoMedidas.medida_fin >= area)
                .first()
            )
            if not presupuesto_medida:
                raise ValueError("No se encontró una tarifa para el área indicada.")

            base_unitario = presupuesto_medida.monto_entre_medidas

            # Aplicar laminado
            if laminado:
                base_unitario *= (1 + material.porcentaje_por_laminado / 100)

            # Aplicar descuento por cantidad
            base_unitario *= (1 - descuento_cantidad / 100)

            # Aplicar porcentaje por montaje si se eligió
            nombre_montado = None
            precio_montado = 0
            if material_montado_id:
                montado = MaterialMontado.query.get(int(material_montado_id))
                if montado:
                    aumento = base_unitario * (montado.porcentaje_por_montado / 100)
                    base_unitario *= (1 + montado.porcentaje_por_montado / 100)
                    nombre_montado = montado.nombre
                    precio_montado = aumento

            precio_total = base_unitario * cantidad

            resultado = {
                "material": material.nombre,
                "area": area,
                "descuento_cantidad": descuento_cantidad,
                "laminado": laminado,
                "material_montado": nombre_montado,
                "precio_montado": round(precio_montado, 5),
                "precio_unitario": round(base_unitario, 5),
                "precio_total": round(precio_total, 5)
            }

        except Exception as e:
            resultado = {"error": f"Ocurrió un error: {str(e)}"}

    return render_template(
        "client_index.html",
        materiales=materiales,
        materiales_montados=materiales_montados,
        resultado=resultado
    )
