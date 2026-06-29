from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
import config

app = Flask(__name__)
app.secret_key = "secretkey"

app.config['MYSQL_HOST'] = config.MYSQL_HOST
app.config['MYSQL_USER'] = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.MYSQL_DB

mysql = MySQL(app)

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

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
                    (name,email,password))
        mysql.connection.commit()
        cur.close()
        return redirect('/login')
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s",
                    (email,password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['user_id'] = user[0]
            session['role'] = user[4]
            if user[4] == 'admin':
                return redirect('/admin')
            return redirect('/dashboard')
    return render_template('login.html')

# Employee Dashboard
@app.route('/dashboard')
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM leaves WHERE user_id=%s",(session['user_id'],))
    data = cur.fetchall()
    cur.close()
    return render_template('dashboard.html', leaves=data)

# Apply Leave
@app.route('/apply', methods=['GET','POST'])
def apply():
    if request.method == 'POST':
        from_date = request.form['from_date']
        to_date = request.form['to_date']
        reason = request.form['reason']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO leaves(user_id,from_date,to_date,reason) VALUES(%s,%s,%s,%s)",
                    (session['user_id'],from_date,to_date,reason))
        mysql.connection.commit()
        cur.close()
        return redirect('/dashboard')
    return render_template('apply_leave.html')

# Admin Dashboard
@app.route('/admin')
def admin():
    cur = mysql.connection.cursor()
    cur.execute("SELECT leaves.id, users.name, from_date, to_date, reason, status FROM leaves JOIN users ON leaves.user_id=users.id")
    data = cur.fetchall()
    cur.close()
    return render_template('admin_dashboard.html', leaves=data)

# Approve / Reject
@app.route('/update/<int:id>/<status>')
def update(id,status):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE leaves SET status=%s WHERE id=%s",(status,id))
    mysql.connection.commit()
    cur.close()
    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True)