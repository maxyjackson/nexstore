import sqlite3
from flask import Flask, render_template_string, request, session, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super_secure_key"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect('store.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS products 
                 (id INTEGER PRIMARY KEY, name TEXT, price REAL, cat TEXT, img TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')

    # Seed products
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        data = [
            (1, 'Ultra Phone', 999, 'Electronics', 'https://picsum.photos/200'),
            (2, 'Pro Laptop', 1500, 'Electronics', 'https://picsum.photos/200'),
            (3, 'Smart Watch', 200, 'Tech', 'https://picsum.photos/200'),
            (4, 'Air Buds', 150, 'Audio', 'https://picsum.photos/200')
        ]
        c.executemany("INSERT INTO products VALUES (?,?,?,?,?)", data)

    conn.commit()
    conn.close()

init_db()

# ---------------- HTML ----------------
html = """
<!DOCTYPE html>
<html>
<head>
<title>NexStore PRO+</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>

<body class="bg-light">

<div class="container mt-4">

<h3>NexStore PRO+</h3>

{% if session.user %}
<p>Welcome, {{ session.user }} | <a href="/logout">Logout</a></p>
{% else %}
<a href="/login">Login</a> | <a href="/register">Register</a>
{% endif %}

<hr>

{% with messages = get_flashed_messages() %}
{% for m in messages %}
<div class="alert alert-info">{{ m }}</div>
{% endfor %}
{% endwith %}

{% if page == 'home' %}
<div class="row">
{% for p in products %}
<div class="col-6 mb-3">
<div class="card p-2">
<img src="{{ p[4] }}">
<b>{{ p[1] }}</b>
${{ p[2] }}
<form method="post" action="/add">
<input type="hidden" name="id" value="{{ p[0] }}">
<button class="btn btn-primary w-100 mt-2">Add</button>
</form>
</div>
</div>
{% endfor %}
</div>

<a href="/cart" class="btn btn-dark">Cart ({{ count }})</a>

{% elif page == 'cart' %}
<h4>Cart</h4>
{% for i in cart %}
<div>{{ i.name }} - ${{ i.price }} x{{ i.qty }}</div>
{% endfor %}
<h5>Total: ${{ total }}</h5>

{% elif page == 'login' %}
<form method="post">
<input name="u" class="form-control mb-2" placeholder="Username">
<input name="p" type="password" class="form-control mb-2" placeholder="Password">
<button class="btn btn-primary w-100">Login</button>
</form>

{% elif page == 'register' %}
<form method="post">
<input name="u" class="form-control mb-2" placeholder="Username">
<input name="p" type="password" class="form-control mb-2" placeholder="Password">
<button class="btn btn-success w-100">Register</button>
</form>
{% endif %}

</div>
</body>
</html>
"""

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    conn = sqlite3.connect('store.db')
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()

    cart = session.get('cart', [])
    count = sum(i['qty'] for i in cart)

    return render_template_string(html, page='home', products=products, count=count)

# ADD TO CART
@app.route("/add", methods=["POST"])
def add():
    pid = int(request.form['id'])

    conn = sqlite3.connect('store.db')
    p = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    conn.close()

    cart = session.get('cart', [])

    for i in cart:
        if i['id'] == pid:
            i['qty'] += 1
            break
    else:
        cart.append({'id': p[0], 'name': p[1], 'price': p[2], 'qty': 1})

    session['cart'] = cart
    flash("Added to cart")
    return redirect("/")

# CART
@app.route("/cart")
def cart():
    cart = session.get('cart', [])
    total = sum(i['price'] * i['qty'] for i in cart)

    return render_template_string(html, page='cart', cart=cart, total=total)

# REGISTER
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        u = request.form['u']
        p = generate_password_hash(request.form['p'])

        conn = sqlite3.connect('store.db')
        try:
            conn.execute("INSERT INTO users VALUES (?,?)", (u,p))
            conn.commit()
            flash("Registered successfully")
            return redirect("/login")
        except:
            flash("User exists")
        conn.close()

    return render_template_string(html, page='register')

# LOGIN
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form['u']
        p = request.form['p']

        conn = sqlite3.connect('store.db')
        user = conn.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
        conn.close()

        if user and check_password_hash(user[1], p):
            session['user'] = u
            flash("Login success")
            return redirect("/")
        else:
            flash("Invalid credentials")

    return render_template_string(html, page='login')

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# RUN
if __name__ == "__main__":
    app.run(debug=True)