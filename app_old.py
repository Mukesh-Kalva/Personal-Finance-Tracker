# Project: Personal Finance Tracker (Advanced)
# Files are delimited with === path === markers so you can copy into your project.

=== requirements.txt ===
flask
flask-login
flask-sqlalchemy
pandas
matplotlib

=== app.py ===
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import pandas as pd
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Init
login_manager = LoginManager(app)
login_manager.login_view = 'login'
db = SQLAlchemy(app)

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    monthly_budget = db.Column(db.Float, default=0.0)
    expenses = db.relationship('Expense', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, pw: str):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw: str) -> bool:
        return check_password_hash(self.password_hash, pw)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    occurred_on = db.Column(db.Date, nullable=False, default=date.today)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# CLI helper to create DB first run
@app.cli.command('initdb')
def initdb():
    db.create_all()
    print('Database initialized.')

# Routes: Auth
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if not username or not password:
            flash('Username and password required', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Routes: App
@app.route('/')
@login_required
def dashboard():
    # Current month range
    today = date.today()
    month_start = today.replace(day=1)
    expenses = Expense.query.filter(Expense.user_id==current_user.id, Expense.occurred_on>=month_start, Expense.occurred_on<=today).order_by(Expense.occurred_on.desc()).all()
    spent = sum(e.amount for e in expenses)
    budget = current_user.monthly_budget or 0.0
    over_budget = budget > 0 and spent > budget
    return render_template('dashboard.html', expenses=expenses, month_spent=spent, budget=budget, over_budget=over_budget)

@app.route('/set-budget', methods=['POST'])
@login_required
def set_budget():
    try:
        current_user.monthly_budget = float(request.form['monthly_budget'])
        db.session.commit()
        flash('Budget updated', 'success')
    except Exception:
        flash('Invalid budget value', 'error')
    return redirect(url_for('dashboard'))

@app.route('/add', methods=['POST'])
@login_required
def add_expense():
    category = request.form['category'].strip() or 'Other'
    amount = float(request.form['amount'])
    occurred_str = request.form.get('occurred_on', '')
    occurred_on = datetime.strptime(occurred_str, '%Y-%m-%d').date() if occurred_str else date.today()
    e = Expense(user_id=current_user.id, category=category, amount=amount, occurred_on=occurred_on)
    db.session.add(e)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    e = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    db.session.delete(e)
    db.session.commit()
    return redirect(url_for('dashboard'))

# Reports
@app.route('/report')
@login_required
def report():
    return render_template('report.html')

@app.route('/api/summary')
@login_required
def api_summary():
    # Params: range=month|year, start=YYYY-MM-DD, end=YYYY-MM-DD
    rng = request.args.get('range', 'month')
    start = request.args.get('start')
    end = request.args.get('end')
    if start and end:
        start_date = datetime.strptime(start, '%Y-%m-%d').date()
        end_date = datetime.strptime(end, '%Y-%m-%d').date()
    else:
        today = date.today()
        if rng == 'year':
            start_date = today.replace(month=1, day=1)
        else:
            start_date = today.replace(day=1)
        end_date = today

    q = Expense.query.filter(Expense.user_id==current_user.id, Expense.occurred_on>=start_date, Expense.occurred_on<=end_date)
    rows = [{'category': e.category, 'amount': float(e.amount), 'occurred_on': e.occurred_on.isoformat()} for e in q]
    if not rows:
        return jsonify({'labels': [], 'values': [], 'total': 0, 'start': start_date.isoformat(), 'end': end_date.isoformat()})

    df = pd.DataFrame(rows)
    summary = df.groupby('category')['amount'].sum().sort_values(ascending=False)
    labels = summary.index.tolist()
    values = [round(float(v), 2) for v in summary.values.tolist()]
    total = round(float(df['amount'].sum()), 2)
    return jsonify({'labels': labels, 'values': values, 'total': total, 'start': start_date.isoformat(), 'end': end_date.isoformat()})

if __name__ == '__main__':
    # Create DB if not exists
    if not os.path.exists('finance.db'):
        with app.app_context():
            db.create_all()
    app.run(debug=True)

=== templates/base.html ===
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}Finance Tracker{% endblock %}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="{{ url_for('static', filename='style.css') }}" rel="stylesheet">
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
  <div class="container-fluid">
    <a class="navbar-brand" href="{{ url_for('dashboard') }}">💰 Finance</a>
    <div class="collapse navbar-collapse">
      <ul class="navbar-nav me-auto mb-2 mb-lg-0">
        {% if current_user.is_authenticated %}
        <li class="nav-item"><a class="nav-link" href="{{ url_for('report') }}">Reports</a></li>
        {% endif %}
      </ul>
      <ul class="navbar-nav">
        {% if current_user.is_authenticated %}
          <li class="nav-item"><span class="navbar-text me-3">Hi, {{ current_user.username }}</span></li>
          <li class="nav-item"><a class="btn btn-outline-light" href="{{ url_for('logout') }}">Logout</a></li>
        {% else %}
          <li class="nav-item"><a class="btn btn-outline-light" href="{{ url_for('login') }}">Login</a></li>
        {% endif %}
      </ul>
    </div>
  </div>
</nav>
<div class="container py-4">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
      {% for category, message in messages %}
        <div class="alert alert-{{ 'danger' if category=='error' else category }}">{{ message }}</div>
      {% endfor %}
    {% endif %}
  {% endwith %}
  {% block content %}{% endblock %}
</div>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</body>
</html>

=== templates/register.html ===
{% extends 'base.html' %}
{% block title %}Register{% endblock %}
{% block content %}
<h2>Create Account</h2>
<form method="post" class="row g-3" autocomplete="off">
  <div class="col-md-6">
    <label class="form-label">Username</label>
    <input class="form-control" name="username" required>
  </div>
  <div class="col-md-6">
    <label class="form-label">Password</label>
    <input type="password" class="form-control" name="password" required>
  </div>
  <div class="col-12">
    <button class="btn btn-primary">Register</button>
    <a href="{{ url_for('login') }}" class="btn btn-link">Have an account? Login</a>
  </div>
</form>
{% endblock %}

=== templates/login.html ===
{% extends 'base.html' %}
{% block title %}Login{% endblock %}
{% block content %}
<h2>Login</h2>
<form method="post" class="row g-3">
  <div class="col-md-6">
    <label class="form-label">Username</label>
    <input class="form-control" name="username" required>
  </div>
  <div class="col-md-6">
    <label class="form-label">Password</label>
    <input type="password" class="form-control" name="password" required>
  </div>
  <div class="col-12">
    <button class="btn btn-primary">Login</button>
    <a href="{{ url_for('register') }}" class="btn btn-link">Register</a>
  </div>
</form>
{% endblock %}

=== templates/dashboard.html ===
{% extends 'base.html' %}
{% block title %}Dashboard{% endblock %}
{% block content %}
<h2>Dashboard</h2>
<form method="post" action="{{ url_for('add_expense') }}" class="row g-3">
  <div class="col-md-4">
    <label class="form-label">Category</label>
    <input class="form-control" name="category" placeholder="Food, Travel, Rent" required>
  </div>
  <div class="col-md-3">
    <label class="form-label">Amount (₹)</label>
    <input type="number" step="0.01" class="form-control" name="amount" required>
  </div>
  <div class="col-md-3">
    <label class="form-label">Date</label>
    <input type="date" class="form-control" name="occurred_on">
  </div>
  <div class="col-md-2 d-flex align-items-end">
    <button class="btn btn-success w-100">Add</button>
  </div>
</form>

<hr>
<form method="post" action="{{ url_for('set_budget') }}" class="row g-3 align-items-end">
  <div class="col-md-3">
    <label class="form-label">Monthly Budget (₹)</label>
    <input type="number" step="0.01" class="form-control" name="monthly_budget" value="{{ '%.2f'|format(budget) }}">
  </div>
  <div class="col-md-2">
    <button class="btn btn-outline-primary">Save Budget</button>
  </div>
  <div class="col-md-7 text-end">
    <span class="badge bg-{{ 'danger' if over_budget else 'secondary' }} p-3 fs-6">This Month Spent: ₹{{ '%.2f'|format(month_spent) }}{% if budget>0 %} / ₹{{ '%.2f'|format(budget) }}{% endif %}</span>
  </div>
</form>

<h4 class="mt-4">Recent Expenses (This Month)</h4>
<table class="table table-striped">
  <thead><tr><th>Date</th><th>Category</th><th class="text-end">Amount (₹)</th><th></th></tr></thead>
  <tbody>
    {% for e in expenses %}
    <tr>
      <td>{{ e.occurred_on.strftime('%Y-%m-%d') }}</td>
      <td>{{ e.category }}</td>
      <td class="text-end">{{ '%.2f'|format(e.amount) }}</td>
      <td class="text-end">
        <form method="post" action="{{ url_for('delete_expense', expense_id=e.id) }}" onsubmit="return confirm('Delete expense?');">
          <button class="btn btn-sm btn-outline-danger">Delete</button>
        </form>
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}

=== templates/report.html ===
{% extends 'base.html' %}
{% block title %}Reports{% endblock %}
{% block content %}
<h2>Reports</h2>
<div class="row g-3 mb-3">
  <div class="col-md-3">
    <label class="form-label">Start</label>
    <input type="date" id="start" class="form-control">
  </div>
  <div class="col-md-3">
    <label class="form-label">End</label>
    <input type="date" id="end" class="form-control">
  </div>
  <div class="col-md-3 d-flex align-items-end">
    <button class="btn btn-primary w-100" onclick="loadSummary()">Apply</button>
  </div>
</div>

<div class="mb-2"><strong>Total:</strong> ₹<span id="total">0</span></div>
<canvas id="pieChart" height="140"></canvas>
<canvas id="barChart" class="mt-4" height="140"></canvas>

<script>
async function loadSummary() {
  const params = new URLSearchParams();
  const start = document.getElementById('start').value;
  const end = document.getElementById('end').value;
  if (start && end) { params.set('start', start); params.set('end', end); }
  const res = await fetch('/api/summary?' + params.toString());
  const data = await res.json();
  document.getElementById('total').textContent = data.total || 0;

  const labels = data.labels || [];
  const values = data.values || [];

  if (window.pieInst) window.pieInst.destroy();
  if (window.barInst) window.barInst.destroy();

  const pieCtx = document.getElementById('pieChart').getContext('2d');
  window.pieInst = new Chart(pieCtx, {
    type: 'pie', data: { labels: labels, datasets: [{ data: values }] }
  });

  const barCtx = document.getElementById('barChart').getContext('2d');
  window.barInst = new Chart(barCtx, {
    type: 'bar', data: { labels: labels, datasets: [{ label: 'Spend (₹)', data: values }] },
    options: { scales: { y: { beginAtZero: true } } }
  });
}

loadSummary();
</script>
{% endblock %}

=== static/style.css ===
body { background: #0f172a0a; }
.navbar-brand { font-weight: 700; }
.table td, .table th { vertical-align: middle; }
.badge.fs-6 { font-weight: 600; }
