from flask import Flask
from datetime import timedelta
from models import db
from auth_router import auth_router
from minha_conta import minha_conta


app = Flask(__name__)
app.config["SECRET_KEY"] = "5c1a32e7f5c8498eaf8b634c2fb7b981e347bbd9e462a06f9a6b8f71b63ad72d"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///usuarios.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.permanent_session_lifetime = timedelta(days=30)

db.init_app(app)
with app.app_context():
    db.create_all()

reset_codes = {}   
delete_codes = {}  
EXPIRA_SEGUNDOS = 30


# Rotas

app.register_blueprint(auth_router)
app.register_blueprint(minha_conta)

# Inicialização

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
