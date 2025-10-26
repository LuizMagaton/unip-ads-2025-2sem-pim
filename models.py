from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
 
# =========================
# Modelo
# =========================
class Usuario(db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    telefone = db.Column(db.String(32), nullable=False)
    senha = db.Column(db.LargeBinary, nullable=False)  # hash bcrypt
    def __repr__(self):
        return f"<Usuario{self.email}>"
