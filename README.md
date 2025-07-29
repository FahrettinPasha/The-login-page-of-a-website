🚀 The Login Page of a Website — Easy to Use, Easy to Integrate!

This project provides a basic but secure login and registration system using HTML, CSS, JavaScript (frontend) and Python Flask (backend). It is designed to be simple, beginner-friendly, and customizable.
🧠 What This Project Includes

    ✅ User registration system

    ✅ Email verification during registration

    ✅ Login system with username and password (no verification code required)

    ✅ Secure password hashing

    ✅ Clean and minimal frontend design (no unnecessary animations)

    ✅ File structure optimized for easy understanding and editing

📂 Folder Structure (Explained Like You're 5)

/kargo_sistemi/
│
├── static/               --> CSS, images, and JavaScript files
│   ├── styles.css        --> Basic styles
│   └── favicon.ico       --> Your browser icon
│
├── templates/            --> HTML pages
│   ├── login.html
│   ├── register.html
│   └── home.html
│
├── main.py               --> Main Python backend (Flask app)
├── database.db           --> SQLite database (automatically created)
├── requirements.txt      --> Required Python libraries
└── README.md             --> You're reading it now :)

🛠️ How to Run This Project on Your Own Computer

    Install Python 3
    https://www.python.org/downloads/

    Clone this repository

git clone https://github.com/FahrettinPasha/The-login-page-of-a-website.git
cd The-login-page-of-a-website

Create a virtual environment (optional but recommended)

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install required packages

pip install -r requirements.txt

Run the server

python main.py

Visit
Open your browser and go to:

    http://localhost:5000

🔄 How to Integrate This Project Into Your Own System (Step-by-Step)

If you want to use this project inside your own system, follow these steps:
1. Copy Only What You Need

    Copy the templates/ folder to your own Flask app.

    Copy the static/ folder if you want to keep the same frontend.

    Merge the routes from main.py into your Flask backend. (Only copy the parts you need like register, login, etc.)

2. Database Integration

    This project uses SQLite. If you're using another database (e.g. PostgreSQL or MySQL), you can easily adapt the code.

    Update the database connection and queries as needed.

3. Email Verification Setup

    The send_verification_email() function in main.py uses Python’s smtplib. You can change the SMTP settings to match your provider (e.g. Gmail, Mailgun, etc.).

    Don't forget to allow access in your email account if using Gmail (or use an app password).

4. Customize the Design

    All styles are in static/styles.css, so you can change colors, layout, fonts, etc.

    The HTML is kept simple so you can easily integrate it with your own templates.

5. Test It!

    Before going live, always test registration, login, and email verification flows.

    You can manually view the database using DB tools like DB Browser for SQLite.

📧 Need Help?

If you need help or want to ask questions about this system, feel free to open an issue or contact me via GitHub.
