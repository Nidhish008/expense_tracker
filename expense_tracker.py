import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
db_path = 'data/expense_tracker.db'

def create_connection():
    return sqlite3.connect(db_path)

def initialize_db():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY,
            date TEXT,
            category TEXT,
            description TEXT,
            amount REAL,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

def add_expense(date, category, description, amount, user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO expenses (date, category, description, amount, user_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (date, category, description, amount, user_id))
    conn.commit()
    conn.close()

def get_expenses(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM expenses WHERE user_id = ?', (user_id,))
    expenses = cursor.fetchall()
    conn.close()
    return expenses

def delete_expense(expense_id, user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses WHERE id = ? AND user_id = ?', (expense_id, user_id))
    conn.commit()
    conn.close()

def add_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    hashed_password = generate_password_hash(password)
    cursor.execute('''
        INSERT INTO users (username, password)
        VALUES (?, ?)
    ''', (username, hashed_password))
    conn.commit()
    conn.close()

def get_user(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))
    return render_template('login.html')
   
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if get_user(username) is None:
            add_user(username, password)
            flash('User registered successfully')
            return redirect(url_for('login'))
        else:
            flash('Username already exists')
            return redirect(url_for('register'))
    return render_template('login.html')

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    expenses = get_expenses(session['user_id'])
    return render_template('index.html', expenses=expenses)

@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    date = request.form['date']
    category = request.form['category']
    description = request.form['description']
    amount = float(request.form['amount'])
    add_expense(date, category, description, amount, session['user_id'])
    return redirect(url_for('home'))

@app.route('/view', methods=['GET'])
def view_expenses():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    expenses = get_expenses(session['user_id'])
    return render_template('viewexpense.html', expenses=expenses)

@app.route('/delete/<int:expense_id>', methods=['POST'])
def delete(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    delete_expense(expense_id, session['user_id'])
    expenses = get_expenses(session['user_id'])
    return render_template('viewexpense.html', expenses=expenses)

@app.route('/calculate')
def calculate_totals():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    expenses = get_expenses(session['user_id'])
    
    total_amount = sum(expense[4] for expense in expenses)

    yearly_expenses = {}
    for expense in expenses:
        year = expense[1][-4:]  
        if year not in yearly_expenses:
            yearly_expenses[year] = 0
        yearly_expenses[year] += expense[4]

    # Calculate monthly expenses
    monthly_expenses = {}
    for expense in expenses:
        year_month = expense[1][3:5] + '-' + expense[1][-4:] 
        if year_month not in monthly_expenses:
            monthly_expenses[year_month] = 0
        monthly_expenses[year_month] += expense[4]

    return render_template('calculatetotals.html', total_amount=total_amount,
                           yearly_expenses=yearly_expenses, monthly_expenses=monthly_expenses)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


if __name__ == "__main__":
    initialize_db()
    app.run(debug=True)
