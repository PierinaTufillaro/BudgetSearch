from .. import db

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    porcentaje_por_laminado = db.Column(db.Float, default=0)

    descuento_cantidad = db.relationship('DescuentoCantidad', backref='material', lazy=True)
    presupuestos_medidas = db.relationship('PresupuestoMedidas', backref='material', lazy=True)

    def __repr__(self):
        return f'<Material {self.id} {self.nombre}>'
