from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, logout_user
from .models import User
from . import db, login_manager
from sqlalchemy import or_
auth = Blueprint("auth", __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form["username"]
        password = request.form["password"]
        
        # Cari berdasarkan username atau email
        user = User.query.filter(
            or_(User.username == identifier, User.email == identifier)
        ).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        
        # (Opsional) Tambahkan pesan error ke template
        return render_template("login.html", error="Invalid credentials.")
    
    return render_template("login.html")

@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
