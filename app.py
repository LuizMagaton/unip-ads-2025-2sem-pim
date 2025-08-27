from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
import bcrypt
import random
import string
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)

USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('senha')
        
        users = load_users()
        
        if email in users:
            stored_password = users[email]['password'].encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                session['user_id'] = email
                session['username'] = users[email]['username']
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('index'))
        
        flash('Email ou senha inválidos', 'danger')
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash('Você foi desconectado', 'info')
    return redirect(url_for('index'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        password = request.form.get('senha')
        confirm_password = request.form.get('confirmar_senha')
        
        users = load_users()
        
        if email in users:
            flash('Este email já está registrado', 'danger')
            return render_template("register.html")
        
        if password != confirm_password:
            flash('As senhas não coincidem', 'danger')
            return render_template("register.html")
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        users[email] = {
            'username': email.split('@')[0],
            'password': hashed_password.decode('utf-8'),
            'telefone': telefone
        }
        
        save_users(users)
        
        flash('Conta criada com sucesso! Faça login agora.', 'success')
        return redirect(url_for('login'))
    
    return render_template("register.html")

def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))



verification_codes = {}

deletion_codes = {}

@app.route("/esquecisenha", methods=['GET', 'POST'])
def esquecisenha():
    if request.method == 'POST':
        email = request.form.get('email')
        verification_code = request.form.get('verification_code')
        new_password = request.form.get('senha')
        confirm_password = request.form.get('confirmar_senha')
        
        users = load_users()
        
        if email and not verification_code and not new_password:
            if email not in users:
                flash('Email não encontrado', 'danger')
                return render_template("esqueci_senha.html")
            
            code = generate_verification_code()
            expiration_time = datetime.now() + timedelta(seconds=30)
            verification_codes[email] = {
                'code': code,
                'expiration': expiration_time
            }
            
            flash(f'Um código de verificação foi enviado para {email}. Por favor, verifique seu email. (Código: {code})', 'info')
            return render_template("esqueci_senha.html", email=email, code_sent=True)
        
        elif email and verification_code and new_password and confirm_password:
            if email not in verification_codes:
                flash('Nenhum código de verificação foi solicitado para este email', 'danger')
                return render_template("esqueci_senha.html")
            
            code_info = verification_codes[email]
            
            if datetime.now() > code_info['expiration']:
                del verification_codes[email]
                flash('O código de verificação expirou. Por favor, solicite um novo código', 'danger')
                return render_template("esqueci_senha.html")
            
            if verification_code != code_info['code']:
                flash('Código de verificação inválido', 'danger')
                return render_template("esqueci_senha.html", email=email, code_sent=True)
            
            if new_password != confirm_password:
                flash('As senhas não coincidem', 'danger')
                return render_template("esqueci_senha.html", email=email, code_sent=True)
            
            # Criptografar a nova senha
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            
            # Atualizar a senha do usuário
            users[email]['password'] = hashed_password.decode('utf-8')
            
            save_users(users)
            
            del verification_codes[email]
            
            flash('Senha atualizada com sucesso! Faça login com sua nova senha.', 'success')
            return redirect(url_for('login'))
        
        else:
            flash('Por favor, preencha todos os campos necessários', 'warning')
            return render_template("esqueci_senha.html")
    
    return render_template("esqueci_senha.html")

@app.route("/minha-conta")
@login_required
def minha_conta():
    return render_template("minha_conta.html")

@app.route("/delete-account", methods=['POST'])
@login_required
def delete_account():
    action = request.form.get('action')
    email = session.get('user_id')
    
    if action == 'request_code':
        # Gerar código de verificação
        code = generate_verification_code()
        expiration_time = datetime.now() + timedelta(seconds=30)
        deletion_codes[email] = {
            'code': code,
            'expiration': expiration_time
        }
        
        # Mostrar código temporário
        flash(f'Um código de verificação foi enviado para {email}. Por favor, verifique seu email. (Código: {code})', 'info')
        return redirect(url_for('minha_conta') + '?code_sent=true')
    
    elif action == 'confirm_delete':
        verification_code = request.form.get('verification_code')
        
        if email not in deletion_codes:
            flash('Nenhum código de verificação foi solicitado para este email', 'danger')
            return redirect(url_for('minha_conta'))
        
        code_info = deletion_codes[email]
        
        # Verificar se o código expirou
        if datetime.now() > code_info['expiration']:
            del deletion_codes[email]
            flash('O código de verificação expirou. Por favor, solicite um novo código', 'danger')
            return redirect(url_for('minha_conta'))
        
        # Verificar se o código está correto
        if verification_code != code_info['code']:
            flash('Código de verificação inválido', 'danger')
            return redirect(url_for('minha_conta') + '?code_sent=true')
        
        # Excluir a conta do usuário
        users = load_users()
        if email in users:
            del users[email]
            save_users(users)
        
        del deletion_codes[email]
        
        session.clear()
        
        flash('Sua conta foi excluída com sucesso', 'success')
        return redirect(url_for('index'))
    
    flash('Ação inválida', 'danger')
    return redirect(url_for('minha_conta'))

# Contexto global para templates
@app.context_processor
def inject_user():
    return dict(user=session.get('user_id'))

if __name__ == "__main__":
    app.run(debug=True)