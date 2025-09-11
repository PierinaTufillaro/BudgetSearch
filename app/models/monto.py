from .. import db


class Monto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    desde = db.Column(db.Float, nullable=False)
    hasta = db.Column(db.Float, nullable=False)
    monto = db.Column(db.Float, nullable=False)

    material_id = db.Column(
        db.Integer, db.ForeignKey("material.id", ondelete="CASCADE"), nullable=False
    )

    laminados = db.relationship(
        "Laminado", backref="monto", lazy=True, cascade="all, delete-orphan"
    )
    montados = db.relationship(
        "Montado", backref="monto", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Monto {self.id} {self.desde}-{self.hasta} monto {self.monto}>"
