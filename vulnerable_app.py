from flask import Flask, request, render_template, session, redirect, url_for, flash
import sqlite3
import os
import hashlib
import re

app = Flask(__name__)

# Antes: secret_key = os.urandom (cambia en cada ejecución → rompe sesiones)
# Ahora: Uso de variables de entorno
app.secret_key = os.environ.get("APP_SECRET_KEY", "default_dev_secret_change_me")


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def sanitize_input(text):
    """ Sanitiza input básico para evitar XSS en templates """
    return re.sub(r'[<>"]', '', text)


@app.route('/')
def index():
    return 'Welcome to the Secure Task Manager Application!'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = sanitize_input(request.form['username'])
        password = request.form['password']

        conn = get_db_connection()
        hashed_password = hash_password(password)

        # Eliminado todo el comportamiento inseguro asociado a SQL injection detectado
        query = "SELECT * FROM users WHERE username = ? AND password = ?"
        user = conn.execute(query, (username, hashed_password)).fetchone()

        if user:
            session.clear()               # Mitiga Session Fixation
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!')
            return redirect(url_for('login'))

    return render_template("login.html")


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    tasks = conn.execute(
        "SELECT * FROM tasks WHERE user_id = ?", (user_id,)
    ).fetchall()
    conn.close()

    return render_template("dashboard.html", user_id=user_id, tasks=tasks)


@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task = sanitize_input(request.form['task'])
    user_id = session['user_id']

    conn = get_db_connection()
    conn.execute("INSERT INTO tasks (user_id, task) VALUES (?, ?)", (user_id, task))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))


@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Antes: cualquier usuario podía borrar tareas de otros
    # Ahora: Verificación de ownership
    conn = get_db_connection()
    task = conn.execute("SELECT user_id FROM tasks WHERE id = ?", (task_id,)).fetchone()

    if not task or task['user_id'] != user_id:
        flash("Unauthorized action.")
        return redirect(url_for('dashboard'))

    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))


@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return 'Welcome to the ADMIN panel!'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)  # debug=False en producción
