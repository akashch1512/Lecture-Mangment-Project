🎓 Lecture Management System

A Django 5.2 based web application for managing educational lectures with role-based access for teachers and students.

🚀 Quick Start (Windows)

Run the automated setup script:

python setup.py

What it does:

Creates a virtual environment

Installs dependencies

Runs migrations

Seeds demo data

Starts the development server

🔐 Demo Credentials

Teacher

chetnac / mansia

Students

sanskruti / Robot@1512

kajal / Robot@1512

🛠️ Tech Stack

Framework: Django 5.2.8

Server: Gunicorn

Database: PostgreSQL

Static Files: WhiteNoise

Env Management: python-dotenv

📁 Structure
myapp/        # Application logic
myproject/   # Settings & configuration
templates/   # HTML templates
static/      # Static assets
setup.py     # Automated setup

🚢 Deployment Notes

Set DATABASE_URL using dj-database-url

Run python manage.py collectstatic

Update ALLOWED_HOSTS before production

Disable DEBUG in production

✅ Automated setup · Role-based auth · Production-ready