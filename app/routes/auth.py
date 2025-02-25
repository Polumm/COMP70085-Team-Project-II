from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from app.models import User, db
from app.forms import LoginForm, SignupForm
from datetime import datetime, timedelta, timezone
import jwt

auth = Blueprint("auth", __name__)


# JWT Token Generator
def generate_jwt(username, expires_in=3600):
    payload = {
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=expires_in),
    }
    secret_key = (
        "supersecretkey"  # Use the same key as the Chatbot Microservice
    )
    return jwt.encode(payload, secret_key, algorithm="HS256")


@auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        print(user)
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get("next")
            return (
                redirect(next_page)
                if next_page
                else redirect(url_for("main.home"))
            )

        flash(
            "Invalid login. Please try again.", "danger"
        )  # Generic error message

    return render_template("login.html", form=form)


@auth.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Account created! You can now log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("signup.html", form=form)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
