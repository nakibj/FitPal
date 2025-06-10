from flask import Blueprint, render_template, request, redirect, session, flash
from .auth_manager import AuthManager

auth_bp = Blueprint('auth', __name__)
auth_manager = AuthManager()

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        user = auth_manager.login(email, password)
        if isinstance(user, dict):  # successful login
            session['user'] = user
            return redirect("/dashboard")  # you can change this
        else:
            flash("Login failed.")
    return render_template("login.html")

@auth_bp.route("/signup", methods=["POST"])
def signup():
    email = request.form['email']
    password = request.form['password']
    user = auth_manager.signup(email, password)
    if isinstance(user, dict):
        flash("Signup successful, you can now log in.")
    else:
        flash("Signup failed.")
    return redirect("/login")

from flask import request, redirect, url_for, render_template
from login.firebase_service import save_user_profile, get_user_profile
from login.auth_manager import get_current_user_id  # assuming you have this function
from app import app

@app.route('/save_profile', methods=['POST'])
def save_profile():
    user_id = get_current_user_id()  # make sure this gives you the user id from auth
    
    profile_data = {
        'gender': request.form.get('gender'),
        'height_cm': int(request.form.get('height_cm')),
        'weight_kg': int(request.form.get('weight_kg')),
        'preferred_styles': request.form.getlist('preferred_styles')
    }
    
    save_user_profile(user_id, profile_data)
    return redirect(url_for('profile'))

@app.route('/profile')
def profile():
    user_id = get_current_user_id()
    profile = get_user_profile(user_id)
    return render_template('profile.html', profile=profile)
