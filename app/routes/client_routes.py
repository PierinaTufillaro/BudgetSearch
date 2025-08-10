"""Rutas para funcionalidades del cliente."""

from flask import Blueprint, request, render_template
from app.models import Material, DescuentoCantidad, PresupuestoMedidas, MaterialMontado
from ..helpers import login_required
from decimal import Decimal, ROUND_HALF_UP

PRECISION = Decimal("0.0000001")
client_routes = Blueprint('client', __name__)

def formatear_precio(valor: Decimal) -> str:
    """
    Formatea un Decimal como precio:
    - Hasta 7 decimales (sin ceros a la derecha innecesarios)
    - Separador de miles
    - Símbolo $
    """
    valor = valor.quantize(PRECISION, rounding=ROUND_HALF_UP)
    texto = f"{valor:f}".rstrip("0").rstrip(".")
    partes = texto.split(".")
    partes[0] = f"{int(partes[0]):,}".replace(",", ".")  
    return f"${'.'.join(partes)}"

@client_routes.route("/client_index", methods=["GET", "POST"])
@login_required('client')
def client_index():
    """Pantalla principal para clientes, permite cotizar productos."""

    materiales = Material.query.all()
    materiales_montados = {}

    for mat in materiales:
        montajes = MaterialMontado.query.filter_by(material_id=mat.id).all()
        materiales_montados[str(mat.id)] = [
            {"id": m.id, "nombre": m.nombre, "porcentaje": m.porcentaje_por_montado}
            for m in montajes
        ]

    resultado = None

    if request.method == "POST":
        material_id = request.form.get("material")

        if material_id:
            materiales_montados = {
                material_id: materiales_montados.get(material_id, [])
            }

        try:
            ancho = Decimal(request.form["ancho"])
            alto = Decimal(request.form["alto"])
            cantidad = Decimal(request.form["cantidad"])
            material_id = int(request.form["material"])
            laminado = request.form.get("laminado") == "on"
            material_montado_id = request.form.get("material_montado")

            material = Material.query.get_or_404(material_id)
            area = ancho * alto

            descuento_cantidad_obj = (
                DescuentoCantidad.query
                .filter_by(material_id=material.id)
                .filter(DescuentoCantidad.cantidad_inicio <= cantidad,
                        DescuentoCantidad.cantidad_fin >= cantidad)
                .order_by(DescuentoCantidad.cantidad_inicio)
                .first()
            )
            descuento_cantidad = (Decimal(str(descuento_cantidad_obj.porcentaje_descuento_por_cantidad))
                                 if descuento_cantidad_obj else Decimal("0"))
            
            presupuesto_medida_obj = (
                PresupuestoMedidas.query
                .filter_by(material_id=material.id)
                .filter(PresupuestoMedidas.medida_inicio <= area,
                        PresupuestoMedidas.medida_fin >= area)
                .first()
            )
            if not presupuesto_medida_obj:
                raise ValueError("No se encontró una tarifa para el área indicada.")

            valor_float = presupuesto_medida_obj.monto_entre_medidas
            valor_str = f"{valor_float:.7f}"
            base_unitario = Decimal(valor_str)  # Precio base sin laminado ni descuento

            precio_modificado = base_unitario

            if laminado:
                porcentaje_laminado = Decimal(str(material.porcentaje_por_laminado))
                precio_modificado *= (Decimal("1") + porcentaje_laminado / Decimal("100"))

            precio_modificado *= (Decimal("1") - descuento_cantidad / Decimal("100"))

            porcentaje_montado = Decimal("0")
            nombre_montado = None
            if material_montado_id:
                montado = MaterialMontado.query.get(int(material_montado_id))
                if montado:
                    porcentaje_montado = Decimal(str(montado.porcentaje_por_montado)) / Decimal("100")
                    nombre_montado = montado.nombre

            precio_unitario_final = (precio_modificado * (Decimal("1") + porcentaje_montado)).quantize(PRECISION, rounding=ROUND_HALF_UP)

            precio_total = (precio_unitario_final * cantidad).quantize(PRECISION, rounding=ROUND_HALF_UP)

            precio_montado = (precio_unitario_final - precio_modificado).quantize(PRECISION, rounding=ROUND_HALF_UP)

            resultado = {
                "material": material.nombre,
                "area": f"{area:.2f} m²",
                "descuento_cantidad": f"{descuento_cantidad}%",
                "laminado": laminado,
                "material_montado": nombre_montado,
                "precio_montado": formatear_precio(precio_montado),
                "precio_unitario": formatear_precio(precio_unitario_final),
                "precio_total": formatear_precio(precio_total)
            }

        except Exception as e:
            resultado = {"error": f"Ocurrió un error: {str(e)}"}

    return render_template(
        "client_index.html",
        materiales=materiales,
        materiales_montados=materiales_montados,
        resultado=resultado
    )
