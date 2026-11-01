from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "smartshopsecret"


# =========================
# DATABASE CONNECTION
# =========================
def get_db():
    conn = sqlite3.connect("shop.db")
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# CREATE TABLES & INSERT PRODUCTS
# =========================
def init_db():
    conn = sqlite3.connect("shop.db")
    c = conn.cursor()

    # USERS TABLE
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # PRODUCTS TABLE
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price INTEGER,
            image TEXT
              description TEXT
        )
    """)

    # CART TABLE
    c.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER
        )
    """)

    # Order table
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_name TEXT,
        price INTEGER,
        quantity INTEGER,
        total INTEGER
    )
""")

    # Insert products only if table is empty
    existing = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]

    if existing == 0:
        products = [
            ("Laptop", 50000, "images/Laptop.jpg"),
            ("Mobile", 20000, "images/Mobile.jpg"),
            ("Headphones", 2000, "images/Headphones.jpg"),
            ("Smart Watch", 3000, "images/Smart Watch.jpg"),
            ("Keyboard", 1500, "images/Keyboard.jpg"),
            ("Mouse", 800, "images/Mouse.jpg"),
            ("Camera", 45000, "images/Camera.jpg"),
            ("Tablet", 25000, "images/Tablet.jpg"),
            ("Smart TV",35000,"images/SmartTV.jpg"),
            ("Bluetooth Speaker",2500,"images/BluetoothSpeaker.jpg"),
            ("Power Bank",1500,"images/PowerBank.jpg"),
            ("Wireless Earbuds",3500,"images/WirelessEarbuds.jpg"),
            ("Printer",8000,"images/Printer.jpg"),
        ]
        c.executemany("INSERT INTO products (name, price, image) VALUES (?, ?, ?)", products)

    conn.commit()
    conn.close()


# =========================
# HOME
# =========================
@app.route("/")
def home():
    return render_template("home.html")


# =========================
# PRODUCTS
# =========================
@app.route("/products")
def products():
    conn = get_db()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template("products.html", products=products)


# =========================
# ADD TO CART
# =========================
@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    conn = get_db()
    c = conn.cursor()

    item = c.execute(
        "SELECT * FROM cart WHERE user_id=? AND product_id=?",
        (user_id, product_id)
    ).fetchone()

    if item:
        c.execute(
            "UPDATE cart SET quantity = quantity + 1 WHERE user_id=? AND product_id=?",
            (user_id, product_id)
        )
    else:
        c.execute(
            "INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)",
            (user_id, product_id, 1)
        )

    conn.commit()
    conn.close()

    return redirect("/cart")

@app.route("/product/<int:id>")
def product_detail(id):
    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()
    conn.close()

    return render_template("product_detail.html", product=product)


@app.route('/admin', methods=['GET', 'POST'])
def admin():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "1234":
            return redirect('/dashboard')

    return render_template('admin_login.html')

@app.route('/dashboard')
def dashboard():

    conn = sqlite3.connect('shop.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM orders")
    orders = c.fetchall()

    conn.close()

    return render_template('admin_dashboard.html', orders=orders)



# =========================
# INCREASE QUANTITY
# =========================
@app.route("/increase/<int:product_id>")
def increase(product_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    conn.execute(
        "UPDATE cart SET quantity = quantity + 1 WHERE user_id=? AND product_id=?",
        (session["user_id"], product_id)
    )
    conn.commit()
    conn.close()

    return redirect("/cart")


# =========================
# DECREASE QUANTITY
# =========================
@app.route("/decrease/<int:product_id>")
def decrease(product_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    item = c.execute(
        "SELECT quantity FROM cart WHERE user_id=? AND product_id=?",
        (session["user_id"], product_id)
    ).fetchone()

    if item and item["quantity"] > 1:
        c.execute(
            "UPDATE cart SET quantity = quantity - 1 WHERE user_id=? AND product_id=?",
            (session["user_id"], product_id)
        )
    else:
        c.execute(
            "DELETE FROM cart WHERE user_id=? AND product_id=?",
            (session["user_id"], product_id)
        )

    conn.commit()
    conn.close()

    return redirect("/cart")


# =========================
# REMOVE ITEM
# =========================
@app.route("/remove_from_cart/<int:product_id>")
def remove_from_cart(product_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    conn.execute(
        "DELETE FROM cart WHERE user_id=? AND product_id=?",
        (session["user_id"], product_id)
    )
    conn.commit()
    conn.close()

    return redirect("/cart")


# =========================
# VIEW CART
# =========================
@app.route('/cart')
def cart():

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()

    items = conn.execute("""
        SELECT products.id, products.name, products.price, products.image, cart.quantity
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id = ?
    """, (session['user_id'],)).fetchall()

    cart_items = []
    total = 0

    for item in items:
        subtotal = item["price"] * item["quantity"]
        total += subtotal

        cart_items.append({
            "id": item["id"],
            "name": item["name"],
            "price": item["price"],
            "image": item["image"],
            "quantity": item["quantity"],
            "subtotal": subtotal
        })

    conn.close()

    return render_template("cart.html",
                           items=cart_items,
                           total=total)


# =========================
# CHECKOUT
# =========================
@app.route("/checkout")
def checkout():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    conn = get_db()
    c = conn.cursor()

    # Get cart items
    items = c.execute("""
        SELECT products.name, products.price, cart.quantity
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id = ?
    """, (user_id,)).fetchall()

    if not items:
        return redirect("/cart")

    grand_total = 0

    for item in items:
        name = item["name"]
        price = item["price"]
        quantity = item["quantity"]
        total = price * quantity
        grand_total += total

        c.execute("""
            INSERT INTO orders (user_id, product_name, price, quantity, total)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, price, quantity, total))

    # Clear cart after order
    c.execute("DELETE FROM cart WHERE user_id=?", (user_id,))

    conn.commit()
    conn.close()

    return render_template("order_success.html", total=grand_total)


# =========================
# REGISTER
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        c = conn.cursor()

        existing = c.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        if existing:
            conn.close()
            return render_template("register.html",
                                   message="⚠ Username already exists")

        c.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        conn.close()

        if user:
            session["user_id"] = user["id"]
            return redirect("/products")
        else:
            return render_template("login.html",
                                   message="Invalid Username or Password")

    return render_template("login.html")

@app.route("/orders")
def orders():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    orders = conn.execute("""
        SELECT * FROM orders WHERE user_id=?
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template("orders.html", orders=orders)

# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.pop("user_id", None)   # correct session key
    return redirect("/")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    init_db()
    app.run(debug=True)