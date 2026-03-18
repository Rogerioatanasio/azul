from .extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)

    trabalhadores = db.relationship("Trabalhador", backref="usuario", lazy=True)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f"<Usuario {self.email}>"


class Trabalhador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    profissao = db.Column(db.String(80), nullable=False)
    whatsapp = db.Column(db.String(40), nullable=False)
    cidade = db.Column(db.String(80), nullable=True)
    estado = db.Column(db.String(2), nullable=True)
    foto = db.Column(db.String(255), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)

    destaque = db.Column(db.Boolean, default=False, nullable=False)
    plano = db.Column(db.String(20), default="gratis", nullable=False)
    
    def __repr__(self):
        return f"<Trabalhador {self.nome}>"