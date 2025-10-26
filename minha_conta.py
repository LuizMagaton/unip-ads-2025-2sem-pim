from flask import request, Blueprint, flash, render_template, redirect, url_for, session
from models import Usuario, db
# Supondo que 'enviar_email_codigo' está em 'utils' ou em um novo módulo
from utils import gerar_codigo, senha_forte, valido # Adicione enviar_email_codigo se estiver aqui
import bcrypt, time

# Variáveis globais/mock para códigos de reset e delete (idealmente estariam em um banco de dados ou cache)
reset_codes = {}
delete_codes = {}
exigir_login = {}
usuario_atual = {}

# IMPORTANTE: Você deve importar as funções 'exigir_login', 'usuario_atual' e 'enviar_email_codigo'
# Exemplo (Você deve ter essas funções em algum lugar, talvez em 'utils' ou outro módulo):
# from funcoes_seguranca import exigir_login, usuario_atual
# from email_service import enviar_email_codigo 

# Criando o Blueprint
minha_conta = Blueprint('minha_conta', __name__)


# -------- Recuperar senha --------
@minha_conta.route("/esquecisenha", methods=["GET", "POST"])
def esquecisenha():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        code = request.form.get("verification_code", "").strip()
        nova = request.form.get("senha", "")
        confirmar = request.form.get("confirmar_senha", "")

        user = Usuario.query.filter_by(email=email).first()

        # 1. Solicitação de código
        if email and not code:
            if not user:
                flash("Email não encontrado.", "danger")
                return render_template("esqueci_senha.html", code_sent=False)

            codigo = gerar_codigo()
            reset_codes[email] = {"code": codigo, "time": time.time()}

            # 🚨 INTEGRAÇÃO DE E-MAIL AQUI 🚨
            # Chame sua função para enviar o e-mail com o código
            try:
                # Exemplo: enviar_email_codigo(email, codigo, assunto="Recuperação de Senha")
                pass # Substitua este 'pass' pela chamada real da sua função de e-mail
                flash(f"Um código de segurança foi enviado para {email}.", "info")
            except Exception as e:
                # Tratar falhas no envio (ex: servidor de e-mail fora do ar)
                print(f"Erro ao enviar e-mail: {e}") 
                flash("Erro ao enviar o código. Tente novamente mais tarde.", "danger")
                return render_template("esqueci_senha.html", code_sent=False)
            
            # Código de debug removido/comentado: # flash(f"Código: {codigo}", "info") 
            
            return render_template("esqueci_senha.html", code_sent=True, email=email)


        # 2. Confirmação de código e nova senha
        if code:
            # Note que a checagem de 'user' deve ser feita aqui novamente
            if not user:
                flash("Email não encontrado.", "danger")
                return render_template("esqueci_senha.html", code_sent=False) 
                
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

            # Usuário já foi checado no início ou no 'if code', mas mantive o seu código:
            # if not user: 
            #     flash("Email não encontrado.", "danger")
            #     return render_template("esqueci_senha.html", code_sent=False)

            user.senha = bcrypt.hashpw(nova.encode("utf-8"), bcrypt.gensalt())
            db.session.commit()
            reset_codes.pop(email, None)

            flash("Senha redefinida com sucesso! Faça login.", "success")
            return redirect(url_for("login"))


    return render_template("esqueci_senha.html", code_sent=False)

# -------- Minha conta --------
@minha_conta.route("/minha_conta")
def minha_conta_route(): # Renomeada para evitar conflito com o nome do Blueprint
    # Assumindo que exigir_login() retorna um redirect se necessário
    redir = exigir_login() 
    if redir:
        return redir
    return render_template("minha_conta.html")

# -------- Excluir conta --------
@minha_conta.route("/delete_account", methods=["POST"])
def delete_account():
    # Assumindo que exigir_login() retorna um redirect se necessário
    redir = exigir_login() 
    if redir:
        return redir

    action = request.form.get("action")
    user = usuario_atual() # Assumindo que usuario_atual() pega o usuário logado
    email = user.email

    # 1) Gerar código
    if action == "request_code":
        codigo = gerar_codigo()
        delete_codes[email] = {"code": codigo, "time": time.time()}
        
        # 🚨 INTEGRAÇÃO DE E-MAIL AQUI 🚨
        # Chame sua função para enviar o e-mail com o código de exclusão
        try:
            # Exemplo: enviar_email_codigo(email, codigo, assunto="Confirmação de Exclusão de Conta")
            pass # Substitua este 'pass' pela chamada real da sua função de e-mail
            flash(f"Um código de segurança para exclusão foi enviado para {email}.", "info")
        except Exception as e:
            print(f"Erro ao enviar e-mail de exclusão: {e}") 
            flash("Erro ao enviar o código. Tente novamente mais tarde.", "danger")
        
        # Código de debug removido/comentado: # flash(f"Código: {codigo}", "info") 
        return redirect(url_for("minha_conta_route", code_sent=1))

    # 2) Confirmar exclusão
    if action == "confirm_delete":
        code = request.form.get("verification_code", "").strip()
        ok, motivo = valido(delete_codes, email, code)
        if not ok:
            flash(motivo, "warning" if "expirado" in motivo.lower() else "danger")
            return redirect(url_for("minha_conta_route"))

        # Remove do banco
        delete_codes.pop(email, None)
        db.session.delete(user)
        db.session.commit()
        session.clear()
        flash("Sua conta foi excluída.", "success")
        return redirect(url_for("index"))

    flash("Ação inválida.", "danger")
    return redirect(url_for("minha_conta_route"))