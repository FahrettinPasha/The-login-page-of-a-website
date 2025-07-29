
📦 Kargo Takip Sistemi - User Management Module
🔍 Overview

This is a full-featured user management system for a Cargo Tracking Web Application. It handles:

    ✅ User Registration

    📧 Email Verification with Code (valid for 10 minutes)

    🔐 Secure Login (via email or username)

    🔁 Password Reset via Email Token (valid for 1 hour)

    📬 Flask-Mail Integration for Gmail

    📅 Date of Birth + T.C. Identity Number + Address + Phone fields

    🛡️ Server-side validations and password strength checking

    Built with Flask, Flask-SQLAlchemy, Flask-Mail, and secure password hashing.

🧰 How to Set Up (Step by Step)
1. Clone the repository

git clone https://github.com/your-username/kargo_sistemi.git
cd kargo_sistemi

2. Install Python dependencies

Use a virtual environment (optional but recommended):

python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt

    If requirements.txt is missing, install manually:

pip install Flask Flask-SQLAlchemy Flask-Mail itsdangerous Werkzeug

3. Configure Gmail for email sending

Make sure:

    You have 2-Step Verification enabled on your Gmail.

    You generate an App Password:
    https://myaccount.google.com/apppasswords

Edit this part in app.py:

app.config['MAIL_USERNAME'] = 'your_gmail@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_app_password'

4. Run the app

python app.py

Open your browser and go to:
http://localhost:5000
🧩 How to Integrate Into Your Own Project

You can integrate the user system into your own Flask app in 3 ways:
Option A: Use it as a separate microservice

Run it on a subdomain like auth.yourdomain.com, then redirect back after login.
Option B: Copy the core logic

Copy these files or parts into your project:

    app.py (especially the routes and models)

    templates/ (HTML pages: register.html, verify.html, login.html, etc.)

    Reuse:

        Kullanici model

        Registration & email verification logic

        Login & session logic

        Password reset functions

Option C: Turn it into a Flask Blueprint

This is better for modular architecture. Extract routes and models into a Blueprint module and import it in your main app.
📌 Important Notes

    The system uses SQLite (site.db) by default. For production, use PostgreSQL or MySQL.

    Email codes and password reset tokens are time-limited for security.

    Passwords are hashed using Werkzeug (PBKDF2).

    Make sure to protect your SECRET_KEY in production.

🧪 Sample Test Users

After registering, check your email for a code. If Gmail blocks it, check spam or use a different mail.
