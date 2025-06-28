from . import db

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medida_alto = db.Column(db.Float, nullable=False)
    medida_ancho = db.Column(db.Float, nullable=False)
    descuento = db.Column(db.Float, default=0)
    material = db.Column(db.String(50), nullable=False)
    monto = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Budget {self.id} {self.material}>'
