# 📊 Personal Finance Tracker  

A **Flask-based web application** to help you manage personal finances with authentication, expense tracking, and reporting features.  

---

## 🚀 Features
- 🔑 User Authentication – Secure login system  
- 📝 Add & Manage Expenses – Track spending by category  
- 📊 Expense Reports – Charts and breakdown by category  
- 📂 SQLite Database – Lightweight and easy to reset  
- ⚡ Proxy & Debug Scripts – Inspect database and reset easily  

---

## 🛠️ Tech Stack
- **Backend**: Flask (Python)  
- **Database**: SQLite + SQLAlchemy  
- **Frontend**: HTML, CSS, Bootstrap  
- **Other Tools**: Jinja2, Flask-Login  

---
Project srtucture



personal-finance-tracker/
│── app.py # Main Flask app
│── reset_db.py # Reset database script
│── inspect_db.py # Inspect database script
│── requirements.txt # Dependencies
│── .gitignore
│── templates/ # HTML templates
│ │── base.html
│ │── index.html
│ │── login.html
│ │── register.html
│ │── dashboard.html
│ │── report.html
│── static/ # CSS, JS, images
│ │── style.css

yaml
Copy code

---

## ⚙️ Installation & Setup

1. Clone the repository:
```bash
git clone https://github.com/Mukesh-Kalva/Personal-Finance-Tracker.git
cd Personal-Finance-Tracker
Create a virtual environment:

bash
Copy code
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate # Mac/Linux
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Initialize the database:

bash
Copy code
python reset_db.py
Run the app:

bash
Copy code
python app.py
Open in browser:

cpp
Copy code
http://127.0.0.1:5000
✅ Future Enhancements
Add income tracking

Export reports (CSV, PDF)

Multi-user dashboard with analytics

## 📂 Project Structure

