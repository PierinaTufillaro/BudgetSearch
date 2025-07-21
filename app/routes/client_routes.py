"""Rutas para funcionalidades del cliente."""

from flask import Blueprint, request, render_template
from app.models import Material, DescuentoCantidad, PresupuestoMedidas
from ..helpers import login_required

client_routes = Blueprint('client', __name__)


@client_routes.route("/client_index", methods=["GET", "POST"])
@login_required('client')
def client_index():
    """Pantalla principal para clientes, permite cotizar productos."""

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

            descuento_cantidad = (
                DescuentoCantidad.query
                .filter(DescuentoCantidad.material_id == material.id)
                .filter(DescuentoCantidad.cantidad_inicio <= cantidad, DescuentoCantidad.cantidad_fin >= cantidad)
                .order_by(DescuentoCantidad.cantidad_inicio)
                .first()
            )
            descuento_cantidad = descuento_cantidad.porcentaje_descuento_por_cantidad if descuento_cantidad else 0

            presupuesto_medida = (
                PresupuestoMedidas.query
                .filter(PresupuestoMedidas.material_id == material.id)
                .filter(PresupuestoMedidas.medida_inicio <= area, PresupuestoMedidas.medida_fin >= area)
                .first()
            )

            base_unitario = presupuesto_medida.monto_entre_medidas

            if laminado:
                base_unitario *= (1 + material.porcentaje_por_laminado / 100)

            base_unitario *= (1 - descuento_cantidad / 100)

            precio_total = base_unitario * cantidad

            resultado = {
                "material": material.nombre,
                "area": area,
                "descuento_cantidad": descuento_cantidad,
                "laminado": laminado,
                "precio_unitario": round(base_unitario, 5),
                "precio_total": round(precio_total, 5)
            }

        except Exception as e:
            resultado = {"error": f"Ocurrió un error: {str(e)}"}

    return render_template("client_index.html", materiales=materiales, resultado=resultado)