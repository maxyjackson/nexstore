import sqlite3
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout

# ================= DATABASE =================
conn = sqlite3.connect("garden_pro.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price REAL
)
""")
conn.commit()

# Seed data (Malawi produce)
cursor.execute("SELECT COUNT(*) FROM products")
if cursor.fetchone()[0] == 0:
    items = [
        ("Bananas", 1200),
        ("Maize (Chimanga)", 6500),
        ("Beans (Nyemba)", 5000),
        ("Tomatoes", 1800),
        ("Cassava", 3000),
        ("Sweet Potatoes", 2500),
        ("Onions", 2200),
        ("Rice", 7000)
    ]
    cursor.executemany("INSERT INTO products (name, price) VALUES (?,?)", items)
    conn.commit()

# ================= CART =================
cart = {}

# ================= SCREENS =================
class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_ui()

    def load_ui(self):
        layout = BoxLayout(orientation="vertical")

        title = Label(text="🌿 Raw Garden Carts PRO", size_hint=(1, 0.1))
        layout.add_widget(title)

        btn_cart = Button(text="🛒 View Cart", size_hint=(1, 0.1))
        btn_cart.bind(on_press=lambda x: self.manager.current = "cart")
        layout.add_widget(btn_cart)

        btn_admin = Button(text="🧑‍🌾 Admin Panel", size_hint=(1, 0.1))
        btn_admin.bind(on_press=lambda x: self.manager.current = "admin")
        layout.add_widget(btn_admin)

        scroll = ScrollView()
        grid = GridLayout(cols=1, size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()

        for p in products:
            box = BoxLayout(size_hint_y=None, height=50)

            box.add_widget(Label(text=f"{p[1]} - MWK {p[2]}"))

            btn = Button(text="Add", size_hint_x=0.3)
            btn.bind(on_press=lambda x, pid=p[0]: self.add_to_cart(pid))

            box.add_widget(btn)
            grid.add_widget(box)

        scroll.add_widget(grid)
        layout.add_widget(scroll)

        self.add_widget(layout)

    def add_to_cart(self, pid):
        cursor.execute("SELECT * FROM products WHERE id=?", (pid,))
        p = cursor.fetchone()

        if p:
            if pid in cart:
                cart[pid]["qty"] += 1
            else:
                cart[pid] = {"name": p[1], "price": p[2], "qty": 1}

class CartScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build()

    def build(self):
        layout = BoxLayout(orientation="vertical")

        layout.add_widget(Label(text="🛒 CART"))

        self.items_box = BoxLayout(orientation="vertical")
        self.refresh()

        layout.add_widget(self.items_box)

        self.total_label = Label(text="")
        layout.add_widget(self.total_label)

        btn_checkout = Button(text="Checkout")
        btn_checkout.bind(on_press=self.checkout)
        layout.add_widget(btn_checkout)

        btn_back = Button(text="Back")
        btn_back.bind(on_press=lambda x: self.manager.current = "home")
        layout.add_widget(btn_back)

        self.add_widget(layout)

    def refresh(self):
        self.items_box.clear_widgets()

        total = 0

        for pid, item in cart.items():
            cost = item["price"] * item["qty"]
            total += cost

            row = BoxLayout(size_hint_y=None, height=40)

            row.add_widget(Label(text=f"{item['name']} x{item['qty']}"))

            remove = Button(text="X", size_hint_x=0.3)
            remove.bind(on_press=lambda x, id=pid: self.remove_item(id))

            row.add_widget(remove)
            self.items_box.add_widget(row)

        self.total_label.text = f"Total: MWK {total}"

    def remove_item(self, pid):
        if pid in cart:
            del cart[pid]
        self.refresh()

    def checkout(self, instance):
        cart.clear()
        self.refresh()
        self.total_label.text = "Order placed ✅"

class AdminScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build()

    def build(self):
        layout = BoxLayout(orientation="vertical")

        layout.add_widget(Label(text="🧑‍🌾 ADMIN PANEL"))

        self.name = TextInput(hint_text="Product name")
        self.price = TextInput(hint_text="Price")

        layout.add_widget(self.name)
        layout.add_widget(self.price)

        btn_add = Button(text="Add Product")
        btn_add.bind(on_press=self.add_product)
        layout.add_widget(btn_add)

        btn_back = Button(text="Back")
        btn_back.bind(on_press=lambda x: self.manager.current = "home")
        layout.add_widget(btn_back)

        self.add_widget(layout)

    def add_product(self, instance):
        cursor.execute(
            "INSERT INTO products (name, price) VALUES (?,?)",
            (self.name.text, float(self.price.text))
        )
        conn.commit()

        self.name.text = ""
        self.price.text = ""

# ================= APP =================
class GardenApp(App):
    def build(self):
        sm = ScreenManager()

        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(CartScreen(name="cart"))
        sm.add_widget(AdminScreen(name="admin"))

        return sm

if __name__ == "__main__":
    GardenApp().run()
