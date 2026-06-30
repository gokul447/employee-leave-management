from flask import Flask, render_template, request, redirect, session
import os
import psycopg2
from urllib.parse import urlparse
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secretkey"

# -------------------------------
# Database Connection
# -------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")

url = urlparse(DATABASE_URL)

conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

# -------------------------------
# Ensure Admin Exists
# -------------------------------
cur = conn.cursor()
cur.execute("SELECT * FROM users WHERE role='admin'")
admin = cur.fetchone()

if not admin:
    hashed_admin_password = generate_password_hash("admin123")
    cur.execute(
        "INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,%s)",
        ('Admin', 'admin@test.com', hashed_admin_password, 'admin')
    )
    conn.commit()

cur.close()

# -------------------------------
# Home
# -------------------------------
@app.route('/')
def index():
    return render_template('index.html')

# -------------------------------
# Register
# -------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')

            hashed_password = generate_password_hash(password)

            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
                (name, email, hashed_password)
            )
            conn.commit()
            cur.close()

            return redirect('/login')

        except Exception as e:
            conn.rollback()
            return f"Error: {e}"

    return render_template('register.html')

# -------------------------------
# Login
# -------------------------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['role'] = user[4]

            if user[4] == 'admin':
                return redirect('/admin')

            return redirect('/dashboard')

    return render_template('login.html')

# -------------------------------
# Logout
# -------------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# -------------------------------
# Dashboard (Employee)
# -------------------------------
@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect('/login')

    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM leaves WHERE user_id=%s",
        (session.get('user_id'),)
    )
    leaves = cur.fetchall()
    cur.close()

    return render_template('dashboard.html', leaves=leaves)

# -------------------------------
# Apply Leave
# -------------------------------
@app.route('/apply', methods=['GET','POST'])
def apply():
    if not session.get('user_id'):
        return redirect('/login')

    if request.method == 'POST':
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')
        reason = request.form.get('reason')

        cur = conn.cursor()
        cur.execute(
            "INSERT INTO leaves(user_id,from_date,to_date,reason) VALUES(%s,%s,%s,%s)",
            (session.get('user_id'), from_date, to_date, reason)
        )
        conn.commit()
        cur.close()

        return redirect('/dashboard')

    return render_template('apply_leave.html')

# -------------------------------
# Admin Dashboard
# -------------------------------
@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return "Access Denied"

    cur = conn.cursor()
    cur.execute("""
        SELECT leaves.id, users.name, leaves.from_date,
               leaves.to_date, leaves.reason, leaves.status
        FROM leaves
        JOIN users ON leaves.user_id = users.id
    """)
    data = cur.fetchall()
    cur.close()

    return render_template('admin_dashboard.html', leaves=data)

# -------------------------------
# Approve / Reject
# -------------------------------
@app.route('/update/<int:id>/<status>')
def update_leave(id, status):
    if session.get('role') != 'admin':
        return "Access Denied"

    cur = conn.cursor()
    cur.execute("UPDATE leaves SET status=%s WHERE id=%s", (status, id))
    conn.commit()
    cur.close()

    return redirect('/admin')