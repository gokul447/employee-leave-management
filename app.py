from flask import Flask, render_template, request, redirect, session
import os
import psycopg2
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = "secretkey"

# Database connection using Render DATABASE_URL
DATABASE_URL = os.environ.get("DATABASE_URL")

url = urlparse(DATABASE_URL)

conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

# Home
@app.route('/')
def index():
    return render_template('index.html')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
            (name, email, password)
        )
        conn.commit()
        cur.close()
        return redirect('/login')
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cur.fetchone()
        cur.close()

        if user:
            session['user_id'] = user[0]
            session['role'] = user[4]
            return redirect('/dashboard')
    return render_template('login.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM leaves WHERE user_id=%s",
        (session.get('user_id'),)
    )
    leaves = cur.fetchall()
    cur.close()
    return render_template('dashboard.html', leaves=leaves)

# Apply Leave
@app.route('/apply', methods=['GET','POST'])
def apply():
    if request.method == 'POST':
        from_date = request.form['from_date']
        to_date = request.form['to_date']
        reason = request.form['reason']

        cur = conn.cursor()
        cur.execute(
            "INSERT INTO leaves(user_id,from_date,to_date,reason) VALUES(%s,%s,%s,%s)",
            (session.get('user_id'), from_date, to_date, reason)
        )
        conn.commit()
        cur.close()
        return redirect('/dashboard')
    return render_template('apply_leave.html')

if __name__ == '__main__':
    app.run(debug=True)