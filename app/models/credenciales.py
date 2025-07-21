from .. import db

class Credenciales(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), nullable=False, unique=True)
    contrasena = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<Credenciales {self.id} {self.usuario}>'
