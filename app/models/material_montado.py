from .. import db


class MaterialMontado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    porcentaje_por_montado = db.Column(db.Float, nullable=False)

    material_id = db.Column(db.Integer, db.ForeignKey('material.id', ondelete="CASCADE"), nullable=False)
