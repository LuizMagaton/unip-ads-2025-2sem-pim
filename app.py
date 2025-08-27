from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
import bcrypt

app = Flask(__name__)

@app.route("/")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/esquecisenha")
def esquecisenha():
    return render_template("esqueci_senha.html")

if __name__ == "__main__":
    app.run(debug=True)