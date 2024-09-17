from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user
from app.models import User
from werkzeug.security import check_password_hash

bp = Blueprint('auth', __name__)

@bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('admin_login.html')

@bp.route('/admin/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
