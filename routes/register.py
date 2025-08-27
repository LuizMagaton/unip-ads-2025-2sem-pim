from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import User, db
import bcrypt

register_db = Blueprint("register", __name__)

@register_db.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        telefone = request.form.get("telefone")
        password = request.form.get("senha")
        confirm_password = request.form.get("comfirmar_senha")

        if User.query.filter_by(email=email).first():
            flash("Este email já está registrado", "danger")
            return render_template("register.html")
        
        if password != confirm_password:
            flash("As senhas não coincidem", "danger")
            return render_template("register.html")
        
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user = User(email=email, username=email.split("@")[0], password=hashed, telefone=telefone)
        db.session.add(user)
        db.session.commit()

        flash("Conta criada com sucesso! Faça login agora.", "success")
        return redirect(url_for("auth.login"))
    
    return render_template("register.html")