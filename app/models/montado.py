from .. import db


class Montado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_material_montaje = db.Column(db.String(100), nullable=False)
    monto_montado = db.Column(db.Float, nullable=False)

    monto_id = db.Column(
        db.Integer, db.ForeignKey("monto.id", ondelete="CASCADE"), nullable=False
    )

    def __repr__(self):
        return f"<Montado {self.id} {self.nombre_material_montaje} monto_montado {self.monto_montado}>"
