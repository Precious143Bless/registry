# ✝ Church Registry System

A web-based parish recordkeeping system built with **Python Django + MySQL + Bootstrap 5**.
Manages church members, sacramental records, and pledge payments in one place.

---

## ⚡ Quick Start

### First Time Setup
> Run this **once** when you first download the project.

1. Make sure **Python 3.10+** and **XAMPP (MySQL)** are installed
2. Create a database named `church_registry` in phpMyAdmin
3. Double-click **`setup.bat`**

`setup.bat` will automatically:
- Create the virtual environment
- Install all required packages
- Set up all database tables
- Ask you to create your admin login

---

### Daily Use
> Run this **every time** you want to open the system.

Double-click **`start.bat`**

`start.bat` will automatically:
- Activate the virtual environment
- Apply any new migrations
- Start the web server

Then open your browser and go to:
```
http://127.0.0.1:8000
```

---

## 📋 Features

- **Members** — Register and manage complete member profiles
- **Sacraments** — Track Baptism, Confirmation, First Holy Communion, Marriage, and Last Rites
- **Pledges** — Record financial pledges with payment history and running balance
- **Print** — Generate printable certificates for any sacramental record
- **Search** — Find any record instantly by name
- **Secure** — Login required to access any part of the system

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3 + Django 4.2 |
| Database | MySQL (via XAMPP) |
| Frontend | HTML + Bootstrap 5 |
| Version Control | Git + GitHub |

---

## 📁 Project Structure

```
church_registry/
├── setup.bat              ← Run this FIRST (one-time setup)
├── start.bat              ← Run this DAILY to launch the system
├── manage.py
├── requirements.txt
├── church_registry.sql    ← Database structure reference
├── church_registry/       ← Django project settings
└── registry/              ← Main application (models, views, templates)
```

---

## ⚙ Default Login

After running `setup.bat`, use the username and password you created during setup.
To create another admin account:
```cmd
venv\Scripts\activate
python manage.py createsuperuser
```
