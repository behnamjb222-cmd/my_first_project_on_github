import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

def setup_database():
    conn = sqlite3.connect('store.db')
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT UNIQUE,
        address TEXT
    );""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        price REAL NOT NULL,
        stock INTEGER NOT NULL DEFAULT 0
    );""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        total_amount REAL NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id) ON DELETE RESTRICT
    );""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        product_name TEXT NOT NULL, 
        unit_price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES invoices (invoice_id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products (product_id) ON DELETE RESTRICT
    );""")
    
    conn.commit()
    conn.close()

class Database:
    def __init__(self, db_file="store.db"):
        self.db_file = db_file

    def get_conn(self):
        conn = sqlite3.connect(self.db_file)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def execute_query(self, query, params=(), commit=False):
        try:
            with self.get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                if commit:
                    conn.commit()
                    return cursor.lastrowid
                else:
                    return cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")
            return None if not commit else -1

class CustomerWindow(tk.Toplevel):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.title("مدیریت مشتریان")
        self.geometry("600x400")
        
        frame_form = ttk.Frame(self, padding="10")
        frame_form.pack(fill="x")
        
        ttk.Label(frame_form, text="نام:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = ttk.Entry(frame_form)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(frame_form, text="تلفن:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.phone_entry = ttk.Entry(frame_form)
        self.phone_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(frame_form, text="آدرس:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.address_entry = ttk.Entry(frame_form)
        self.address_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        frame_form.columnconfigure(1, weight=1)
        
        frame_buttons = ttk.Frame(self, padding="10")
        frame_buttons.pack(fill="x")
        
        ttk.Button(frame_buttons, text="افزودن", command=self.add_customer).pack(side="right", padx=5)
        ttk.Button(frame_buttons, text="ویرایش", command=self.update_customer).pack(side="right", padx=5)
        ttk.Button(frame_buttons, text="حذف", command=self.delete_customer).pack(side="right", padx=5)
        ttk.Button(frame_buttons, text="پاک کردن فرم", command=self.clear_fields).pack(side="right", padx=5)
        
        frame_search = ttk.Frame(self, padding="10")
        frame_search.pack(fill="x")
        
        self.search_entry = ttk.Entry(frame_search)
        self.search_entry.pack(side="right", padx=5, fill="x", expand=True)
        ttk.Button(frame_search, text="جستجو", command=self.search_customer).pack(side="right")
        
        self.tree = ttk.Treeview(self, columns=("id", "name", "phone", "address"), show="headings", height=10)
        self.tree.heading("id", text="شناسه")
        self.tree.heading("name", text="نام و نام خانوادگی")
        self.tree.heading("phone", text="شماره تماس")
        self.tree.heading("address", text="آدرس")
        
        self.tree.column("id", width=50)
        self.tree.column("name", width=150)
        self.tree.column("phone", width=100)
        self.tree.column("address", width=250)
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self.on_customer_select)
        
        self.load_customers()

    def load_customers(self, query="SELECT * FROM customers ORDER BY name"):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        rows = self.db.execute_query(query)
        if rows:
            for row in rows:
                self.tree.insert("", "end", values=(row["customer_id"], row["name"], row["phone"], row["address"]))

    def add_customer(self):
        name = self.name_entry.get()
        phone = self.phone_entry.get()
        address = self.address_entry.get()
        
        if not name:
            messagebox.showwarning("خطا", "فیلد نام نمی‌تواند خالی باشد.")
            return
            
        res = self.db.execute_query("INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)",
                                  (name, phone, address), commit=True)
        if res != -1:
            messagebox.showinfo("موفقیت", "مشتری با موفقیت اضافه شد.")
            self.clear_fields()
            self.load_customers()
        
    def update_customer(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("خطا", "لطفاً یک مشتری را برای ویرایش انتخاب کنید.")
            return
            
        customer_id = self.tree.item(selected_item)["values"][0]
        name = self.name_entry.get()
        phone = self.phone_entry.get()
        address = self.address_entry.get()
        
        if not name:
            messagebox.showwarning("خطا", "فیلد نام نمی‌تواند خالی باشد.")
            return
            
        res = self.db.execute_query("UPDATE customers SET name=?, phone=?, address=? WHERE customer_id=?",
                                  (name, phone, address, customer_id), commit=True)
        if res != -1:
            messagebox.showinfo("موفقیت", "مشتری با موفقیت ویرایش شد.")
            self.clear_fields()
            self.load_customers()

    def delete_customer(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("خطا", "لطفاً یک مشتری را برای حذف انتخاب کنید.")
            return
            
        if not messagebox.askyesno("تایید حذف", "آیا از حذف این مشتری مطمئن هستید؟"):
            return
            
        customer_id = self.tree.item(selected_item)["values"][0]
        
        res = self.db.execute_query("DELETE FROM customers WHERE customer_id=?", (customer_id,), commit=True)
        if res != -1:
            messagebox.showinfo("موفقیت", "مشتری با موفقیت حذف شد.")
            self.clear_fields()
            self.load_customers()

    def search_customer(self):
        search_term = self.search_entry.get()
        query = f"SELECT * FROM customers WHERE name LIKE '%{search_term}%' OR phone LIKE '%{search_term}%' ORDER BY name"
        self.load_customers(query)

    def clear_fields(self):
        self.name_entry.delete(0, "end")
        self.phone_entry.delete(0, "end")
        self.address_entry.delete(0, "end")
        self.tree.selection_remove(self.tree.focus())

    def on_customer_select(self, event):
        selected_item = self.tree.focus()
        if not selected_item:
            return
        
        values = self.tree.item(selected_item)["values"]
        self.clear_fields()
        self.name_entry.insert(0, values[1])
        self.phone_entry.insert(0, values[2])
        self.address_entry.insert(0, values[3])

class ProductWindow(tk.Toplevel):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.title("مدیریت کالاها")
        self.geometry("600x400")
        
        frame_form = ttk.Frame(self, padding="10")
        frame_form.pack(fill="x")
        
        ttk.Label(frame_form, text="نام کالا:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = ttk.Entry(frame_form)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(frame_form, text="قیمت واحد:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.price_entry = ttk.Entry(frame_form)
        self.price_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(frame_form, text="موجودی:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.stock_entry = ttk.Entry(frame_form)
        self.stock_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        frame_form.columnconfigure(1, weight=1)
        
        frame_buttons = ttk.Frame(self, padding="10")
        frame_buttons.pack(fill="x")
        
        ttk.Button(frame_buttons, text="افزودن", command=self.add_product).pack(side="right", padx=5)
        ttk.Button(frame_buttons, text="ویرایش", command=self.update_product).pack(side="right", padx=5)
        ttk.Button(frame_buttons, text="حذف", command=self.delete_product).pack(side="right", padx=5)
        ttk.Button(frame_buttons, text="پاک کردن فرم", command=self.clear_fields).pack(side="right", padx=5)
        
        frame_search = ttk.Frame(self, padding="10")
        frame_search.pack(fill="x")
        
        self.search_entry = ttk.Entry(frame_search)
        self.search_entry.pack(side="right", padx=5, fill="x", expand=True)
        ttk.Button(frame_search, text="جستجو", command=self.search_product).pack(side="right")
        
        self.tree = ttk.Treeview(self, columns=("id", "name", "price", "stock"), show="headings", height=10)
        self.tree.heading("id", text="شناسه")
        self.tree.heading("name", text="نام کالا")
        self.tree.heading("price", text="قیمت")
        self.tree.heading("stock", text="موجودی")
        
        self.tree.column("id", width=50)
        self.tree.column("name", width=200)
        self.tree.column("price", width=100)
        self.tree.column("stock", width=100)
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self.on_product_select)
        
        self.load_products()

    def load_products(self, query="SELECT * FROM products ORDER BY name"):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        rows = self.db.execute_query(query)
        if rows:
            for row in rows:
                self.tree.insert("", "end", values=(row["product_id"], row["name"], row["price"], row["stock"]))

    def add_product(self):
        name = self.name_entry.get()
        price = self.price_entry.get()
        stock = self.stock_entry.get()
        
        if not name or not price or not stock:
            messagebox.showwarning("خطا", "تمام فیلدها باید پر شوند.")
            return
            
        try:
            price_val = float(price)
            stock_val = int(stock)
        except ValueError:
            messagebox.showwarning("خطا", "قیمت و موجودی باید عدد باشند.")
            return
            
        res = self.db.execute_query("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
                                  (name, price_val, stock_val), commit=True)
        if res != -1:
            messagebox.showinfo("موفقیت", "کالا با موفقیت اضافه شد.")
            self.clear_fields()
            self.load_products()
        
    def update_product(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("خطا", "لطفاً یک کالا را برای ویرایش انتخاب کنید.")
            return
            
        product_id = self.tree.item(selected_item)["values"][0]
        name = self.name_entry.get()
        price = self.price_entry.get()
        stock = self.stock_entry.get()
        
        if not name or not price or not stock:
            messagebox.showwarning("خطا", "تمام فیلدها باید پر شوند.")
            return
            
        try:
            price_val = float(price)
            stock_val = int(stock)
        except ValueError:
            messagebox.showwarning("خطا", "قیمت و موجودی باید عدد باشند.")
            return

        res = self.db.execute_query("UPDATE products SET name=?, price=?, stock=? WHERE product_id=?",
                                  (name, price_val, stock_val, product_id), commit=True)
        if res != -1:
            messagebox.showinfo("موفقیت", "کالا با موفقیت ویرایش شد.")
            self.clear_fields()
            self.load_products()

    def delete_product(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("خطا", "لطفاً یک کالا را برای حذف انتخاب کنید.")
            return
            
        if not messagebox.askyesno("تایید حذف", "آیا از حذف این کالا مطمئن هستید؟"):
            return
            
        product_id = self.tree.item(selected_item)["values"][0]
        
        res = self.db.execute_query("DELETE FROM products WHERE product_id=?", (product_id,), commit=True)
        if res != -1:
            messagebox.showinfo("موفقیت", "کالا با موفقیت حذف شد.")
            self.clear_fields()
            self.load_products()

    def search_product(self):
        search_term = self.search_entry.get()
        query = f"SELECT * FROM products WHERE name LIKE '%{search_term}%' ORDER BY name"
        self.load_products(query)

    def clear_fields(self):
        self.name_entry.delete(0, "end")
        self.price_entry.delete(0, "end")
        self.stock_entry.delete(0, "end")
        self.tree.selection_remove(self.tree.focus())

    def on_product_select(self, event):
        selected_item = self.tree.focus()
        if not selected_item:
            return
        
        values = self.tree.item(selected_item)["values"]
        self.clear_fields()
        self.name_entry.insert(0, values[1])
        self.price_entry.insert(0, str(values[2]))
        self.stock_entry.insert(0, str(values[3]))

class NewInvoiceWindow(tk.Toplevel):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.cart = {} 
        self.title("ثبت فاکتور جدید")
        self.geometry("800x600")

        frame_top = ttk.Frame(self, padding=10)
        frame_top.pack(fill="x")
        
        ttk.Label(frame_top, text="مشتری:").pack(side="right", padx=5)
        self.customer_combo = ttk.Combobox(frame_top, state="readonly")
        self.customer_combo.pack(side="right", fill="x", expand=True, padx=5)
        
        self.total_label = ttk.Label(frame_top, text="مجموع: 0 تومان", font=("Arial", 12, "bold"))
        self.total_label.pack(side="left", padx=10)

        frame_products = ttk.Frame(self, padding=10)
        frame_products.pack(fill="both", expand=True)
        
        ttk.Label(frame_products, text="لیست کالاها").pack()
        self.product_tree = ttk.Treeview(frame_products, columns=("id", "name", "price", "stock"), show="headings", height=8)
        self.product_tree.heading("id", text="شناسه")
        self.product_tree.heading("name", text="نام کالا")
        self.product_tree.heading("price", text="قیمت")
        self.product_tree.heading("stock", text="موجودی")
        self.product_tree.column("id", width=50)
        self.product_tree.pack(fill="both", expand=True, pady=5)
        
        frame_add = ttk.Frame(frame_products)
        frame_add.pack(fill="x", pady=5)
        ttk.Label(frame_add, text="تعداد:").pack(side="right", padx=5)
        self.quantity_entry = ttk.Entry(frame_add, width=10)
        self.quantity_entry.pack(side="right", padx=5)
        ttk.Button(frame_add, text="افزودن به سبد", command=self.add_to_cart).pack(side="right")

        frame_cart = ttk.Frame(self, padding=10)
        frame_cart.pack(fill="both", expand=True)

        ttk.Label(frame_cart, text="سبد خرید").pack()
        self.cart_tree = ttk.Treeview(frame_cart, columns=("id", "name", "price", "qty", "subtotal"), show="headings", height=8)
        self.cart_tree.heading("id", text="شناسه")
        self.cart_tree.heading("name", text="نام کالا")
        self.cart_tree.heading("price", text="قیمت")
        self.cart_tree.heading("qty", text="تعداد")
        self.cart_tree.heading("subtotal", text="جمع جزء")
        self.cart_tree.column("id", width=50)
        self.cart_tree.pack(fill="both", expand=True, pady=5)
        
        frame_cart_buttons = ttk.Frame(frame_cart)
        frame_cart_buttons.pack(fill="x")
        ttk.Button(frame_cart_buttons, text="حذف از سبد", command=self.remove_from_cart).pack(side="right")
        
        frame_bottom = ttk.Frame(self, padding=10)
        frame_bottom.pack(fill="x")
        ttk.Button(frame_bottom, text="ثبت نهایی فاکتور", command=self.save_invoice).pack(expand=True)
        
        self.load_customers_and_products()

    def load_customers_and_products(self):
        customers = self.db.execute_query("SELECT customer_id, name FROM customers ORDER BY name")
        if customers:
            self.customer_combo["values"] = [f"{c['name']} (ID: {c['customer_id']})" for c in customers]
        
        self.load_products()

    def load_products(self):
        for row in self.product_tree.get_children():
            self.product_tree.delete(row)
        products = self.db.execute_query("SELECT * FROM products WHERE stock > 0 ORDER BY name")
        if products:
            for p in products:
                self.product_tree.insert("", "end", values=(p["product_id"], p["name"], p["price"], p["stock"]))

    def add_to_cart(self):
        selected_item = self.product_tree.focus()
        if not selected_item:
            messagebox.showwarning("خطا", "کالایی انتخاب نشده است.")
            return
            
        try:
            quantity = int(self.quantity_entry.get())
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("خطا", "تعداد باید یک عدد صحیح مثبت باشد.")
            return
            
        product = self.product_tree.item(selected_item)["values"]
        product_id = product[0]
        product_name = product[1]
        unit_price = float(product[2])
        stock = int(product[3])
        
        if quantity > stock:
            messagebox.showwarning("خطا", f"موجودی کالا کافی نیست. (موجودی: {stock})")
            return
        
        if product_id in self.cart:
            self.cart[product_id]["quantity"] += quantity
        else:
            self.cart[product_id] = {
                "name": product_name,
                "price": unit_price,
                "quantity": quantity
            }
            
        self.refresh_cart_tree()
        self.quantity_entry.delete(0, "end")

    def remove_from_cart(self):
        selected_item = self.cart_tree.focus()
        if not selected_item:
            messagebox.showwarning("خطا", "کالایی از سبد خرید انتخاب نشده است.")
            return
        
        product_id = self.cart_tree.item(selected_item)["values"][0]
        
        if product_id in self.cart:
            del self.cart[product_id]
            
        self.refresh_cart_tree()

    def refresh_cart_tree(self):
        for row in self.cart_tree.get_children():
            self.cart_tree.delete(row)
        
        total = 0
        for pid, item in self.cart.items():
            subtotal = item["price"] * item["quantity"]
            self.cart_tree.insert("", "end", values=(pid, item["name"], item["price"], item["quantity"], subtotal))
            total += subtotal
            
        self.total_label.config(text=f"مجموع: {total:,.2f} تومان")
        self.current_total = total

    def save_invoice(self):
        customer_selection = self.customer_combo.get()
        if not customer_selection:
            messagebox.showwarning("خطا", "مشتری انتخاب نشده است.")
            return
            
        if not self.cart:
            messagebox.showwarning("خطا", "سبد خرید خالی است.")
            return
            
        try:
            customer_id = int(customer_selection.split("(ID: ")[1].replace(")", ""))
        except Exception:
            messagebox.showerror("خطا", "خطا در شناسایی مشتری.")
            return
        
        invoice_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_amount = self.current_total
        
        try:
            with self.db.get_conn() as conn:
                cursor = conn.cursor()
                
                cursor.execute("INSERT INTO invoices (customer_id, date, total_amount) VALUES (?, ?, ?)",
                               (customer_id, invoice_date, total_amount))
                invoice_id = cursor.lastrowid
                
                for pid, item in self.cart.items():
                    subtotal = item["price"] * item["quantity"]
                    cursor.execute("""
                        INSERT INTO invoice_items 
                        (invoice_id, product_id, product_name, unit_price, quantity, subtotal) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (invoice_id, pid, item["name"], item["price"], item["quantity"], subtotal))
                    
                    cursor.execute("UPDATE products SET stock = stock - ? WHERE product_id = ?",
                                   (item["quantity"], pid))
                
                conn.commit()
                messagebox.showinfo("موفقیت", f"فاکتور شماره {invoice_id} با موفقیت ثبت شد.")
                self.destroy()
                
        except sqlite3.Error as e:
            messagebox.showerror("خطای دیتابیس", f"خطا در ثبت فاکتور: {e}")

class ViewInvoicesWindow(tk.Toplevel):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.title("مشاهده فاکتورها")
        self.geometry("900x600")
        
        frame_main = ttk.Frame(self, padding=10)
        frame_main.pack(fill="both", expand=True)
        
        frame_main.rowconfigure(1, weight=1)
        frame_main.columnconfigure(0, weight=2)
        frame_main.columnconfigure(1, weight=1)
        
        frame_invoices = ttk.Frame(frame_main, padding=5)
        frame_invoices.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=5)
        
        ttk.Label(frame_invoices, text="لیست فاکتورها").pack()
        
        self.invoice_tree = ttk.Treeview(frame_invoices, columns=("id", "customer", "date", "total"), show="headings")
        self.invoice_tree.heading("id", text="شماره فاکتور")
        self.invoice_tree.heading("customer", text="مشتری")
        self.invoice_tree.heading("date", text="تاریخ")
        self.invoice_tree.heading("total", text="مبلغ کل")
        self.invoice_tree.column("id", width=80)
        self.invoice_tree.column("customer", width=150)
        self.invoice_tree.column("date", width=150)
        self.invoice_tree.column("total", width=100)
        self.invoice_tree.pack(fill="both", expand=True)
        self.invoice_tree.bind("<<TreeviewSelect>>", self.load_invoice_details)

        frame_buttons = ttk.Frame(frame_main)
        frame_buttons.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(frame_buttons, text="حذف فاکتور", command=self.delete_invoice).pack(fill="x")
        
        frame_items = ttk.Frame(frame_main, padding=5)
        frame_items.grid(row=1, column=1, rowspan=2, sticky="nsew", padx=5)

        ttk.Label(frame_items, text="جزئیات اقلام فاکتور").pack()
        self.items_tree = ttk.Treeview(frame_items, columns=("name", "price", "qty", "subtotal"), show="headings")
        self.items_tree.heading("name", text="نام کالا")
        self.items_tree.heading("price", text="قیمت واحد")
        self.items_tree.heading("qty", text="تعداد")
        self.items_tree.heading("subtotal", text="جمع جزء")
        self.items_tree.column("name", width=120)
        self.items_tree.column("price", width=80)
        self.items_tree.column("qty", width=50)
        self.items_tree.column("subtotal", width=80)
        self.items_tree.pack(fill="both", expand=True)
        
        self.load_invoices()

    def load_invoices(self):
        for row in self.invoice_tree.get_children():
            self.invoice_tree.delete(row)
        
        query = """
            SELECT i.invoice_id, c.name, i.date, i.total_amount 
            FROM invoices i
            JOIN customers c ON i.customer_id = c.customer_id
            ORDER BY i.date DESC
        """
        rows = self.db.execute_query(query)
        if rows:
            for row in rows:
                self.invoice_tree.insert("", "end", values=(row["invoice_id"], row["name"], row["date"], f"{row['total_amount']:,.0f}"))

    def load_invoice_details(self, event=None):
        for row in self.items_tree.get_children():
            self.items_tree.delete(row)
            
        selected_item = self.invoice_tree.focus()
        if not selected_item:
            return
            
        invoice_id = self.invoice_tree.item(selected_item)["values"][0]
        
        query = "SELECT product_name, unit_price, quantity, subtotal FROM invoice_items WHERE invoice_id = ?"
        rows = self.db.execute_query(query, (invoice_id,))
        if rows:
            for row in rows:
                self.items_tree.insert("", "end", values=(row["product_name"], row["unit_price"], row["quantity"], row["subtotal"]))

    def delete_invoice(self):
        selected_item = self.invoice_tree.focus()
        if not selected_item:
            messagebox.showwarning("خطا", "لطفاً یک فاکتور را برای حذف انتخاب کنید.")
            return
            
        if not messagebox.askyesno("تایید حذف", "آیا از حذف این فاکتور مطمئن هستید؟\n(موجودی کالاها بازگردانده خواهد شد)"):
            return
            
        invoice_id = self.invoice_tree.item(selected_item)["values"][0]
        
        try:
            with self.db.get_conn() as conn:
                cursor = conn.cursor()
                
                items_to_restore = cursor.execute("SELECT product_id, quantity FROM invoice_items WHERE invoice_id = ?", (invoice_id,)).fetchall()
                
                for item in items_to_restore:
                    cursor.execute("UPDATE products SET stock = stock + ? WHERE product_id = ?", (item["quantity"], item["product_id"]))
                
                cursor.execute("DELETE FROM invoices WHERE invoice_id = ?", (invoice_id,))
                
                conn.commit()
                messagebox.showinfo("موفقیت", "فاکتور با موفقیت حذف شد و موجودی کالاها بروزرسانی شد.")
                self.load_invoices()
                for row in self.items_tree.get_children():
                    self.items_tree.delete(row)
                    
        except sqlite3.Error as e:
            messagebox.showerror("خطای دیتابیس", f"خطا در حذف فاکتور: {e}")

class ReportsWindow(tk.Toplevel):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.title("گزارش‌ها")
        self.geometry("800x600")
        
        frame_controls = ttk.Frame(self, padding=10)
        frame_controls.pack(fill="x")

        self.report_list = [
            "1. مجموع فروش هر کالا (تعداد)",
            "2. کالاها با فروش بیشتر از 10 عدد",
            "3. مجموع خرید هر مشتری (مبلغ)",
            "4. مشتریان با خرید بالای 500",
            "5. فاکتورهای با مبلغ بالای 1000",
            "6. کالاها با فروش کمتر از 5 عدد",
            "7. پرفروش‌ترین کالا (مبلغ)",
            "8. بهترین مشتریان (م مبلغ)",
            "9. کالاهای با موجودی کمتر از 5",
            "10. فروش کالا در ماه خاص (مثال: 2024-10)",
            "11. مشتریان فعال در ماه خاص (مثال: 2024-10)",
            "12. فاکتورهای با بیش از 5 قلم کالا",
            "13. کالاهای فروخته شده کمتر از 3 بار",
            "14. مجموع خرید هر مشتری (تعداد)",
            "15. مشتریان با بیش از 3 فاکتور",
            "16. کالاها با فروش بیش از 500 (مبلغ)",
            "17. خرید مشتری در 3 ماه گذشته",
            "18. کالاها با موجودی بین 5 تا 10",
            "19. مشتریان بدون خرید در ماه گذشته",
            "20. مجموع فروش روزانه هر کالا (تعداد)"
        ]
        
        self.report_combo = ttk.Combobox(frame_controls, values=self.report_list, state="readonly", width=60)
        self.report_combo.pack(side="right", fill="x", expand=True, padx=5)
        self.report_combo.current(0)
        
        self.param_entry = ttk.Entry(frame_controls, width=15)
        self.param_entry.pack(side="right", padx=5)
        self.param_entry.insert(0, "YYYY-MM")
        
        ttk.Button(frame_controls, text="اجرای گزارش", command=self.run_report).pack(side="right")
        
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tree = ttk.Treeview(self.tree_frame, show="headings")
        
        self.v_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.h_scroll = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        
        self.v_scroll.pack(side="right", fill="y")
        self.h_scroll.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)
        
    def setup_tree_columns(self, columns):
        if hasattr(self, 'tree'):
            self.tree.destroy()
            
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings")
        self.tree.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
            
        self.tree.pack(fill="both", expand=True)
        self.v_scroll.config(command=self.tree.yview)
        self.h_scroll.config(command=self.tree.xview)

    def run_report(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        selected_report = self.report_combo.get()
        param = self.param_entry.get()
        query = ""
        params = ()
        columns = []

        try:
            if selected_report.startswith("1."):
                columns = ["نام کالا", "مجموع تعداد فروش"]
                query = """
                    SELECT p.name, SUM(ii.quantity) as total_quantity
                    FROM invoice_items ii
                    JOIN products p ON ii.product_id = p.product_id
                    GROUP BY p.name
                    ORDER BY total_quantity DESC
                """
            elif selected_report.startswith("2."):
                columns = ["نام کالا", "مجموع تعداد فروش"]
                query = """
                    SELECT p.name, SUM(ii.quantity) as total_quantity
                    FROM invoice_items ii
                    JOIN products p ON ii.product_id = p.product_id
                    GROUP BY p.name
                    HAVING total_quantity > 10
                    ORDER BY total_quantity DESC
                """
            elif selected_report.startswith("3."):
                columns = ["نام مشتری", "مجموع مبلغ خرید"]
                query = """
                    SELECT c.name, SUM(i.total_amount) as total_spent
                    FROM invoices i
                    JOIN customers c ON i.customer_id = c.customer_id
                    GROUP BY c.name
                    ORDER BY total_spent DESC
                """
            elif selected_report.startswith("4."):
                columns = ["نام مشتری", "مجموع مبلغ خرید"]
                query = """
                    SELECT c.name, SUM(i.total_amount) as total_spent
                    FROM invoices i
                    JOIN customers c ON i.customer_id = c.customer_id
                    GROUP BY c.name
                    HAVING total_spent > 500
                    ORDER BY total_spent DESC
                """
            elif selected_report.startswith("5."):
                columns = ["شماره فاکتور", "نام مشتری", "مبلغ کل"]
                query = """
                    SELECT i.invoice_id, c.name, i.total_amount
                    FROM invoices i
                    JOIN customers c ON i.customer_id = c.customer_id
                    WHERE i.total_amount > 1000
                    ORDER BY i.total_amount DESC
                """
            elif selected_report.startswith("6."):
                columns = ["نام کالا", "مجموع تعداد فروش"]
                query = """
                    SELECT p.name, SUM(ii.quantity) as total_quantity
                    FROM invoice_items ii
                    JOIN products p ON ii.product_id = p.product_id
                    GROUP BY p.name
                    HAVING total_quantity < 5
                    ORDER BY total_quantity ASC
                """
            elif selected_report.startswith("7."):
                columns = ["نام کالا", "مجموع مبلغ فروش"]
                query = """
                    SELECT ii.product_name, SUM(ii.subtotal) as total_revenue
                    FROM invoice_items ii
                    GROUP BY ii.product_name
                    ORDER BY total_revenue DESC
                    LIMIT 5
                """
            elif selected_report.startswith("8."):
                columns = ["نام مشتری", "مجموع مبلغ خرید"]
                query = """
                    SELECT c.name, SUM(i.total_amount) as total_spent
                    FROM invoices i
                    JOIN customers c ON i.customer_id = c.customer_id
                    GROUP BY c.name
                    ORDER BY total_spent DESC
                    LIMIT 5
                """
            elif selected_report.startswith("9."):
                columns = ["نام کالا", "موجودی"]
                query = "SELECT name, stock FROM products WHERE stock < 5 ORDER BY stock ASC"
            
            elif selected_report.startswith("10."):
                columns = ["نام کالا", "تعداد فروش در ماه"]
                query = """
                    SELECT ii.product_name, SUM(ii.quantity) as total_quantity
                    FROM invoice_items ii
                    JOIN invoices i ON ii.invoice_id = i.invoice_id
                    WHERE STRFTIME('%Y-%m', i.date) = ?
                    GROUP BY ii.product_name
                    ORDER BY total_quantity DESC
                """
                params = (param,)

            elif selected_report.startswith("11."):
                columns = ["نام مشتری", "مجموع خرید در ماه"]
                query = """
                    SELECT c.name, SUM(i.total_amount) as total_spent
                    FROM invoices i
                    JOIN customers c ON i.customer_id = c.customer_id
                    WHERE STRFTIME('%Y-%m', i.date) = ?
                    GROUP BY c.name
                    ORDER BY total_spent DESC
                """
                params = (param,)

            elif selected_report.startswith("12."):
                columns = ["شماره فاکتور", "تعداد اقلام"]
                query = """
                    SELECT invoice_id, COUNT(item_id) as item_count
                    FROM invoice_items
                    GROUP BY invoice_id
                    HAVING item_count > 5
                    ORDER BY item_count DESC
                """
            elif selected_report.startswith("13."):
                columns = ["نام کالا", "تعداد دفعات فروش"]
                query = """
                    SELECT product_name, COUNT(DISTINCT invoice_id) as sale_count
                    FROM invoice_items
                    GROUP BY product_name
                    HAVING sale_count < 3
                    ORDER BY sale_count ASC
                """
            elif selected_report.startswith("14."):
                columns = ["نام مشتری", "مجموع تعداد خرید"]
                query = """
                    SELECT c.name, SUM(ii.quantity) as total_items
                    FROM invoices i
                    JOIN customers c ON i.customer_id = c.customer_id
                    JOIN invoice_items ii ON i.invoice_id = ii.invoice_id
                    GROUP BY c.name
                    ORDER BY total_items DESC
                """
            elif selected_report.startswith("15."):
                columns = ["نام مشتری", "تعداد فاکتور"]
                query = """
                    SELECT c.name, COUNT(i.invoice_id) as invoice_count
                    FROM invoices i
                    JOIN customers c ON i.customer_id = c.customer_id
                    GROUP BY c.name
                    HAVING invoice_count > 3
                    ORDER BY invoice_count DESC
                """
            elif selected_report.startswith("16."):
                columns = ["نام کالا", "مجموع مبلغ فروش"]
                query = """
                    SELECT product_name, SUM(subtotal) as total_revenue
                    FROM invoice_items
                    GROUP BY product_name
                    HAVING total_revenue > 500
                    ORDER BY total_revenue DESC
                """
            elif selected_report.startswith("17."):
                columns = ["نام مشتری", "مجموع خرید ۳ ماه اخیر"]
                date_3_months_ago = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")
                query = """
                    SELECT c.name, SUM(i.total_amount) as total_spent
                    FROM invoices i
                    JOIN customers c ON i.customer_id = c.customer_id
                    WHERE i.date >= ?
                    GROUP BY c.name
                    ORDER BY total_spent DESC
                """
                params = (date_3_months_ago,)
            
            elif selected_report.startswith("18."):
                columns = ["نام کالا", "موجودی"]
                query = "SELECT name, stock FROM products WHERE stock BETWEEN 5 AND 10 ORDER BY stock ASC"

            elif selected_report.startswith("19."):
                date_1_month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                columns = ["نام مشتری"]
                query = """
                    SELECT name
                    FROM customers
                    WHERE customer_id NOT IN (
                        SELECT DISTINCT customer_id FROM invoices WHERE date >= ?
                    )
                """
                params = (date_1_month_ago,)
            
            elif selected_report.startswith("20."):
                columns = ["تاریخ", "نام کالا", "تعداد فروش روزانه"]
                query = """
                    SELECT STRFTIME('%Y-%m-%d', i.date) as sale_date, ii.product_name, SUM(ii.quantity) as daily_quantity
                    FROM invoice_items ii
                    JOIN invoices i ON ii.invoice_id = i.invoice_id
                    GROUP BY sale_date, ii.product_name
                    ORDER BY sale_date DESC, daily_quantity DESC
                """

            self.setup_tree_columns(columns)
            rows = self.db.execute_query(query, params)
            if rows:
                for row in rows:
                    self.tree.insert("", "end", values=tuple(row))
            elif rows is not None:
                messagebox.showinfo("گزارش", "داده‌ای برای این گزارش یافت نشد.")

        except Exception as e:
            messagebox.showerror("خطا", f"خطا در اجرای گزارش: {e}")

class App(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.title("سیستم مدیریت فروشگاه")
        self.geometry("400x500")
        
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(expand=True, fill="both")
        
        ttk.Label(main_frame, text="به سیستم مدیریت فروشگاه خوش آمدید", font=("Arial", 14, "bold")).pack(pady=10)
        
        btn_style = ttk.Style()
        btn_style.configure("TButton", font=("Arial", 12), padding=10)
        
        ttk.Button(main_frame, text="مدیریت مشتریان", command=self.open_customer_window, style="TButton").pack(fill="x", pady=5)
        ttk.Button(main_frame, text="مدیریت کالاها", command=self.open_product_window, style="TButton").pack(fill="x", pady=5)
        ttk.Button(main_frame, text="ثبت فاکتور جدید", command=self.open_new_invoice_window, style="TButton").pack(fill="x", pady=5)
        ttk.Button(main_frame, text="مشاهده فاکتورها", command=self.open_view_invoices_window, style="TButton").pack(fill="x", pady=5)
        ttk.Button(main_frame, text="گزارش‌ها", command=self.open_reports_window, style="TButton").pack(fill="x", pady=5)

    def open_window(self, WindowClass):
        try:
            win = WindowClass(self, self.db)
            win.transient(self)
            win.grab_set()
            self.wait_window(win)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open window: {e}")

    def open_customer_window(self):
        self.open_window(CustomerWindow)

    def open_product_window(self):
        self.open_window(ProductWindow)

    def open_new_invoice_window(self):
        self.open_window(NewInvoiceWindow)

    def open_view_invoices_window(self):
        self.open_window(ViewInvoicesWindow)

    def open_reports_window(self):
        self.open_window(ReportsWindow)


if __name__ == "__main__":
    setup_database()
    db_instance = Database()
    app = App(db_instance)
    app.mainloop()