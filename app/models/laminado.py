from .. import db


class Laminado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto_laminado = db.Column(db.Float, nullable=False)

    monto_id = db.Column(
        db.Integer, db.ForeignKey("monto.id", ondelete="CASCADE"), nullable=False
    )

    def __repr__(self):
        return f"<Laminado {self.id} monto_laminado {self.monto_laminado}>"
