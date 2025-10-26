from models import Usuario, db
from flask import request, flash, render_template, redirect, url_for, Blueprint, session
import bcrypt
from utils import senha_forte, usuario_atual

auth_router = Blueprint('auth',__name__)

@auth_router.route("/")
def index():
    user = usuario_atual()
    return render_template("index.html", user=user)

#---------- Registrar ----------

@auth_router.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        telefone = request.form.get("telefone", "").strip()
        senha = request.form.get("senha", "")
        confirmar = request.form.get("confirmar_senha", "")

        if Usuario.query.filter_by(email=email).first():
            flash("Email já cadastrado.", "danger")
            return render_template("register.html")

        if senha != confirmar:
            flash("As senhas não conferem.", "danger")
            return render_template("register.html")

        if not senha_forte(senha):
            flash("Senha fraca: use ao menos 8 caracteres, com letras e números.", "danger")
            return render_template("register.html")

        senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())
        user = Usuario(email=email, telefone=telefone, senha=senha_hash)
        db.session.add(user)
        db.session.commit()

        flash("Conta criada com sucesso! Faça login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

#---------- Login -----------

@auth_router.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        lembrar = bool(request.form.get("remember"))

        user = Usuario.query.filter_by(email=email).first()
        if not user or not bcrypt.checkpw(senha.encode("utf-8"), user.senha):
            flash("Credenciais inválidas.", "danger")
            return render_template("login.html")

        # Seta sessão conforme seu HTML (minha_conta.html usa session.username & session.user_id)
        session["usuario_id"] = user.id
        session["username"] = email.split("@")[0]  # apelido simples
        session["user_id"]  = user.email          # no seu HTML isso exibe o email

        if lembrar:
            session.permanent = True

        flash("Login realizado com sucesso!", "success")
        return redirect(url_for("auth.index"))

    return render_template("login.html")

#--------- Logout ---------

@auth_router.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da conta.", "info")
    return redirect(url_for("auth.index"))