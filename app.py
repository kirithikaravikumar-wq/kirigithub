from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
import random

app = Flask(__name__)
app.secret_key = 'canteen_secret_key_2026'

# Admin password
ADMIN_PASSWORD = 'admin123'

# Menu items with prices
MENU_ITEMS = {
    'Masala Dosa': {'price': 50, 'image': 'https://images.pexels.com/photos/5560763/pexels-photo-5560763.jpeg?auto=compress&cs=tinysrgb&w=600'},
    'Idli': {'price': 30, 'image': 'https://images.pexels.com/photos/4331491/pexels-photo-4331491.jpeg?auto=compress&cs=tinysrgb&w=600'},
    'Medu Vada': {'price': 40, 'image': 'https://upload.wikimedia.org/wikipedia/commons/1/1b/Medu_Vada.JPG'},
    'Samosa': {'price': 20, 'image': 'https://upload.wikimedia.org/wikipedia/commons/c/cb/Samosachutney.jpg'},

    # ✅ LOCAL IMAGES (NO images/ folder)
    'Uttapam': {'price': 45, 'image': '/static/utthappam.jpg'},
    'Ven Pongal': {'price': 50, 'image': '/static/venpongal.jpg'},
    'Poori': {'price': 50, 'image': '/static/poori.jpg'},
    'Upma': {'price': 35, 'image': '/static/upma.jpg'},
}


def get_db():
    """Create a new database connection per request."""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="kirithika_09",
        database="canteen"
    )


# ---------------- HOME PAGE ----------------
@app.route('/')
def home():
    return render_template('home.html')


# ---------------- MENU PAGE ----------------
@app.route('/menu')
def menu():
    return render_template('menu.html', menu_items=MENU_ITEMS)


# ---------------- ORDER PAGE ----------------
@app.route('/order')
def order():
    return render_template('order.html', menu_items=MENU_ITEMS)


# ---------------- PLACE ORDER ----------------
@app.route('/place_order', methods=['POST'])
def place_order():
    name = request.form['name']
    food = request.form['food']
    quantity = int(request.form['quantity'])

    # Get price from menu dict
    price = MENU_ITEMS.get(food, {}).get('price', 0)
    total = quantity * price
    token = random.randint(100, 999)
    status = "Preparing"

    db = get_db()
    cursor = db.cursor()
    sql = "INSERT INTO orders (name, food, quantity, total, token, status) VALUES (%s,%s,%s,%s,%s,%s)"
    values = (name, food, quantity, total, token, status)
    cursor.execute(sql, values)
    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('bill', token=token))


# ---------------- BILL PAGE ----------------
@app.route('/bill/<int:token>')
def bill(token):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT name, food, quantity, total, token, status FROM orders WHERE token=%s ORDER BY id DESC LIMIT 1", (token,))
    order = cursor.fetchone()
    cursor.close()
    db.close()

    if order:
        return render_template('bill.html', order=order)
    else:
        flash('Order not found!', 'error')
        return redirect(url_for('home'))


# ---------------- CHECK STATUS PAGE ----------------
@app.route('/check_status', methods=['GET', 'POST'])
def check_status():
    order = None
    if request.method == 'POST':
        token = request.form.get('token', '')
        if token:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT name, food, quantity, total, token, status FROM orders WHERE token=%s ORDER BY id DESC LIMIT 1", (token,))
            order = cursor.fetchone()
            cursor.close()
            db.close()
            if not order:
                flash('No order found with that token number.', 'error')

    return render_template('status.html', order=order)


# ---------------- ADMIN LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Incorrect password!', 'error')
    return render_template('login.html')


# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name, food, quantity, total, token, status FROM orders ORDER BY id DESC")
    orders = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('admin.html', orders=orders)


# ---------------- MARK ORDER READY ----------------
@app.route('/ready/<int:id>')
def ready(id):
    if not session.get('admin'):
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE orders SET status='Ready' WHERE id=%s", (id,))
    db.commit()
    cursor.close()
    db.close()

    flash('Order marked as Ready!', 'success')
    return redirect(url_for('admin'))


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))


# ---------------- RUN SERVER ----------------
if __name__ == '__main__':
    app.run(debug=True)