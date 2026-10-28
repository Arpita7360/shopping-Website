
import os
import sqlite3
import hashlib
import streamlit as st
from datetime import datetime
from html import escape

# =====================================================
# PAGE CONFIGURATION
# =====================================================
st.set_page_config(
    page_title="ShopEase Online Shopping",
    page_icon="🛍️",
    layout="wide"
)

# Writable temporary database for the Streamlit demo.
# Use a hosted database for permanent account storage.
DB_PATH = os.path.join("/tmp", "shopease.db")


# =====================================================
# DATABASE
# =====================================================
def get_connection():
    return sqlite3.connect(DB_PATH, timeout=30)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                items TEXT NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


def hash_password(password):
    # Demo only; use Argon2 or bcrypt for a production website.
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_user(name, email, password):
    try:
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO users_v2
                (name, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                name.strip(),
                email.strip().lower(),
                hash_password(password),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "This email is already registered."
    except sqlite3.Error:
        return False, "Database error. Please try again."


def login_user(email, password):
    with get_connection() as conn:
        return conn.execute("""
            SELECT name, email
            FROM users_v2
            WHERE email = ? AND password_hash = ?
        """, (
            email.strip().lower(),
            hash_password(password)
        )).fetchone()


def save_order(email, items, total):
    item_text = "\n".join(
        f"{item['name']} x {item['quantity']}" for item in items
    )
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO orders_v2
            (email, items, total, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            email, item_text, total, "Demo order placed",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()


def get_orders(email):
    with get_connection() as conn:
        return conn.execute("""
            SELECT id, items, total, status, created_at
            FROM orders_v2
            WHERE email = ?
            ORDER BY id DESC
        """, (email,)).fetchall()


init_db()


# =====================================================
# SESSION STATE
# =====================================================
defaults = {
    "page": "Home",
    "user": None,
    "cart": {},
    "wishlist": [],
    "ratings": {},
    "last_order": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =====================================================
# STYLING
# =====================================================
st.markdown("""
<style>
.stApp {
    background: #08090d;
    color: white;
}
[data-testid="stSidebar"] {
    background: #11131b;
    border-right: 1px solid #292d3b;
}
[data-testid="stHeader"] {
    background: #08090d;
}
h1, h2, h3, h4, p, label, li, span {
    color: white;
}
div.stButton > button {
    background: linear-gradient(90deg, #ff416c, #7c4dff);
    color: white;
    border: none;
    border-radius: 9px;
    font-weight: 600;
    min-height: 40px;
}
div.stButton > button:hover {
    border: 1px solid white;
    color: white;
}
.hero {
    background: linear-gradient(120deg, #29104c, #14233f, #40152e);
    padding: 30px;
    border: 1px solid #483564;
    border-radius: 16px;
    margin-bottom: 20px;
}
.hero p {
    color: #e4e5f3;
}
.price {
    color: #43e6a3;
    font-size: 19px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# PRODUCT CATALOG
# =====================================================
products = []


def add_product(category, subcategory, name, price, image, description):
    if not image.startswith(("https://", "http://")):
        image = (
            f"https://images.unsplash.com/{image}"
            "?auto=format&fit=crop&w=700&q=80"
        )

    products.append({
        "id": len(products) + 1,
        "category": category,
        "subcategory": subcategory,
        "name": name,
        "price": float(price),
        "image": image,
        "description": description
    })


# Fashion
fashion = [
    ("Men", "Men's Shirt", 799, "photo-1596755094514-f87e34085b2c"),
    ("Men", "Men's T-Shirt", 399, "photo-1521572163474-6864f9cf17ab"),
    ("Men", "Men's Jeans", 999, "photo-1542272604-787c3835535d"),
    ("Men", "Men's Jacket", 1499, "photo-1551028719-00167b16eac5"),
    ("Men", "Men's Kurta", 899, "photo-1598033129183-c4f50c736f10"),
    ("Men", "Men's Blazer", 1999, "photo-1591047139829-d91aecb6caea"),
    ("Women", "Women's Kurti", 699, "photo-1583391733956-6c78276477e7"),
    ("Women", "Women's Jeans", 999, "photo-1541099649105-f69ad21f3246"),
    ("Women", "Crop Top", 449, "photo-1503342217505-b0a15ec3261c"),
    ("Women", "Bodycon Dress", 1199, "photo-1539008835657-9e8e9680c956"),
    ("Women", "Saree", 1499, "photo-1610030469983-98e550d6193c"),
    ("Women", "Lehenga", 2499, "photo-1583391733956-6c78276477e7"),
    ("Women", "Anarkali Gown", 1899, "photo-1595777457583-95e059d581b8")
]

for group, name, price, image in fashion:
    add_product("Fashion", group, name, price, image, f"{name} for everyday and special occasions.")


# Mobiles
mobiles = [
    ("Samsung", "Samsung Galaxy Phone", 18999, "photo-1511707171634-5f897ff02aa9"),
    ("Vivo", "Vivo Smartphone", 14999, "photo-1598327105666-5b89351aff97"),
    ("Oppo", "Oppo Smartphone", 15999, "photo-1511707171634-5f897ff02aa9"),
    ("Realme", "Realme Smartphone", 12999, "photo-1598327105666-5b89351aff97"),
    ("iPhone", "Apple iPhone", 59999, "photo-1592899677977-9c10ca588bbd"),
    ("Motorola", "Motorola Smartphone", 16999, "photo-1511707171634-5f897ff02aa9")
]

for brand, name, price, image in mobiles:
    add_product("Mobiles", brand, name, price, image, f"{brand} smartphone. Verify model specifications before buying.")


# Electronics
electronics = [
    ("Laptop", 45999, "photo-1496181133206-80ce9b88a853"),
    ("Monitor", 11999, "photo-1527443224154-c4a3942d3acf"),
    ("Printer", 7999, "photo-1612815154858-60aa4c59eaa6"),
    ("Projector", 18999, "photo-1574717024653-61fd2cf4d44d")
]

for name, price, image in electronics:
    add_product("Electronics", name, name, price, image, f"{name} for home, office or study.")


# Accessories
accessories = [
    ("Men's Watch", 1299, "photo-1524592094714-0f0654e20314"),
    ("Women's Watch", 1599, "photo-1523275335684-37898b6baf30"),
    ("Sunglasses", 699, "photo-1511499767150-a48a237f0083"),
    ("Earrings", 399, "photo-1535632066927-ab7c9ab60908"),
    ("Keychain", 149, "photo-1617038220319-276d3cfab638"),
    ("Necklace Set", 999, "photo-1599643478518-a784e5dc4c8f"),
    ("Rings", 499, "photo-1605100804763-247f67b3557e")
]

for name, price, image in accessories:
    add_product("Accessories", name, name, price, image, f"{name} for your collection.")


# Toys
toys = [
    ("Teddy Bear", 499, "photo-1559454403-b8fb88521f11"),
    ("Toy Car", 299, "photo-1594787318286-3d835c1d207f"),
    ("Building Blocks", 599, "photo-1587654780291-39c9404d746b"),
    ("Doll", 699, "photo-1560961911-ba7ef651a56c"),
    ("Toy Train", 799, "photo-1516627145497-ae6968895b74"),
    ("Puzzle Game", 349, "photo-1606503153255-59d8b8b821f4"),
    ("Remote Control Car", 1299, "photo-1594787318286-3d835c1d207f"),
    ("Robot Toy", 999, "photo-1535378620166-273708d44e4c"),
    ("Basketball", 499, "photo-1519861531473-9200262188bf"),
    ("Stuffed Animal", 449, "photo-1559454403-b8fb88521f11")
]

for name, price, image in toys:
    add_product("Toys", name, name, price, image, f"{name} for play and gifting.")


# Food and healthcare
food_items = [
    ("Almonds (Badam)", 499, "https://images.unsplash.com/photo-1508061253366-f7da158b6d46?auto=format&fit=crop&w=700&q=80"),
    ("Cashew Nuts (Kaju)", 599, "https://images.unsplash.com/photo-1505576633757-0ac1084af824?auto=format&fit=crop&w=700&q=80"),
    ("Pistachios (Pista)", 549, "https://images.unsplash.com/photo-1511497584788-876760111969?auto=format&fit=crop&w=700&q=80"),
    ("Walnuts (Akhrot)", 499, "https://images.unsplash.com/photo-1508061253366-f7da158b6d46?auto=format&fit=crop&w=700&q=80"),
    ("Dates (Khajoor)", 349, "https://images.unsplash.com/photo-1559181567-c3190ca9959b?auto=format&fit=crop&w=700&q=80"),
    ("Dark Chocolate", 249, "https://cdn.gutekueche.de/media/article/72988/conv/schokolade-default.jpg"),
    ("Milk Chocolate", 199, "https://resources.koha.net/images/2026/March/23/0a4b309d-10f6-4675-bbdc-30fd4348c113.webp?q=90&r=fill&w=1200")
]

for name, price, image in food_items:
    add_product("Food & Healthcare", "Food", name, price, image, f"{name} product.")

seed_items = [
    ("Chia Seeds", 199),
    ("Flax Seeds (Alsi)", 149),
    ("Pumpkin Seeds", 249),
    ("Sunflower Seeds", 179),
    ("Sesame Seeds (Til)", 129),
    ("Watermelon Seeds", 199),
    ("Basil Seeds (Sabja)", 149),
    ("Hemp Seeds", 299)
]

seed_image = "https://buynutslane.com/cdn/shop/files/SEED_MIX_5.jpg?v=1724921656&width=1200"

for name, price in seed_items:
    add_product("Food & Healthcare", "Seeds", name, price, seed_image, f"{name}. Check packaging and allergy information.")


# =====================================================
# HELPERS
# =====================================================
def money(value):
    return f"₹{value:,.2f}"


def get_product(product_id):
    return next((p for p in products if p["id"] == product_id), None)


def add_to_cart(product_id):
    st.session_state.cart[product_id] = st.session_state.cart.get(product_id, 0) + 1


def cart_total():
    total = 0
    for product_id, quantity in st.session_state.cart.items():
        product = get_product(product_id)
        if product:
            total += product["price"] * quantity
    return total


def rating_info(product_id):
    ratings = st.session_state.ratings.get(product_id, [])
    if not ratings:
        return "☆☆☆☆☆", "No ratings"
    avg = sum(ratings) / len(ratings)
    return "★" * round(avg) + "☆" * (5 - round(avg)), f"{avg:.1f}/5"


# =====================================================
# SIDEBAR NAVIGATION
# =====================================================
pages = [
    "Home", "Login", "Create Account", "Shop All",
    "Fashion", "Mobiles", "Electronics", "Accessories",
    "Toys", "Food & Healthcare", "Wishlist", "Cart",
    "My Orders", "Account"
]

with st.sidebar:
    st.markdown("# 🛍️ ShopEase")
    st.caption("Your everyday shopping destination")

    selected_page = st.selectbox(
        "Navigate",
        pages,
        index=pages.index(st.session_state.page)
        if st.session_state.page in pages else 0
    )
    st.session_state.page = selected_page

    st.divider()
    st.write(f"🛒 Cart items: {sum(st.session_state.cart.values())}")

    if st.session_state.user:
        st.success(f"Welcome, {st.session_state.user['name']}")
        if st.button("Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = "Home"
            st.rerun()


page = st.session_state.page


# =====================================================
# HOME PAGE
# =====================================================
if page == "Home":
    st.markdown("""
    <div class="hero">
        <h1>Welcome to ShopEase 🛍️</h1>
        <p>Your one-stop destination for fashion, mobiles, electronics, toys and more.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Products", len(products))
    col2.metric("Categories", 6)
    col3.metric("Cart Items", sum(st.session_state.cart.values()))

    if st.session_state.user:
        st.success(f"Welcome back, {st.session_state.user['name']}!")

    st.subheader("Welcome! What would you like to do?")

    left, right = st.columns(2)

    with left:
        st.markdown("### 🔐 Already have an account?")
        st.write("Log in to continue shopping and view your orders.")
        if st.button("Login", key="home_login", use_container_width=True):
            st.session_state.page = "Login"
            st.rerun()

    with right:
        st.markdown("### ✨ New to ShopEase?")
        st.write("Create an account to get started.")
        if st.button("Create Account", key="home_register", use_container_width=True):
            st.session_state.page = "Create Account"
            st.rerun()

    st.markdown("---")
    st.subheader("Shop by Category")

    category_images = {
        "Fashion": "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=700&q=80",
        "Mobiles": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=700&q=80",
        "Electronics": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=700&q=80",
        "Accessories": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=700&q=80",
        "Toys": "https://images.unsplash.com/photo-1559454403-b8fb88521f11?auto=format&fit=crop&w=700&q=80",
        "Food & Healthcare": seed_image
    }

    cols = st.columns(3)
    for i, (category, image) in enumerate(category_images.items()):
        with cols[i % 3]:
            st.image(image, use_container_width=True)
            if st.button(f"Explore {category}", key=f"home_{category}", use_container_width=True):
                st.session_state.page = category
                st.rerun()


# =====================================================
# LOGIN PAGE
# =====================================================
elif page == "Login":
    st.markdown("""
    <div class="hero">
        <h1>🔐 Login to ShopEase</h1>
        <p>Welcome back! Enter your account details to continue shopping.</p>
    </div>
    """, unsafe_allow_html=True)

    _, center, _ = st.columns([1, 2, 1])

    with center:
        with st.form("login_page_form"):
            email = st.text_input("Email Address", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if not email.strip() or not password:
                    st.error("Please enter your email and password.")
                else:
                    try:
                        user = login_user(email, password)
                        if user:
                            st.session_state.user = {
                                "name": user[0],
                                "email": user[1]
                            }
                            st.session_state.page = "Shop All"
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Incorrect email or password.")
                    except sqlite3.Error:
                        st.error("Unable to access the database. Please try again.")

        st.write("Don't have an account?")
        if st.button("Create a New Account", use_container_width=True):
            st.session_state.page = "Create Account"
            st.rerun()

        if st.button("← Back to Home", use_container_width=True):
            st.session_state.page = "Home"
            st.rerun()


# =====================================================
# CREATE ACCOUNT PAGE
# =====================================================
elif page == "Create Account":
    st.markdown("""
    <div class="hero">
        <h1>✨ Create Your ShopEase Account</h1>
        <p>Register to start exploring our products.</p>
    </div>
    """, unsafe_allow_html=True)

    _, center, _ = st.columns([1, 2, 1])

    with center:
        with st.form("create_account_form"):
            name = st.text_input("Full Name", placeholder="Enter your name")
            email = st.text_input("Email Address", placeholder="Enter your email")
            password = st.text_input("Create Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")

            submitted = st.form_submit_button("Create Account", use_container_width=True)

            if submitted:
                if not name.strip() or not email.strip() or not password:
                    st.error("Please fill in all fields.")
                elif "@" not in email or "." not in email.split("@")[-1]:
                    st.error("Please enter a valid email address.")
                elif len(password) < 6:
                    st.error("Password must contain at least 6 characters.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                else:
                    ok, message = register_user(name, email, password)
                    if ok:
                        st.success(message)
                        st.session_state.page = "Login"
                        st.info("Please log in with your new account.")
                    else:
                        st.error(message)

        if st.button("Already have an account? Login", use_container_width=True):
            st.session_state.page = "Login"
            st.rerun()

        if st.button("← Back to Home", use_container_width=True):
            st.session_state.page = "Home"
            st.rerun()


# =====================================================
# SHOP PAGES
# =====================================================
elif page in [
    "Shop All", "Fashion", "Mobiles", "Electronics",
    "Accessories", "Toys", "Food & Healthcare"
]:
    st.title(f"🛍️ {page}")

    search = st.text_input("🔎 Search products", placeholder="Search by product name...")
    c1, c2 = st.columns(2)

    with c1:
        max_price = st.slider("Maximum price (₹)", 100, 100000, 100000, step=100)

    with c2:
        sorting = st.selectbox(
            "Sort by",
            ["Recommended", "Price: Low to High", "Price: High to Low", "Name"]
        )

    shown = products[:]
    if page != "Shop All":
        shown = [p for p in shown if p["category"] == page]

    if search.strip():
        term = search.strip().lower()
        shown = [
            p for p in shown
            if term in p["name"].lower()
            or term in p["subcategory"].lower()
            or term in p["category"].lower()
        ]

    shown = [p for p in shown if p["price"] <= max_price]

    if page == "Fashion":
        gender = st.radio("Fashion", ["All", "Men", "Women"], horizontal=True)
        if gender != "All":
            shown = [p for p in shown if p["subcategory"] == gender]

    if page == "Mobiles":
        brands = ["All"] + sorted({p["subcategory"] for p in shown})
        brand = st.selectbox("Mobile brand", brands)
        if brand != "All":
            shown = [p for p in shown if p["subcategory"] == brand]

    if page == "Food & Healthcare":
        kind = st.radio("Product type", ["All", "Food", "Seeds"], horizontal=True)
        if kind != "All":
            shown = [p for p in shown if p["subcategory"] == kind]

    if sorting == "Price: Low to High":
        shown.sort(key=lambda p: p["price"])
    elif sorting == "Price: High to Low":
        shown.sort(key=lambda p: p["price"], reverse=True)
    elif sorting == "Name":
        shown.sort(key=lambda p: p["name"].lower())

    st.caption(f"{len(shown)} product(s) found")

    cols = st.columns(4)
    for i, product in enumerate(shown):
        with cols[i % 4]:
            with st.container(border=True):
                st.image(product["image"], use_container_width=True)
                st.markdown(f"**{escape(product['name'])}**")
                st.markdown(
                    f"<div class='price'>{money(product['price'])}</div>",
                    unsafe_allow_html=True
                )
                stars, rating_text = rating_info(product["id"])
                st.caption(f"{stars} {rating_text}")
                st.caption(product["description"])

                with st.popover("⭐ Rate Product", use_container_width=True):
                    rating = st.select_slider(
                        "Your rating",
                        options=[1, 2, 3, 4, 5],
                        value=5,
                        key=f"rating_{product['id']}"
                    )
                    if st.button("Submit Rating", key=f"rate_{product['id']}"):
                        st.session_state.ratings.setdefault(product["id"], []).append(rating)
                        st.success("Rating saved for this session.")

                a, b = st.columns(2)
                with a:
                    if st.button("🛒 Add", key=f"add_{product['id']}", use_container_width=True):
                        add_to_cart(product["id"])
                        st.toast("Added to cart!")

                with b:
                    saved = product["id"] in st.session_state.wishlist
                    label = "❤️ Saved" if saved else "♡ Wishlist"
                    if st.button(label, key=f"wish_{product['id']}", use_container_width=True):
                        if saved:
                            st.session_state.wishlist.remove(product["id"])
                        else:
                            st.session_state.wishlist.append(product["id"])
                        st.rerun()


# =====================================================
# WISHLIST PAGE
# =====================================================
elif page == "Wishlist":
    st.title("❤️ My Wishlist")

    saved_products = [
        get_product(pid) for pid in st.session_state.wishlist
        if get_product(pid)
    ]

    if not saved_products:
        st.info("Your wishlist is empty.")
    else:
        for product in saved_products:
            with st.container(border=True):
                a, b, c = st.columns([1, 3, 1])
                with a:
                    st.image(product["image"], use_container_width=True)
                with b:
                    st.subheader(product["name"])
                    st.write(money(product["price"]))
                    st.caption(product["description"])
                with c:
                    if st.button("Add to Cart", key=f"wishlist_add_{product['id']}"):
                        add_to_cart(product["id"])
                        st.toast("Added to cart.")
                    if st.button("Remove", key=f"wishlist_remove_{product['id']}"):
                        st.session_state.wishlist.remove(product["id"])
                        st.rerun()


# =====================================================
# CART AND CHECKOUT PAGE
# =====================================================
elif page == "Cart":
    st.title("🛒 Shopping Cart")

    if not st.session_state.cart:
        st.info("Your cart is empty. Browse the shop to add products.")
    else:
        for product_id in list(st.session_state.cart.keys()):
            product = get_product(product_id)
            if not product:
                continue

            quantity = st.session_state.cart[product_id]
            with st.container(border=True):
                a, b, c = st.columns([1, 3, 2])
                with a:
                    st.image(product["image"], use_container_width=True)
                with b:
                    st.subheader(product["name"])
                    st.write("Price:", money(product["price"]))
                    st.write("Subtotal:", money(product["price"] * quantity))
                with c:
                    new_quantity = st.number_input(
                        "Quantity",
                        min_value=0,
                        max_value=99,
                        value=quantity,
                        key=f"qty_{product_id}"
                    )
                    if new_quantity != quantity:
                        if new_quantity == 0:
                            st.session_state.cart.pop(product_id, None)
                        else:
                            st.session_state.cart[product_id] = new_quantity
                        st.rerun()

        total = cart_total()
        st.divider()
        st.subheader(f"Total: {money(total)}")

        st.subheader("Checkout Details")
        with st.form("checkout_form"):
            customer_name = st.text_input(
                "Full Name",
                value=st.session_state.user["name"]
                if st.session_state.user else ""
            )
            address = st.text_area("Delivery Address")
            phone = st.text_input("Phone Number")
            payment = st.selectbox(
                "Payment Method",
                ["Cash on Delivery (Demo)", "UPI (Demo)", "Card (Demo)"]
            )

            place_order = st.form_submit_button(
                "Place Demo Order", use_container_width=True
            )

            if place_order:
                if not st.session_state.user:
                    st.error("Please log in before placing an order.")
                elif not customer_name.strip() or not address.strip() or not phone.strip():
                    st.error("Please complete all delivery details.")
                elif len(phone.strip()) < 10:
                    st.error("Please enter a valid phone number.")
                else:
                    order_items = []
                    for pid, qty in st.session_state.cart.items():
                        item = get_product(pid)
                        if item:
                            order_items.append({
                                "name": item["name"],
                                "quantity": qty
                            })

                    try:
                        save_order(
                            st.session_state.user["email"],
                            order_items,
                            total
                        )
                        st.session_state.last_order = {
                            "name": customer_name.strip(),
                            "total": total,
                            "payment": payment
                        }
                        st.session_state.cart = {}
                        st.success("Demo order placed successfully!")
                        st.info("No real payment was processed.")
                        st.rerun()
                    except sqlite3.Error:
                        st.error("Could not save the order. Please try again.")

    if st.session_state.last_order:
        st.divider()
        st.subheader("Latest Demo Order")
        st.write("Customer:", st.session_state.last_order["name"])
        st.write("Total:", money(st.session_state.last_order["total"]))
        st.write("Payment:", st.session_state.last_order["payment"])


# =====================================================
# ORDER HISTORY PAGE
# =====================================================
elif page == "My Orders":
    st.title("📦 My Orders")

    if not st.session_state.user:
        st.warning("Please log in to view your orders.")
        if st.button("Go to Login"):
            st.session_state.page = "Login"
            st.rerun()
    else:
        try:
            orders = get_orders(st.session_state.user["email"])
            if not orders:
                st.info("No orders found yet.")
            else:
                for order in orders:
                    order_id, items, total, status, created_at = order
                    with st.expander(f"Order #{order_id} — {money(total)}"):
                        st.write("Date:", created_at)
                        st.write("Status:", status)
                        st.code(items)
        except sqlite3.Error:
            st.error("Unable to load orders. Please try again.")


# =====================================================
# ACCOUNT PAGE
# =====================================================
elif page == "Account":
    st.title("👤 My Account")

    if st.session_state.user:
        st.success("You are logged in.")
        st.write("Name:", st.session_state.user["name"])
        st.write("Email:", st.session_state.user["email"])
        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.page = "Home"
            st.rerun()
    else:
        st.info("Please log in or create an account.")
        a, b = st.columns(2)
        with a:
            if st.button("Login", use_container_width=True):
                st.session_state.page = "Login"
                st.rerun()
        with b:
            if st.button("Create Account", use_container_width=True):
                st.session_state.page = "Create Account"
                st.rerun()


# =====================================================
# FOOTER
# =====================================================
st.divider()
st.markdown(
    "<p style='text-align:center;color:#aab0c0;'>"
    "© ShopEase | Educational E-commerce Demo"
    "</p>",
    unsafe_allow_html=True
)
