"""
LOOPH E-Commerce Platform - Authentication Routes
Login, Register (with OTP), Forgot Password (with OTP), Logout
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.crypto import encrypt_field
from app import db
from app.models import User, OtpToken
from app.utils.helpers import is_valid_email, sanitize_string
from app.utils.export import export_to_excel
from app.auth.utils import verify_captcha, generate_otp, validate_otp
from app.utils.email import send_email, send_welcome_email

auth_bp = Blueprint('auth', __name__)


# ── OTP EMAIL HELPER ────────────────────────────────────────────────────────

def _send_otp_email(to_email, otp_code, purpose='verify'):
    if purpose == 'reset':
        subject = "Your loophco Password Reset Code"
        heading = "PASSWORD RESET"
        note = "You requested a password reset on loophco."
    else:
        subject = "Your loophco Verification Code"
        heading = "EMAIL VERIFICATION"
        note = "Thanks for joining loophco."

    html_body = f"""
    <div style="background:#080807;padding:48px 32px;font-family:'DM Sans',Arial,sans-serif;color:#f0ede6;text-align:center;max-width:480px;margin:0 auto">
      <p style="font-family:'Cormorant Garamond',Georgia,serif;font-size:2.2rem;font-weight:300;letter-spacing:.12em;margin-bottom:.25rem">loophco</p>
      <p style="color:#5a5550;font-size:.65rem;letter-spacing:.28em;text-transform:uppercase;margin-bottom:2.5rem">{heading}</p>
      <div style="border:1px solid rgba(196,169,125,.22);padding:2rem;margin-bottom:2rem">
        <p style="color:#a09890;font-size:.82rem;margin-bottom:1.25rem">{note} Your one-time code is:</p>
        <p style="font-family:'DM Mono',monospace;font-size:2.6rem;letter-spacing:.3em;color:#c4a97d;margin:0">{otp_code}</p>
        <p style="color:#5a5550;font-size:.72rem;margin-top:1.25rem">Expires in 10 minutes. Do not share this code.</p>
      </div>
      <p style="color:#5a5550;font-size:.68rem">If you didn't request this, you can safely ignore this email.</p>
    </div>
    """
    text_body = f"Your loophco code: {otp_code}. Expires in 10 minutes."
    return send_email(to_email, subject, html_body, text_body)


# ── PENDING USER HELPER — stores/retrieves registration data via DB OtpToken ─
# NOTE: We use a temporary "placeholder" User approach: pending data lives in
# the session (short-lived), but the OTP itself is backed by DB so a session
# drop doesn't invalidate the code. If the session IS lost entirely the user
# must register again — that is the correct UX.

def _get_pending_or_abort(email):
    """Return pending registration dict from session, or None if missing."""
    if not email:
        return None
    keys = ['pending_username', 'pending_full_name', 'pending_address',
            'pending_phone', 'pending_password']
    data = {k.replace('pending_', ''): session.get(k) for k in keys}
    if not all(data.values()):
        return None
    return data


# ── LOGIN ────────────────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('customer.shop'))

    if request.method == 'POST':
        username_or_email = sanitize_string(request.form.get('username_or_email'), max_length=120)
        password = request.form.get('password', '')

        if not username_or_email or not password:
            return render_template('login.html', error='Email/Username and password are required')

        # Try to find user by username first, then by email
        user = User.query.filter_by(username=username_or_email).first()
        if not user:
            user = User.query.filter_by(email=username_or_email.lower()).first()

        if user and check_password_hash(user.password, password):
            if user.role == 'customer' and not getattr(user, 'is_verified', True):
                return render_template('login.html', error='Please verify your email before logging in.')
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session.permanent = True
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard', toast='login'))
            return redirect(url_for('customer.shop', toast='login'))
        else:
            return render_template('login.html', error='Invalid email/username or password')

    return render_template('login.html')


# ── REGISTER — Step 1: Collect details, validate, send OTP ──────────────────

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('customer.shop'))

    if request.method == 'POST':
        username         = sanitize_string(request.form.get('username'), max_length=80)
        email            = sanitize_string(request.form.get('email'), max_length=120)
        full_name        = sanitize_string(request.form.get('full_name'), max_length=120)
        address          = sanitize_string(request.form.get('address'))
        phone_number     = sanitize_string(request.form.get('phone_number'), max_length=30)
        password         = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        captcha_response = request.form.get('g-recaptcha-response', '')

        if not all([username, email, password, confirm_password, full_name, address, phone_number]):
            return render_template('register.html', error='All fields are required')
        if len(username) < 3:
            return render_template('register.html', error='Username must be at least 3 characters')
        if len(password) < 6:
            return render_template('register.html', error='Password must be at least 6 characters')
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')
        if not is_valid_email(email):
            return render_template('register.html', error='Invalid email format')
        email_lower = email.lower().strip()
        if not email_lower.endswith('@gmail.com'):
            return render_template('register.html', error='Please use a Gmail address (@gmail.com)')
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists')
        if User.query.filter_by(email=email_lower).first():
            return render_template('register.html', error='Email already registered')
        if not verify_captcha(captcha_response, request.remote_addr):
            return render_template('register.html', error='CAPTCHA verification failed. Please try again.')

        # ── FIX: Use a temporary placeholder user to anchor the OtpToken in DB ──
        # This makes OTP resilient to session loss between steps.
        # We create a "pending" (unverified) user record, then activate it on verify.
        try:
            # Clean up any previous pending record for this email (e.g. re-registration)
            existing_pending = User.query.filter_by(email=email_lower, is_verified=False).first()
            if existing_pending:
                # Remove old OTP tokens for this user
                OtpToken.query.filter_by(user_id=existing_pending.id, purpose='verify').delete()
                db.session.delete(existing_pending)
                db.session.commit()

            pending_user = User(
                username     = username,
                email        = email_lower,
                password     = generate_password_hash(password),
                role         = 'customer',
                full_name    = full_name,
                address      = encrypt_field(address),
                phone_number = encrypt_field(phone_number),
                is_verified  = False,  # Not active until OTP confirmed
            )
            db.session.add(pending_user)
            db.session.commit()

            # Generate OTP stored in DB (not session) — survives session loss
            otp_code = generate_otp(pending_user.id, purpose='verify', ttl_minutes=10)
            session['pending_email']   = email_lower
            session['pending_user_id'] = pending_user.id

        except Exception as e:
            print(f"--- REGISTER DB ERROR: {e} ---")
            db.session.rollback()
            return render_template('register.html', error='Registration failed. Please try again.')

        try:
            _send_otp_email(email_lower, otp_code, purpose='verify')
        except Exception as e:
            print(f"--- OTP EMAIL ERROR: {e} ---")
            # Clean up the pending user since email failed
            try:
                db.session.delete(pending_user)
                db.session.commit()
            except Exception:
                db.session.rollback()
            return render_template('register.html', error='Failed to send verification email. Please check your email address and try again.')

        return redirect(url_for('auth.verify_email'))

    return render_template('register.html')


# ── REGISTER — Step 2: Verify OTP ───────────────────────────────────────────

@auth_bp.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    email = session.get('pending_email')
    if not email:
        return redirect(url_for('auth.register'))

    if request.method == 'POST':
        otp_entered  = request.form.get('otp_code', '').strip().upper()
        user_id      = session.get('pending_user_id')

        # Fallback: look up pending user by email if session_user_id was lost
        if not user_id:
            pending = User.query.filter_by(email=email, is_verified=False).first()
            if pending:
                user_id = pending.id
            else:
                return render_template('verify_otp.html',
                    error='Session expired. Please register again.', email=email)

        if not otp_entered:
            return render_template('verify_otp.html',
                error='Please enter the verification code.', email=email)

        if not validate_otp(user_id, otp_entered, purpose='verify'):
            return render_template('verify_otp.html',
                error='Invalid or expired code. Please check your email.', email=email)

        try:
            user = User.query.get(user_id)
            if not user:
                return render_template('verify_otp.html',
                    error='Account not found. Please register again.', email=email)

            user.is_verified = True
            db.session.commit()
            export_to_excel()
            send_welcome_email(user)

            for key in ['pending_email', 'pending_user_id']:
                session.pop(key, None)

            flash('Account verified! You can now sign in.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            print(f"--- DB SAVE ERROR: {e} ---")
            db.session.rollback()
            return render_template('verify_otp.html',
                error='Something went wrong. Please try again.', email=email)

    return render_template('verify_otp.html', email=email)


# ── REGISTER — Resend OTP ───────────────────────────────────────────────────

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    email   = session.get('pending_email')
    user_id = session.get('pending_user_id')
    if not email:
        return redirect(url_for('auth.register'))

    if not user_id:
        pending = User.query.filter_by(email=email, is_verified=False).first()
        if pending:
            user_id = pending.id
        else:
            flash('Session expired. Please register again.', 'error')
            return redirect(url_for('auth.register'))

    try:
        # Invalidate old tokens before issuing new one
        OtpToken.query.filter_by(user_id=user_id, purpose='verify', used=False).update({'used': True})
        db.session.commit()

        otp_code = generate_otp(user_id, purpose='verify', ttl_minutes=10)
        _send_otp_email(email, otp_code, purpose='verify')
        flash('A new code has been sent to your email.', 'info')
    except Exception as e:
        print(f"--- RESEND OTP ERROR: {e} ---")
        flash('Failed to resend code. Please try again.', 'error')

    return redirect(url_for('auth.verify_email'))


# ── FORGOT PASSWORD — Step 1: Enter email ───────────────────────────────────

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = sanitize_string(request.form.get('email', ''), max_length=120).lower()
        user = User.query.filter_by(email=email).first()
        if user:
            try:
                # Invalidate any existing reset tokens
                OtpToken.query.filter_by(user_id=user.id, purpose='reset', used=False).update({'used': True})
                db.session.commit()

                otp_code = generate_otp(user.id, purpose='reset', ttl_minutes=10)
                _send_otp_email(email, otp_code, purpose='reset')
            except Exception as e:
                print(f"--- RESET OTP EMAIL ERROR: {e} ---")
                return render_template('forgot_password.html', error='Failed to send email. Please try again.')
        # Always redirect regardless — prevents email enumeration
        session['reset_email'] = email
        return redirect(url_for('auth.forgot_password_verify'))

    return render_template('forgot_password.html')


# ── FORGOT PASSWORD — Step 2: Verify OTP ────────────────────────────────────

@auth_bp.route('/forgot-password/verify', methods=['GET', 'POST'])
def forgot_password_verify():
    email = session.get('reset_email')
    if not email:
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        otp_entered = request.form.get('otp_code', '').strip().upper()
        user = User.query.filter_by(email=email).first()
        if not user:
            return render_template('forgot_password_verify.html',
                error='No account found for this email.', email=email)
        if not validate_otp(user.id, otp_entered, purpose='reset'):
            return render_template('forgot_password_verify.html',
                error='Invalid or expired code. Please try again.', email=email)
        session['reset_verified'] = True
        return redirect(url_for('auth.forgot_password_reset'))

    return render_template('forgot_password_verify.html', email=email)


# ── FORGOT PASSWORD — Resend OTP ─────────────────────────────────────────────

@auth_bp.route('/forgot-password/resend', methods=['POST'])
def forgot_password_resend():
    email = session.get('reset_email')
    if not email:
        return redirect(url_for('auth.forgot_password'))
    user = User.query.filter_by(email=email).first()
    if user:
        try:
            # Invalidate old tokens
            OtpToken.query.filter_by(user_id=user.id, purpose='reset', used=False).update({'used': True})
            db.session.commit()

            otp_code = generate_otp(user.id, purpose='reset', ttl_minutes=10)
            _send_otp_email(email, otp_code, purpose='reset')
            flash('A new code has been sent to your email.', 'info')
        except Exception as e:
            print(f"--- RESEND RESET OTP ERROR: {e} ---")
            flash('Failed to resend code. Please try again.', 'error')
    else:
        flash('Email not found.', 'error')
    return redirect(url_for('auth.forgot_password_verify'))


# ── FORGOT PASSWORD — Step 3: New password ──────────────────────────────────

@auth_bp.route('/forgot-password/reset', methods=['GET', 'POST'])
def forgot_password_reset():
    email    = session.get('reset_email')
    verified = session.get('reset_verified', False)
    if not email or not verified:
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password     = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        if len(new_password) < 6:
            return render_template('forgot_password_reset.html',
                error='Password must be at least 6 characters.')
        if new_password != confirm_password:
            return render_template('forgot_password_reset.html',
                error='Passwords do not match.')
        user = User.query.filter_by(email=email).first()
        if not user:
            return redirect(url_for('auth.forgot_password'))
        try:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            for key in ['reset_email', 'reset_verified']:
                session.pop(key, None)
            flash('Your password has been reset. Please sign in with your new password.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            print(f"--- PASSWORD RESET DB ERROR: {e} ---")
            db.session.rollback()
            return render_template('forgot_password_reset.html',
                error='Something went wrong. Please try again.')

    return render_template('forgot_password_reset.html')


# ── LOGOUT ───────────────────────────────────────────────────────────────────

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        session.clear()
        return redirect(url_for('main.index', toast='logout'))
    if session.get('role') == 'admin':
        return redirect(url_for('admin.dashboard'))
    if session.get('user_id'):
        return redirect(url_for('customer.shop'))
    return redirect(url_for('main.index'))
