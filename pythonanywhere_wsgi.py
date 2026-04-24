"""
ETERNO E-Commerce Platform - WSGI Entry Point for PythonAnywhere
This file is used by PythonAnywhere to run the Flask application
Account: loophco
"""
import os
import sys

# Add your project directory to the sys.path
project_home = os.path.expanduser('~/eterno-web')
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set the environment to PythonAnywhere
os.environ['FLASK_CONFIG'] = 'pythonanywhere'

# Set Environment Variables
os.environ['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'eterno_pythonanywhere_secret_2024_change_me')
os.environ['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'loophco@gmail.com')
os.environ['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
os.environ['RECAPTCHA_SITE_KEY'] = os.environ.get('RECAPTCHA_SITE_KEY', '')
os.environ['RECAPTCHA_SECRET_KEY'] = os.environ.get('RECAPTCHA_SECRET_KEY', '')

# Import and create the Flask app
from app import create_app

app = create_app('pythonanywhere')

if __name__ == '__main__':
    app.run()
