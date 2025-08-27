from flask import Blueprint, render_template ,request ,redirect ,url_for, session, flash
from models import User
import bcrypt

auth_db = Blueprint("auth", __name__)

@auth_db.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("senha")

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            session["user_id"] = user.id
            session["username"] = user.username
            flash("login realizado com sucesso!", "success")
            return redirect(url_for("index"))
        flash("Email ou senha inválidas", "danger")

    return render_template("login.html")

@auth_db.route("/logout")
def logout():
    session.clear()
    flash("Você foi desconectado", "info")
    return redirect(url_for("index"))