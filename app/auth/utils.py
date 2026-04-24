from functools import wraps
from datetime import datetime, timedelta
import os
import requests
from flask import session, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import OtpToken

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth.login'))
        
        if session.get('role') != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def customer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth.login'))
        
        if session.get('role') != 'customer':
            flash('Customer access only', 'danger')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def hash_password(password):
    return generate_password_hash(password)

def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)

def create_user_session(user):
    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role
    session.permanent = True

def clear_user_session():
    session.clear()

def get_current_user_id():
    return session.get('user_id')

def get_current_user_role():
    return session.get('role')

def is_authenticated():
    return 'user_id' in session

def is_admin():
    return session.get('role') == 'admin'


def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login to access this page', 'warning')
                return redirect(url_for('auth.login'))
            if session.get('role') not in allowed_roles:
                flash('You do not have permission to access this page', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def staff_required(f):
    return role_required('staff', 'cashier', 'admin')(f)


def cashier_required(f):
    return role_required('cashier', 'admin')(f)


def verify_captcha(response_token, remote_ip=None):
    secret_key = current_app.config.get('RECAPTCHA_SECRET_KEY')
    if not secret_key:
        return True
    payload = {
        'secret': secret_key,
        'response': response_token
    }
    if remote_ip:
        payload['remoteip'] = remote_ip
    try:
        verify_url = 'https://www.google.com/recaptcha/api/siteverify'
        resp = requests.post(verify_url, data=payload, timeout=5)
        data = resp.json()
        return bool(data.get('success'))
    except Exception:
        return False


def generate_otp(user_id, purpose, ttl_minutes=10):
    code = f"{os.urandom(3).hex()[:6]}".upper()
    expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
    token = OtpToken(user_id=user_id, code=code, purpose=purpose, expires_at=expires_at)
    db.session.add(token)
    db.session.commit()
    return code


def validate_otp(user_id, code, purpose):
    if not code:
        return False
    token = (
        OtpToken.query
        .filter_by(user_id=user_id, code=code.upper().strip(), purpose=purpose, used=False)
        .order_by(OtpToken.created_at.desc())
        .first()
    )
    if not token or not token.is_valid(purpose):
        return False
    token.used = True
    db.session.commit()
    return True