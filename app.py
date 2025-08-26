from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
import bcrypt

app = Flask(__name__)

@app.route("/")
def menu():
    return render_template("menu.html")

if __name__ == "__main__":
    app.run(debug=True)