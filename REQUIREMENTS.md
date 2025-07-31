# ✅ Project Setup Guide (Linux, macOS, Windows)

This guide helps you install everything using just **one terminal command**, no manual setup needed.

---

## 🧰 Requirements

- Python 3.x installed
- Git installed
- Internet connection

---

## 🐧 For Linux and macOS users

Open your terminal and run this:

```bash
git clone https://github.com/FahrettinPasha/The-login-page-of-a-website.git && \
cd The-login-page-of-a-website && \
python3 -m venv venv && \
source venv/bin/activate && \
pip install --upgrade pip && \
pip install flask flask-mail flask-sqlalchemy && \
python3 -c "from app import create_tables; create_tables()" && \
echo "✅ Setup completed! Run with: python app.py"



🪟 For Windows users (PowerShell)

Open PowerShell and run this:

git clone https://github.com/FahrettinPasha/The-login-page-of-a-website.git
cd The-login-page-of-a-website
python -m venv venv
.\venv\Scripts\activate
pip install --upgrade pip
pip install flask flask-mail flask-sqlalchemy
python -c "from app import create_tables; create_tables()"
Write-Host "✅ Setup completed! Run with: python app.py"


