from .. import db


class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

    montos = db.relationship(
        "Monto", backref="material", lazy=True, cascade="all, delete-orphan"
    )
    descuentos = db.relationship(
        "DescuentoCantidad", backref="material", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Material {self.id} {self.nombre}>"
