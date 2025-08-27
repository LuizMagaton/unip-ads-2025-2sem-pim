from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# inicializa o banco
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)


    app.config['SECRET_KEY'] = 'sua_chave_secreta'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from .auth import auth_bp
    app.register_blueprint(auth_bp)

    return app