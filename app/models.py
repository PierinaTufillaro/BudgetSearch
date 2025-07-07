from . import db

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    monto_por_cm2 = db.Column(db.Float, nullable=False)  # Precio base por cm²
    porcentaje_por_laminado = db.Column(db.Float, default=0)  # % adicional por laminado

    descuentos_medidas = db.relationship('DescuentoMedidas', backref='material', lazy=True)
    presupuestos_medidas = db.relationship('PresupuestoMedidas', backref='material', lazy=True)

    def __repr__(self):
        return f'<Material {self.id} {self.nombre}>'

class DescuentoMedidas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cantidad_inicio = db.Column(db.Float, nullable=False)
    cantidad_fin = db.Column(db.Float, nullable=False)
    porcentaje_descuento_por_cantidad = db.Column(db.Float, nullable=False)

    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)

    def __repr__(self):
        return (f'<DescuentoMedidas {self.id} {self.cantidad_inicio}-{self.cantidad_fin} '
                f'descuento {self.porcentaje_descuento_por_cantidad} %>')

class PresupuestoMedidas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medida_inicio = db.Column(db.Float, nullable=False)
    medida_fin = db.Column(db.Float, nullable=False)
    monto_entre_medidas = db.Column(db.Float, nullable=False)

    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)

    def __repr__(self):
        return (f'<PresupuestoMedidas {self.id} Material {self.material_id} '
                f'{self.medida_inicio}-{self.medida_fin} monto {self.monto_entre_medidas}>')
