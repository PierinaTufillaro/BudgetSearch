"""Rutas para funcionalidades del cliente."""

from flask import Blueprint, request, render_template
from app.models import Material, DescuentoCantidad, Montado, Monto, Laminado
from ..helpers import login_required
from decimal import Decimal, ROUND_HALF_UP

PRECISION = Decimal("0.0000001")
client_routes = Blueprint("client", __name__)

def formatear_precio(valor: Decimal) -> str:
    """Formatea un Decimal como precio."""
    valor = valor.quantize(PRECISION, rounding=ROUND_HALF_UP)
    texto = f"{valor:f}".rstrip("0").rstrip(".")
    partes = texto.split(".")
    partes[0] = f"{int(partes[0]):,}".replace(",", ".")
    return f"${'.'.join(partes)}"


@client_routes.route("/client_index", methods=["GET", "POST"])
@login_required("client")
def client_index():
    """Pantalla principal para clientes, permite cotizar productos."""

    materiales = Material.query.all()
    materiales_montados = {}
    materiales_laminado = {}

    # Construimos diccionario de montados únicos por material y disponibilidad de laminado
    for mat in materiales:
        montajes = (
            Montado.query
            .join(Monto, Montado.monto_id == Monto.id)
            .filter(Monto.material_id == mat.id)
            .all()
        )
        
        # Crear diccionario para evitar duplicados por nombre
        montados_unicos = {}
        for m in montajes:
            nombre = m.nombre_material_montaje
            if nombre not in montados_unicos:
                montados_unicos[nombre] = {
                    "id": m.id,
                    "nombre": nombre,
                    "monto": m.monto_montado,
                }
        
        materiales_montados[str(mat.id)] = list(montados_unicos.values())
        
        # Verificar si hay laminado disponible para este material
        montos_con_laminado = (
            Monto.query
            .join(Laminado, Monto.id == Laminado.monto_id)
            .filter(Monto.material_id == mat.id)
            .all()
        )
        materiales_laminado[str(mat.id)] = len(montos_con_laminado) > 0

    resultado = None

    if request.method == "POST":
        try:
            material_id = int(request.form.get("material"))
            ancho = Decimal(request.form["ancho"])
            alto = Decimal(request.form["alto"])
            cantidad = Decimal(request.form["cantidad"])
            laminado = request.form.get("laminado") == "on"
            material_montado_ids = request.form.getlist("material_montado")

            material = Material.query.get_or_404(material_id)
            area = ancho * alto

            # Buscar rango de monto según área
            monto_obj = (
                Monto.query
                .filter_by(material_id=material.id)
                .filter(Monto.desde <= area, Monto.hasta >= area)
                .first()
            )
            if not monto_obj:
                raise ValueError("No se encontró una tarifa para el área indicada.")

            # Precio base del rango
            precio_modificado = Decimal(str(monto_obj.monto))

            # Aplicar laminado (si existe para ese rango)
            laminado_obj = Laminado.query.filter_by(monto_id=monto_obj.id).first()
            if laminado and laminado_obj:
                precio_modificado += Decimal(str(laminado_obj.monto_laminado))

            # Aplicar descuento por cantidad
            descuento_cantidad_obj = (
                DescuentoCantidad.query
                .filter_by(material_id=material.id)
                .filter(
                    DescuentoCantidad.cantidad_inicio <= cantidad,
                    DescuentoCantidad.cantidad_fin >= cantidad,
                )
                .order_by(DescuentoCantidad.cantidad_inicio)
                .first()
            )
            descuento_cantidad = (
                Decimal(str(descuento_cantidad_obj.porcentaje_descuento_por_cantidad))
                if descuento_cantidad_obj else Decimal("0")
            )
            precio_modificado *= (Decimal("1") - descuento_cantidad / Decimal("100"))

            # Aplicar montados seleccionados (suma fija por m²)
            precio_por_m2 = precio_modificado
            nombres_montados = []
            for mm_id in material_montado_ids:
                # Verificar que el ID no esté vacío antes de convertir
                if mm_id and mm_id.strip():
                    try:
                        montado = Montado.query.get(int(mm_id))
                        if montado:
                            monto_padre = Monto.query.get(montado.monto_id)
                            if monto_padre and monto_padre.material_id == material.id:
                                if montado.monto_montado is not None:
                                    precio_por_m2 += Decimal(str(montado.monto_montado))
                                nombres_montados.append(montado.nombre_material_montaje)
                    except (ValueError, TypeError):
                        # Si hay error al convertir a int, continuar sin procesar este ID
                        continue

            # Calcular precios
            precio_por_m2 = precio_por_m2.quantize(PRECISION, rounding=ROUND_HALF_UP)
            precio_por_pieza = (precio_por_m2 * area).quantize(PRECISION, rounding=ROUND_HALF_UP)
            precio_total = (precio_por_pieza * cantidad).quantize(PRECISION, rounding=ROUND_HALF_UP)

            resultado = {
                "material": material.nombre,
                "ancho": f"{ancho:.1f} cm",
                "alto": f"{alto:.1f} cm",
                "area": f"{area:.2f} m²",
                "cantidad": int(cantidad),
                "laminado": laminado,
                "material_montado": ", ".join(nombres_montados) if nombres_montados else None,
                "precio_por_m2": formatear_precio(precio_por_m2),
                "precio_por_pieza": formatear_precio(precio_por_pieza),
                "precio_total": formatear_precio(precio_total),
            }

        except Exception as e:
            resultado = {"error": f"Ocurrió un error: {str(e)}"}

    return render_template(
        "client_index.html",
        materiales=materiales,
        materiales_montados=materiales_montados,
        materiales_laminado=materiales_laminado,
        resultado=resultado,
    )
