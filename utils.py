import re
from flask import session, flash,redirect,url_for
from models import Usuario
import random
import time
EXPIRA_SEGUNDOS = 30

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