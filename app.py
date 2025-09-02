from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'replace_with_a_long_random_string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
db = SQLAlchemy(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# ==============================
# MODELS
# ==============================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    expenses = db.relationship('Expense', backref='user', lazy=True)


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==============================
# ROUTES
# ==============================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        hashed_pw = generate_password_hash(password, method="sha256")

        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "danger")
            return redirect(url_for("register"))

        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials!", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        category = request.form.get("category")
        amount = float(request.form.get("amount"))
        date = request.form.get("date")

        new_expense = Expense(category=category, amount=amount, date=date, user_id=current_user.id)
        db.session.add(new_expense)
        db.session.commit()
        flash("Expense added!", "success")
        return redirect(url_for("dashboard"))

    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", expenses=expenses)


@app.route("/report")
@login_required
def report():
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    if not expenses:
        flash("No expenses found!", "warning")
        return redirect(url_for("dashboard"))

    data = {"Category": [e.category for e in expenses],
            "Amount": [e.amount for e in expenses]}
    df = pd.DataFrame(data)
    chart_data = df.groupby("Category")["Amount"].sum().to_dict()

    return render_template("report.html", chart_data=chart_data)


# ==============================
# INIT DB COMMAND
# ==============================
@app.cli.command("initdb")
def initdb():
    db.create_all()
    print("Database initialized!")


if __name__ == "__main__":
    with app.app_context():
        if not os.path.exists("finance.db"):
            db.create_all()
    app.run(debug=True)
