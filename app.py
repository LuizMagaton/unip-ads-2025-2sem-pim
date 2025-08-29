from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session
)
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
import bcrypt, time, random, re




app = Flask(__name__)
app.config["SECRET_KEY"] = "5c1a32e7f5c8498eaf8b634c2fb7b981e347bbd9e462a06f9a6b8f71b63ad72d"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///usuarios.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.permanent_session_lifetime = timedelta(days=30)

db = SQLAlchemy(app)

# =========================
# Modelo
# =========================
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    telefone = db.Column(db.String(32), nullable=False)
    senha = db.Column(db.LargeBinary, nullable=False)  # hash bcrypt


def senha_forte(s: str) -> bool:
    """Mín. 8 caracteres, com letras e números."""
    if len(s) < 8:
        return False
    tem_letra = re.search(r"[A-Za-z]", s) is not None
    tem_num = re.search(r"\d", s) is not None
    return tem_letra and tem_num

def usuario_atual():
    uid = session.get("usuario_id")
    if not uid:
        return None
    return Usuario.query.get(uid)

def exigir_login():
    if not session.get("usuario_id"):
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))
    return None

reset_codes = {}   
delete_codes = {}  
EXPIRA_SEGUNDOS = 30

def gerar_codigo():
    return str(random.randint(100000, 999999))

def valido(caixa, email, code):
    """Valida código e prazo (30s)."""
    dados = caixa.get(email)
    if not dados:
        return False, "Código inexistente ou expirado."
    if time.time() - dados["time"] > EXPIRA_SEGUNDOS:
        caixa.pop(email, None)
        return False, "Código expirado."
    if code != dados["code"]:
        return False, "Código inválido."
    return True, ""


# Rotas

@app.route("/")
def index():
    user = usuario_atual()
    return render_template("index.html", user=user)

@app.route("/register", methods=["GET", "POST"])
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
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
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
        return redirect(url_for("index"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da conta.", "info")
    return redirect(url_for("index"))

# -------- Recuperar senha --------
@app.route("/esquecisenha", methods=["GET", "POST"])
def esquecisenha():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        code = request.form.get("verification_code", "").strip()
        nova = request.form.get("senha", "")
        confirmar = request.form.get("confirmar_senha", "")

        user = Usuario.query.filter_by(email=email).first()


        if email and not code:
            if not user:
                flash("Email não encontrado.", "danger")
                return render_template("esqueci_senha.html", code_sent=False)

            codigo = gerar_codigo()
            reset_codes[email] = {"code": codigo, "time": time.time()}

        
            flash(f"Código: {codigo}", "info")
            return render_template("esqueci_senha.html", code_sent=True, email=email)


        if code:
            ok, motivo = valido(reset_codes, email, code)
            if not ok:
                flash(motivo, "warning" if "expirado" in motivo.lower() else "danger")
                return render_template("esqueci_senha.html", code_sent=False)

            if nova != confirmar:
                flash("As senhas não conferem.", "danger")
                return render_template("esqueci_senha.html", code_sent=True, email=email)

            if not senha_forte(nova):
                flash("Senha fraca: use ao menos 8 caracteres, com letras e números.", "danger")
                return render_template("esqueci_senha.html", code_sent=True, email=email)

            if not user:
                flash("Email não encontrado.", "danger")
                return render_template("esqueci_senha.html", code_sent=False)

            user.senha = bcrypt.hashpw(nova.encode("utf-8"), bcrypt.gensalt())
            db.session.commit()
            reset_codes.pop(email, None)

            flash("Senha redefinida com sucesso! Faça login.", "success")
            return redirect(url_for("login"))


    return render_template("esqueci_senha.html", code_sent=False)

# -------- Minha conta --------
@app.route("/minha_conta")
def minha_conta():
    redir = exigir_login()
    if redir:
        return redir
    return render_template("minha_conta.html")

# -------- Excluir conta --------
@app.route("/delete_account", methods=["POST"])
def delete_account():
    redir = exigir_login()
    if redir:
        return redir

    action = request.form.get("action")
    user = usuario_atual()
    email = user.email

    # 1) Gerar código
    if action == "request_code":
        codigo = gerar_codigo()
        delete_codes[email] = {"code": codigo, "time": time.time()}
        flash(f"Código: {codigo}", "info")  
        return redirect(url_for("minha_conta", code_sent=1))

    # 2) Confirmar exclusão
    if action == "confirm_delete":
        code = request.form.get("verification_code", "").strip()
        ok, motivo = valido(delete_codes, email, code)
        if not ok:
            flash(motivo, "warning" if "expirado" in motivo.lower() else "danger")
            return redirect(url_for("minha_conta"))

        # Remove do banco
        delete_codes.pop(email, None)
        db.session.delete(user)
        db.session.commit()
        session.clear()
        flash("Sua conta foi excluída.", "success")
        return redirect(url_for("index"))

    flash("Ação inválida.", "danger")
    return redirect(url_for("minha_conta"))


# Inicialização

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
