from .. import db

class DescuentoCantidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cantidad_inicio = db.Column(db.Float, nullable=False)
    cantidad_fin = db.Column(db.Float, nullable=False)
    porcentaje_descuento_por_cantidad = db.Column(db.Float, nullable=False)

    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)

    def __repr__(self):
        return (f'<DescuentoCantidad {self.id} {self.cantidad_inicio}-{self.cantidad_fin} '
                f'descuento {self.porcentaje_descuento_por_cantidad} %>')
