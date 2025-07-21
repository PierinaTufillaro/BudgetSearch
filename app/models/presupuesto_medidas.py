from .. import db

class PresupuestoMedidas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medida_inicio = db.Column(db.Float, nullable=False)
    medida_fin = db.Column(db.Float, nullable=False)
    monto_entre_medidas = db.Column(db.Float, nullable=False)

    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)

    def __repr__(self):
        return (f'<PresupuestoMedidas {self.id} Material {self.material_id} '
                f'{self.medida_inicio}-{self.medida_fin} monto {self.monto_entre_medidas}>')
