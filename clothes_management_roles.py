
import os
import sys
import sqlite3
import hashlib
import calendar
import csv
import subprocess
import tempfile
from datetime import datetime, date, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
from PIL import Image, ImageTk

# ---------- Configuration ----------
DB_FILENAME   = "clothes_management.db"
IMAGE_FOLDER  = "item_images"
LOW_STOCK_QTY = 5   # Threshold for low-stock alert

# ---------- Styling Constants ----------
BG_COLOR    = "#f0f0f0"
HEADER_BG   = "#057cf3"
HEADER_FG   = "white"
BUTTON_BG   = "#3109c0"
BUTTON_FG   = "white"
SUCCESS_BG  = "#27ae60"
WARNING_BG  = "#f39c12"
DANGER_BG   = "#e74c3c"
FRAME_BG    = "white"
TEXT_BG     = "white"
TREE_BG     = "white"
LOW_STOCK_COLOR = "#fff3cd"
OUT_STOCK_COLOR = "#fce8e8"

# ---------- Utility ----------
def hash_password(username, password):
    s = (username + '|' + password).encode('utf-8')
    return hashlib.sha256(s).hexdigest()

def verify_password(username, password, hashed):
    return hash_password(username, password) == hashed

def get_connection():
    return sqlite3.connect(DB_FILENAME)

def generate_item_code(name):
    stamp = datetime.now().strftime("%H%M%S")
    base = ''.join(ch for ch in name if ch.isalnum()).upper()[:4]
    return f"{base}{stamp}"

# ---------- Database ----------
def init_db():
    first_time = not os.path.exists(DB_FILENAME)
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            season TEXT NOT NULL,
            size TEXT,
            color TEXT,
            quantity INTEGER NOT NULL DEFAULT 0,
            purchase_price REAL NOT NULL,
            sale_price REAL NOT NULL,
            image_path TEXT,
            created_at TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            txn_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            txn_date TEXT NOT NULL,
            performed_by TEXT NOT NULL,
            FOREIGN KEY(item_id) REFERENCES items(id)
        )
    """)
    conn.commit()

    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        default_admin = "admin"
        default_pass  = "admin123"
        c.execute("INSERT INTO users (username,password,role,created_at) VALUES (?,?,?,?)",
                  (default_admin, hash_password(default_admin, default_pass),
                   'admin', datetime.now().isoformat()))
        conn.commit()
        print(f"Default admin created – Username: '{default_admin}', Password: '{default_pass}'")

    conn.close()
    if first_time:
        create_sample_data()

def create_sample_data():
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    sample_items = [
        ("BLUSHT001","Blue Shirt","Men","Summer","M","Blue",20,500.0,850.0,now),
        ("REDDRS001","Red Dress","Women","Summer","L","Red",10,800.0,1200.0,now),
        ("KDJKT001","Kids Jacket","Kids","Winter","S","Green",5,900.0,1400.0,now),
        ("WHTTSH001","White T-Shirt","Men","Summer","L","White",3,300.0,550.0,now),
        ("BLKPNT001","Black Pant","Women","Winter","M","Black",0,700.0,1100.0,now),
    ]
    for item in sample_items:
        c.execute("""INSERT OR IGNORE INTO items
            (item_code,name,category,season,size,color,quantity,purchase_price,sale_price,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)""", item)
    conn.commit()

    c.execute("SELECT id FROM items WHERE item_code='BLUSHT001'")
    sid = c.fetchone()[0]
    c.execute("SELECT id FROM items WHERE item_code='REDDRS001'")
    did = c.fetchone()[0]
    c.execute("SELECT id FROM items WHERE item_code='KDJKT001'")
    jid = c.fetchone()[0]

    for txn in [
        (sid,'purchase',20,500.0,10000.0,now,'admin'),
        (sid,'sale',5,850.0,4250.0,now,'admin'),
        (did,'purchase',10,800.0,8000.0,now,'admin'),
        (did,'sale',2,1200.0,2400.0,now,'admin'),
        (jid,'purchase',5,900.0,4500.0,now,'admin'),
    ]:
        c.execute("INSERT INTO transactions VALUES (NULL,?,?,?,?,?,?,?)", txn)
    conn.commit()
    conn.close()

# ---------- Business Logic ----------
def register_user_by_admin(admin_username, username, password, role='staff'):
    if role not in ('admin','staff'):
        role = 'staff'
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username,password,role,created_at) VALUES (?,?,?,?)",
                  (username, hash_password(username, password), role, datetime.now().isoformat()))
        conn.commit()
        return True, "User created successfully."
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    finally:
        conn.close()

def check_login(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT password,role FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if not row:
        return False, None
    stored, role = row
    return (True, role) if verify_password(username, password, stored) else (False, None)

def change_password(username, old_password, new_password):
    ok, _ = check_login(username, old_password)
    if not ok:
        return False, "Old password is incorrect."
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE username=?",
              (hash_password(username, new_password), username))
    conn.commit()
    conn.close()
    return True, "Password changed successfully."

def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id,username,role,created_at FROM users ORDER BY created_at")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_user(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return True, "User deleted successfully."

def add_item(name, category, season, size, color, quantity,
             purchase_price, sale_price, image_path=None, item_code=None):
    if not item_code:
        item_code = generate_item_code(name)
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO items
            (item_code,name,category,season,size,color,quantity,
             purchase_price,sale_price,image_path,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                  (item_code,name,category,season,size,color,quantity,
                   purchase_price,sale_price,image_path,datetime.now().isoformat()))
        conn.commit()
        return True, f"Item '{name}' added successfully."
    except sqlite3.IntegrityError:
        return False, "Item code already exists."
    finally:
        conn.close()

def update_item(item_id, name, category, season, size, color,
                quantity, purchase_price, sale_price, image_path=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""UPDATE items SET name=?,category=?,season=?,size=?,color=?,
                 quantity=?,purchase_price=?,sale_price=?,image_path=?
                 WHERE id=?""",
              (name,category,season,size,color,quantity,
               purchase_price,sale_price,image_path,item_id))
    conn.commit()
    conn.close()
    return True, "Item updated successfully."

def delete_item(item_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT image_path FROM items WHERE id=?", (item_id,))
    row = c.fetchone()
    if row and row[0]:
        try: os.remove(row[0])
        except Exception: pass
    c.execute("DELETE FROM items WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return True, "Item deleted successfully."

def search_items(term=None, category_filter=None, season_filter=None,
                 color_filter=None, size_filter=None):
    conn = get_connection()
    c = conn.cursor()
    query = """SELECT id,item_code,name,category,season,size,color,
               quantity,purchase_price,sale_price,image_path,created_at
               FROM items WHERE 1=1"""
    params = []
    if term:
        query += " AND (name LIKE ? OR item_code LIKE ? OR category LIKE ? OR color LIKE ? OR size LIKE ?)"
        params.extend([f"%{term}%"]*5)
    if category_filter and category_filter != "All":
        query += " AND category=?"; params.append(category_filter)
    if season_filter and season_filter != "All":
        query += " AND season=?"; params.append(season_filter)
    if color_filter and color_filter.strip():
        query += " AND color LIKE ?"; params.append(f"%{color_filter}%")
    if size_filter and size_filter != "All":
        query += " AND size=?"; params.append(size_filter)
    query += " ORDER BY name"
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

def get_stock_summary():
    """Return current stock levels for all items – used in stock report."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT item_code,name,category,season,size,color,
                 quantity,purchase_price,sale_price
                 FROM items ORDER BY quantity ASC""")
    rows = c.fetchall()
    conn.close()
    return rows

def record_transaction(item_id, txn_type, quantity, unit_price, performed_by, txn_date=None):
    txn_date = txn_date or datetime.now().isoformat()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT quantity FROM items WHERE id=?", (item_id,))
    row = c.fetchone()
    if row is None:
        conn.close(); return False, "Item not found."
    current_qty = row[0]
    if txn_type == 'sale' and quantity > current_qty:
        conn.close()
        return False, f"Insufficient stock. Available: {current_qty}"
    new_qty = current_qty + quantity if txn_type == 'purchase' else current_qty - quantity
    total_price = quantity * unit_price
    try:
        c.execute("""INSERT INTO transactions
            (item_id,txn_type,quantity,unit_price,total_price,txn_date,performed_by)
            VALUES (?,?,?,?,?,?,?)""",
                  (item_id,txn_type,quantity,unit_price,total_price,txn_date,performed_by))
        c.execute("UPDATE items SET quantity=? WHERE id=?", (new_qty, item_id))
        conn.commit()
        return True, f"{txn_type.capitalize()} recorded successfully."
    except Exception as e:
        conn.rollback(); return False, f"Error: {str(e)}"
    finally:
        conn.close()

def generate_report(interval='daily', start_date=None, end_date=None):
    conn = get_connection()
    c = conn.cursor()
    query = """SELECT t.id,t.item_id,i.item_code,i.name,t.txn_type,
               t.quantity,t.unit_price,t.total_price,t.txn_date,t.performed_by
               FROM transactions t JOIN items i ON t.item_id=i.id WHERE 1=1"""
    params = []
    today = date.today()

    if interval == 'daily':
        s = datetime(today.year,today.month,today.day)
        e = datetime(today.year,today.month,today.day,23,59,59)
        query += " AND txn_date BETWEEN ? AND ?"; params.extend([s.isoformat(),e.isoformat()])
    elif interval == 'weekly':
        week_start = today - timedelta(days=today.weekday())
        week_end   = week_start + timedelta(days=6)
        s = datetime(week_start.year,week_start.month,week_start.day)
        e = datetime(week_end.year,week_end.month,week_end.day,23,59,59)
        query += " AND txn_date BETWEEN ? AND ?"; params.extend([s.isoformat(),e.isoformat()])
    elif interval == 'monthly':
        s = datetime(today.year,today.month,1)
        last_day = calendar.monthrange(today.year,today.month)[1]
        e = datetime(today.year,today.month,last_day,23,59,59)
        query += " AND txn_date BETWEEN ? AND ?"; params.extend([s.isoformat(),e.isoformat()])
    elif interval == 'yearly':
        s = datetime(today.year,1,1)
        e = datetime(today.year,12,31,23,59,59)
        query += " AND txn_date BETWEEN ? AND ?"; params.extend([s.isoformat(),e.isoformat()])
    elif interval == 'custom':
        if not start_date or not end_date:
            conn.close()
            return {"error":"Start date and end date are required for custom range"}
        s = datetime.combine(start_date, datetime.min.time())
        e = datetime.combine(end_date,   datetime.max.time())
        query += " AND txn_date BETWEEN ? AND ?"; params.extend([s.isoformat(),e.isoformat()])

    query += " ORDER BY t.txn_date"
    c.execute(query, params)
    rows = c.fetchall()

    total_purchases = total_sales = 0.0
    qty_purchased = qty_sold = 0
    per_item = {}

    for row in rows:
        _,_,item_code,name,txn_type,quantity,_,total_price,_,_ = row
        if txn_type == 'purchase':
            total_purchases += total_price; qty_purchased += quantity
        else:
            total_sales += total_price; qty_sold += quantity
        key = f"{item_code} - {name}"
        if key not in per_item:
            per_item[key] = {"purchased":0,"purchase_total":0.0,"sold":0,"sale_total":0.0}
        if txn_type == 'purchase':
            per_item[key]["purchased"] += quantity
            per_item[key]["purchase_total"] += total_price
        else:
            per_item[key]["sold"] += quantity
            per_item[key]["sale_total"] += total_price

    conn.close()
    return {
        "transactions": rows,
        "total_purchases": total_purchases,
        "total_sales": total_sales,
        "qty_purchased": qty_purchased,
        "qty_sold": qty_sold,
        "profit": total_sales - total_purchases,
        "per_item": per_item,
    }

def export_report_csv(report_dict, filename):
    with open(filename,'w',newline='',encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(["Clothes Management System – Report"])
        w.writerow([])
        w.writerow(["Summary"])
        w.writerow(["Total Purchases", f"${report_dict.get('total_purchases',0):.2f}"])
        w.writerow(["Total Sales",     f"${report_dict.get('total_sales',0):.2f}"])
        w.writerow(["Qty Purchased",   report_dict.get('qty_purchased',0)])
        w.writerow(["Qty Sold",        report_dict.get('qty_sold',0)])
        w.writerow(["Profit/Loss",     f"${report_dict.get('profit',0):.2f}"])
        w.writerow([])
        w.writerow(["Per Item Breakdown"])
        w.writerow(["Item","Purchased Qty","Purchased Total","Sold Qty","Sold Total"])
        for item, vals in report_dict.get('per_item',{}).items():
            w.writerow([item,vals.get('purchased',0),
                        f"${vals.get('purchase_total',0):.2f}",
                        vals.get('sold',0),
                        f"${vals.get('sale_total',0):.2f}"])

def export_stock_csv(filename):
    rows = get_stock_summary()
    with open(filename,'w',newline='',encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(["Clothes Management System – Stock Report",
                    datetime.now().strftime("%Y-%m-%d %H:%M")])
        w.writerow([])
        w.writerow(["Code","Name","Category","Season","Size","Color",
                    "Qty","Cost Price","Sale Price","Status"])
        for r in rows:
            code,name,cat,season,sz,col,qty,pp,sp = r
            status = "OUT OF STOCK" if qty == 0 else ("LOW STOCK" if qty <= LOW_STOCK_QTY else "OK")
            w.writerow([code,name,cat,season,sz,col,qty,f"${pp:.2f}",f"${sp:.2f}",status])

def print_text_report(text_content, title="Report"):
    """Print report by writing a temp text file and opening it with the OS default handler."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                         delete=False, encoding='utf-8') as f:
            f.write(text_content)
            tmp = f.name
        if sys.platform.startswith('win'):
            os.startfile(tmp, 'print')
        elif sys.platform == 'darwin':
            subprocess.run(['lpr', tmp])
        else:
            subprocess.run(['lpr', tmp])
        return True, "Sent to printer."
    except Exception as e:
        return False, f"Print failed: {e}"

def build_report_text(report_dict, title="Report"):
    lines = [
        "=" * 60,
        f"  CLOTHES MANAGEMENT SYSTEM – {title.upper()}",
        f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60, "",
        "FINANCIAL SUMMARY",
        f"  Total Sales    : ${report_dict.get('total_sales',0):>10.2f}",
        f"  Total Purchases: ${report_dict.get('total_purchases',0):>10.2f}",
        f"  Net Profit     : ${report_dict.get('profit',0):>10.2f}",
        "",
        "INVENTORY MOVEMENT",
        f"  Qty Sold      : {report_dict.get('qty_sold',0)}",
        f"  Qty Purchased : {report_dict.get('qty_purchased',0)}",
        "",
        "PER ITEM BREAKDOWN",
        f"  {'Item':<35} {'Sold':>6} {'Sale $':>10} {'Bought':>6} {'Buy $':>10}",
        "-" * 75,
    ]
    for item, vals in report_dict.get('per_item',{}).items():
        lines.append(
            f"  {item:<35} {vals.get('sold',0):>6} "
            f"${vals.get('sale_total',0):>9.2f} "
            f"{vals.get('purchased',0):>6} "
            f"${vals.get('purchase_total',0):>9.2f}"
        )
    lines += ["", "=" * 60]
    return "\n".join(lines)

def build_stock_report_text():
    rows = get_stock_summary()
    lines = [
        "=" * 70,
        "  CLOTHES MANAGEMENT SYSTEM – CURRENT STOCK REPORT",
        f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 70, "",
        f"  {'Code':<12} {'Name':<20} {'Cat':<8} {'Size':<5} {'Color':<10} {'Qty':>5}  Status",
        "-" * 70,
    ]
    total = 0
    for r in rows:
        code,name,cat,_,sz,col,qty,_,_ = r
        status = "OUT OF STOCK" if qty == 0 else ("LOW STOCK" if qty <= LOW_STOCK_QTY else "")
        lines.append(f"  {code:<12} {name:<20} {cat:<8} {sz:<5} {col:<10} {qty:>5}  {status}")
        total += qty
    lines += ["", f"  Total items in stock: {total}", "=" * 70]
    return "\n".join(lines)

# ---------- Styled Widget Classes ----------
class StyledButton(tk.Button):
    def __init__(self, parent, **kwargs):
        tk.Button.__init__(self, parent, **kwargs)
        self.configure(bg=BUTTON_BG,fg=BUTTON_FG,relief='raised',
                       padx=10,pady=5,font=('Arial',10))

class SuccessButton(StyledButton):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs); self.configure(bg=SUCCESS_BG)

class DangerButton(StyledButton):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs); self.configure(bg=DANGER_BG)

class WarningButton(StyledButton):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs); self.configure(bg=WARNING_BG)

class StyledFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs); self.configure(bg=FRAME_BG)

class StyledLabelFrame(tk.LabelFrame):
    def __init__(self, parent, **kwargs):
        tk.LabelFrame.__init__(self, parent, **kwargs)
        self.configure(bg=FRAME_BG,fg=HEADER_BG,font=('Arial',11,'bold'))

# ---------- Main Application ----------
class ClothesManagementSystem(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Clothes Management System")
        self.geometry("1280x750")
        self.minsize(1100,650)
        self.configure(bg=BG_COLOR)
        self.active_user = None
        self.active_role = None
        self.selected_item = None
        self.preview_image = None
        Path(IMAGE_FOLDER).mkdir(parents=True, exist_ok=True)
        self.build_ui()
        self.refresh_data()

    # ── UI Construction ──────────────────────────────────────────────────
    def build_ui(self):
        top_bar = tk.Frame(self, bg=HEADER_BG, height=50)
        top_bar.pack(side='top', fill='x')
        top_bar.pack_propagate(False)

        tk.Label(top_bar, text="👕 Clothes Management System",
                 bg=HEADER_BG, fg=HEADER_FG, font=("Helvetica",16,"bold")).pack(side='left',padx=20)

        # Low-stock alert badge (top bar, right side)
        self.alert_label = tk.Label(top_bar, text="", bg=WARNING_BG, fg="white",
                                    font=("Arial",10,"bold"), padx=8, pady=2)
        self.alert_label.pack(side='right', padx=10)

        self.user_label = tk.Label(top_bar, text="Not logged in",
                                   bg=HEADER_BG, fg=HEADER_FG, font=("Arial",10))
        self.user_label.pack(side='right', padx=20)

        tk.Button(top_bar, text="Logout", command=self.logout,
                  bg=DANGER_BG, fg="white", relief='flat').pack(side='right', padx=5)
        tk.Button(top_bar, text="Change Password", command=self.change_password,
                  bg=BUTTON_BG, fg="white", relief='flat').pack(side='right', padx=5)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.login_tab     = self.create_login_tab()
        self.dashboard_tab = self.create_dashboard_tab()
        self.reports_tab   = self.create_reports_tab()
        self.stock_tab     = self.create_stock_tab()
        self.users_tab     = self.create_users_tab()

        self.notebook.add(self.login_tab,     text="🔐 Login")
        self.notebook.add(self.dashboard_tab, text="📊 Dashboard")
        self.notebook.add(self.reports_tab,   text="📈 Reports")
        self.notebook.add(self.stock_tab,     text="📦 Stock Report")
        self.notebook.add(self.users_tab,     text="👥 User Management")

        for i in range(1, 5):
            self.notebook.tab(i, state="disabled")

    # ── Login Tab ─────────────────────────────────────────────────────────
    def create_login_tab(self):
        tab = StyledFrame(self.notebook)
        tab.configure(padx=20, pady=20)

        login_frame = StyledLabelFrame(tab, text="Login")
        login_frame.pack(fill='x', pady=(0,20))

        tk.Label(login_frame, text="Username:", bg=FRAME_BG).grid(row=0,column=0,sticky='w',pady=5,padx=10)
        self.login_username = tk.Entry(login_frame, width=30, font=('Arial',10))
        self.login_username.grid(row=0,column=1,pady=5,padx=(0,10))
        self.login_username.insert(0,"admin")

        tk.Label(login_frame, text="Password:", bg=FRAME_BG).grid(row=1,column=0,sticky='w',pady=5,padx=10)
        self.login_password = tk.Entry(login_frame, show="*", width=30, font=('Arial',10))
        self.login_password.grid(row=1,column=1,pady=5,padx=(0,10))
        self.login_password.insert(0,"admin123")

        SuccessButton(login_frame, text="Login", command=self.login).grid(
            row=2,column=0,columnspan=2,pady=10,padx=10,sticky='we')

        # Default credentials hint
        tk.Label(login_frame,
                 text=" Staff accounts created by admin in User Management tab",
                 bg=FRAME_BG, fg="gray", font=('Arial',9)).grid(
            row=3,column=0,columnspan=2,pady=(0,8))

        return tab

    # ── Dashboard Tab ─────────────────────────────────────────────────────
    def create_dashboard_tab(self):
        tab = StyledFrame(self.notebook)

        toolbar = StyledFrame(tab)
        toolbar.pack(fill='x', padx=10, pady=10)

        self.add_btn      = StyledButton(toolbar, text="➕ Add Item",    command=self.add_item)
        self.edit_btn     = StyledButton(toolbar, text="✏️ Edit Item",   command=self.edit_item)
        self.delete_btn   = DangerButton(toolbar,  text="🗑️ Delete",     command=self.delete_item)
        self.purchase_btn = StyledButton(toolbar, text="📥 Purchase",    command=lambda: self.record_transaction('purchase'))
        self.sale_btn     = WarningButton(toolbar, text="📤 Sale",       command=lambda: self.record_transaction('sale'))
        StyledButton(toolbar, text="🔄 Refresh", command=self.refresh_data).pack(side='left',padx=5)

        for b in (self.add_btn,self.edit_btn,self.delete_btn,self.purchase_btn,self.sale_btn):
            b.pack(side='left', padx=5)

        # Search / filter bar
        sf = StyledFrame(tab); sf.pack(fill='x', padx=10, pady=5)
        tk.Label(sf, text="Search:", bg=FRAME_BG).pack(side='left')
        self.search_entry = tk.Entry(sf, width=25, font=('Arial',10))
        self.search_entry.pack(side='left', padx=5)
        self.search_entry.bind('<KeyRelease>', self.search_items)

        tk.Label(sf, text="Category:", bg=FRAME_BG).pack(side='left', padx=(15,5))
        self.category_filter = ttk.Combobox(sf,values=["All","Men","Women","Kids"],state="readonly",width=8)
        self.category_filter.set("All"); self.category_filter.pack(side='left',padx=5)
        self.category_filter.bind('<<ComboboxSelected>>', self.search_items)

        tk.Label(sf, text="Season:", bg=FRAME_BG).pack(side='left', padx=(15,5))
        self.season_filter = ttk.Combobox(sf,values=["All","Summer","Winter"],state="readonly",width=8)
        self.season_filter.set("All"); self.season_filter.pack(side='left',padx=5)
        self.season_filter.bind('<<ComboboxSelected>>', self.search_items)

        tk.Label(sf, text="Size:", bg=FRAME_BG).pack(side='left', padx=(15,5))
        self.size_filter = ttk.Combobox(sf,values=["All","XS","S","M","L","XL","XXL"],state="readonly",width=6)
        self.size_filter.set("All"); self.size_filter.pack(side='left',padx=5)
        self.size_filter.bind('<<ComboboxSelected>>', self.search_items)

        tk.Label(sf, text="Color:", bg=FRAME_BG).pack(side='left', padx=(15,5))
        self.color_filter = tk.Entry(sf, width=10, font=('Arial',10))
        self.color_filter.pack(side='left',padx=5)
        self.color_filter.bind('<KeyRelease>', self.search_items)

        # Main content
        content = StyledFrame(tab); content.pack(fill='both',expand=True,padx=10,pady=10)

        items_frame = StyledLabelFrame(content, text="Inventory Items")
        items_frame.pack(fill='both',expand=True,side='left')

        tree_frame = StyledFrame(items_frame); tree_frame.pack(fill='both',expand=True,padx=10,pady=10)

        style = ttk.Style(); style.theme_use('clam')
        style.configure("Custom.Treeview",background=TREE_BG,fieldbackground=TREE_BG,foreground="black")
        style.map("Custom.Treeview",background=[('selected',HEADER_BG)])

        cols = ("ID","Code","Name","Category","Season","Size","Color","Qty","Cost","Price","Profit/unit")
        self.items_tree = ttk.Treeview(tree_frame,columns=cols,show='headings',height=15,style="Custom.Treeview")
        widths = [40,80,140,75,70,50,75,50,75,75,80]
        for col,w in zip(cols,widths):
            self.items_tree.heading(col,text=col)
            self.items_tree.column(col,width=w)

        # Tag colours for stock status
        self.items_tree.tag_configure('low',   background=LOW_STOCK_COLOR)
        self.items_tree.tag_configure('out',   background=OUT_STOCK_COLOR)
        self.items_tree.tag_configure('normal',background=TREE_BG)

        sb = ttk.Scrollbar(tree_frame,orient='vertical',command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=sb.set)
        self.items_tree.pack(side='left',fill='both',expand=True)
        sb.pack(side='right',fill='y')
        self.items_tree.bind('<<TreeviewSelect>>', self.on_item_select)

        # Right panel
        right = StyledFrame(content, width=340); right.pack(fill='y',side='right',padx=(10,0))
        right.pack_propagate(False)

        preview_frame = StyledLabelFrame(right, text="Item Preview")
        preview_frame.pack(fill='x', pady=(0,10))

        img_frame = StyledFrame(preview_frame, height=140); img_frame.pack(fill='x',pady=5,padx=10)
        img_frame.pack_propagate(False)
        self.preview_label = tk.Label(img_frame,text="No image",bg=FRAME_BG,anchor='center')
        self.preview_label.pack(fill='both',expand=True)

        self.item_info = tk.Text(preview_frame,height=9,width=34,wrap='word',bg=TEXT_BG,font=('Arial',9))
        self.item_info.pack(fill='x',pady=5,padx=10)
        self.item_info.insert('1.0',"Select an item to view details")
        self.item_info.config(state='disabled')

        txn_frame = StyledLabelFrame(right, text="Recent Transactions")
        txn_frame.pack(fill='both',expand=True)

        tf = StyledFrame(txn_frame); tf.pack(fill='both',expand=True,padx=10,pady=10)
        tcols = ("Type","Item","Qty","Amount","Date","User")
        self.txn_tree = ttk.Treeview(tf,columns=tcols,show='headings',height=8,style="Custom.Treeview")
        for col in tcols:
            self.txn_tree.heading(col,text=col); self.txn_tree.column(col,width=65)
        tsb = ttk.Scrollbar(tf,orient='vertical',command=self.txn_tree.yview)
        self.txn_tree.configure(yscrollcommand=tsb.set)
        self.txn_tree.pack(side='left',fill='both',expand=True); tsb.pack(side='right',fill='y')

        # Stock-status legend
        leg = StyledFrame(tab); leg.pack(fill='x',padx=10,pady=(0,5))
        tk.Label(leg,text="● Low stock (≤5)",bg=LOW_STOCK_COLOR,fg="#856404",font=('Arial',9),padx=6).pack(side='left',padx=4)
        tk.Label(leg,text="● Out of stock",  bg=OUT_STOCK_COLOR,fg="#842029",font=('Arial',9),padx=6).pack(side='left',padx=4)

        return tab

    # ── Reports Tab ───────────────────────────────────────────────────────
    def create_reports_tab(self):
        tab = StyledFrame(self.notebook); tab.configure(padx=20,pady=20)

        ctrl = StyledFrame(tab); ctrl.pack(fill='x',pady=(0,10))
        tk.Label(ctrl, text="Period:", bg=FRAME_BG).pack(side='left')
        self.report_period = ttk.Combobox(ctrl,
            values=["Daily","Weekly","Monthly","Yearly","Custom"],state="readonly",width=10)
        self.report_period.set("Daily"); self.report_period.pack(side='left',padx=5)

        tk.Label(ctrl,text="From:",bg=FRAME_BG).pack(side='left',padx=(20,5))
        self.start_date = tk.Entry(ctrl,width=12,font=('Arial',10),
                                   state='disabled',disabledbackground="#e0e0e0",
                                   disabledforeground="#aaaaaa")
        self.start_date.pack(side='left')
        tk.Label(ctrl,text="To:",bg=FRAME_BG).pack(side='left',padx=(10,5))
        self.end_date = tk.Entry(ctrl,width=12,font=('Arial',10),
                                 state='disabled',disabledbackground="#e0e0e0",
                                 disabledforeground="#aaaaaa")
        self.end_date.pack(side='left')
        tk.Label(ctrl,text="(YYYY-MM-DD, Custom only)",bg=FRAME_BG,
                 fg="gray",font=('Arial',8)).pack(side='left',padx=(6,0))

        StyledButton(ctrl, text="Generate", command=self.generate_report).pack(side='left',padx=10)
        SuccessButton(ctrl, text="Export CSV", command=self.export_report).pack(side='left')
        WarningButton(ctrl, text="🖨️ Print",   command=self.print_report).pack(side='left',padx=5)

        self.report_period.bind('<<ComboboxSelected>>', self.on_report_period_change)

        rep_frame = StyledLabelFrame(tab, text="Report Results")
        rep_frame.pack(fill='both',expand=True)

        self.summary_text = tk.Text(rep_frame,height=9,width=80,bg=TEXT_BG,font=('Arial',9))
        self.summary_text.pack(fill='x',pady=(10,5),padx=10)

        tf = StyledFrame(rep_frame); tf.pack(fill='both',expand=True,padx=10,pady=(5,10))
        rcols = ("Date","Type","Item","Qty","Unit Price","Total","User")
        self.report_tree = ttk.Treeview(tf,columns=rcols,show='headings',style="Custom.Treeview")
        for col in rcols:
            self.report_tree.heading(col,text=col); self.report_tree.column(col,width=80)
        self.report_tree.column("Item",width=120); self.report_tree.column("Date",width=130)
        rsb = ttk.Scrollbar(tf,orient='vertical',command=self.report_tree.yview)
        self.report_tree.configure(yscrollcommand=rsb.set)
        self.report_tree.pack(side='left',fill='both',expand=True); rsb.pack(side='right',fill='y')

        self._last_report = None
        return tab

    # ── Stock Report Tab ──────────────────────────────────────────────────
    def create_stock_tab(self):
        tab = StyledFrame(self.notebook); tab.configure(padx=20,pady=20)

        ctrl = StyledFrame(tab); ctrl.pack(fill='x',pady=(0,10))
        StyledButton(ctrl,  text="🔄 Refresh",    command=self.load_stock_report).pack(side='left',padx=5)
        SuccessButton(ctrl, text="Export CSV",    command=self.export_stock_report).pack(side='left',padx=5)
        WarningButton(ctrl, text="🖨️ Print",       command=self.print_stock_report).pack(side='left',padx=5)

        # Summary stat labels
        srow = StyledFrame(tab); srow.pack(fill='x',pady=(0,10))
        self.stat_total   = self._stat_box(srow,"Total Items","—")
        self.stat_low     = self._stat_box(srow,"Low Stock","—",WARNING_BG)
        self.stat_out     = self._stat_box(srow,"Out of Stock","—",DANGER_BG)
        self.stat_value   = self._stat_box(srow,"Stock Value","—",SUCCESS_BG)

        sf = StyledLabelFrame(tab, text="Current Stock Levels")
        sf.pack(fill='both',expand=True)

        tf = StyledFrame(sf); tf.pack(fill='both',expand=True,padx=10,pady=10)
        scols = ("Code","Name","Category","Season","Size","Color","Qty","Cost","Price","Profit/unit","Status")
        self.stock_tree = ttk.Treeview(tf,columns=scols,show='headings',style="Custom.Treeview")
        sw = [75,140,75,70,50,75,50,75,75,80,90]
        for col,w in zip(scols,sw):
            self.stock_tree.heading(col,text=col); self.stock_tree.column(col,width=w)
        self.stock_tree.tag_configure('low',background=LOW_STOCK_COLOR)
        self.stock_tree.tag_configure('out',background=OUT_STOCK_COLOR)
        ssb = ttk.Scrollbar(tf,orient='vertical',command=self.stock_tree.yview)
        self.stock_tree.configure(yscrollcommand=ssb.set)
        self.stock_tree.pack(side='left',fill='both',expand=True); ssb.pack(side='right',fill='y')

        return tab

    def _stat_box(self, parent, label, value, color=HEADER_BG):
        f = tk.Frame(parent,bg=color,padx=16,pady=8,relief='flat')
        f.pack(side='left',padx=6)
        tk.Label(f,text=label,bg=color,fg="white",font=('Arial',9)).pack()
        v = tk.Label(f,text=value,bg=color,fg="white",font=('Arial',14,'bold'))
        v.pack()
        return v

    # ── User Management Tab ───────────────────────────────────────────────
    def create_users_tab(self):
        tab = StyledFrame(self.notebook); tab.configure(padx=20,pady=20)

        # Registration
        reg_frame = StyledLabelFrame(tab, text="Register New User (Admin Only)")
        reg_frame.pack(fill='x',pady=(0,20))

        labels = ["Admin Username:","Admin Password:","New Username:","New Password:","Role:"]
        self.reg_fields = {}
        for i,lbl in enumerate(labels):
            tk.Label(reg_frame,text=lbl,bg=FRAME_BG).grid(row=i,column=0,sticky='w',pady=3,padx=10)
            if lbl == "Role:":
                w = ttk.Combobox(reg_frame,values=["staff","admin"],state="readonly",width=28)
                w.set("staff")
            elif "Password" in lbl:
                w = tk.Entry(reg_frame,show="*",width=30,font=('Arial',10))
            else:
                w = tk.Entry(reg_frame,width=30,font=('Arial',10))
            w.grid(row=i,column=1,pady=3,padx=(0,10))
            self.reg_fields[lbl] = w

        StyledButton(reg_frame,text="Create User",command=self.register_user).grid(
            row=len(labels),column=0,columnspan=2,pady=10,padx=10,sticky='we')

        # Users list
        ul_frame = StyledLabelFrame(tab, text="Existing Users")
        ul_frame.pack(fill='both',expand=True)

        uf = StyledFrame(ul_frame); uf.pack(fill='x',padx=10,pady=(10,0))
        StyledButton(uf,text="🔄 Refresh",command=self.load_users).pack(side='left',padx=5)
        DangerButton(uf,text="🗑️ Delete Selected",command=self.delete_selected_user).pack(side='left',padx=5)
        tk.Label(uf,text="(Cannot delete the currently logged-in admin)",
                 bg=FRAME_BG,fg="gray",font=('Arial',9)).pack(side='left',padx=10)

        utf = StyledFrame(ul_frame); utf.pack(fill='both',expand=True,padx=10,pady=10)
        ucols = ("ID","Username","Role","Created At")
        self.users_tree = ttk.Treeview(utf,columns=ucols,show='headings',style="Custom.Treeview",height=8)
        for col,w in zip(ucols,[50,150,80,200]):
            self.users_tree.heading(col,text=col); self.users_tree.column(col,width=w)
        usb = ttk.Scrollbar(utf,orient='vertical',command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=usb.set)
        self.users_tree.pack(side='left',fill='both',expand=True); usb.pack(side='right',fill='y')

        return tab

    # ── Event Handlers ────────────────────────────────────────────────────
    def login(self):
        username = self.login_username.get().strip()
        password = self.login_password.get().strip()
        if not username or not password:
            messagebox.showwarning("Input Error","Please enter both username and password"); return
        success, role = check_login(username, password)
        if success:
            self.active_user = username; self.active_role = role
            self.user_label.config(text=f"👤 {username} ({role})")
            for i in range(1,5): self.notebook.tab(i, state="normal")
            # Hide User Management tab for staff
            if role != 'admin':
                self.notebook.tab(4, state="disabled")
            self.notebook.select(1)
            self.apply_permissions()
            self.refresh_data()
            messagebox.showinfo("Success", f"Welcome {username}!")
        else:
            messagebox.showerror("Login Failed","Invalid username or password")

    def logout(self):
        self.active_user = None; self.active_role = None
        self.user_label.config(text="Not logged in")
        for i in range(1,5): self.notebook.tab(i, state="disabled")
        self.notebook.select(0)
        self.login_username.delete(0,tk.END)
        self.login_password.delete(0,tk.END)

    def change_password(self):
        if not self.active_user:
            messagebox.showwarning("Not logged in","Please log in first"); return
        dialog = ChangePasswordDialog(self, self.active_user)
        self.wait_window(dialog)

    def register_user(self):
        f = self.reg_fields
        admin_user = f["Admin Username:"].get().strip()
        admin_pass = f["Admin Password:"].get().strip()
        new_user   = f["New Username:"].get().strip()
        new_pass   = f["New Password:"].get().strip()
        role       = f["Role:"].get()
        if not all([admin_user, admin_pass, new_user, new_pass]):
            messagebox.showwarning("Input Error","Please fill all fields"); return
        ok, r = check_login(admin_user, admin_pass)
        if not ok or r != 'admin':
            messagebox.showerror("Auth Failed","Invalid admin credentials"); return
        success, message = register_user_by_admin(admin_user, new_user, new_pass, role)
        if success:
            messagebox.showinfo("Success", message)
            for key,w in f.items():
                if hasattr(w,'delete'): w.delete(0,tk.END)
            self.load_users()
        else:
            messagebox.showerror("Error", message)

    def load_users(self):
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        for row in get_all_users():
            self.users_tree.insert('','end', values=row)

    def delete_selected_user(self):
        sel = self.users_tree.selection()
        if not sel:
            messagebox.showwarning("Select User","Please select a user to delete"); return
        uid,uname,role,_ = self.users_tree.item(sel[0])['values']
        if uname == self.active_user:
            messagebox.showerror("Cannot Delete","You cannot delete your own account."); return
        if not messagebox.askyesno("Confirm","Delete user '%s'?" % uname, icon='warning'): return
        ok, msg = delete_user(uid)
        if ok:
            messagebox.showinfo("Success", msg); self.load_users()
        else:
            messagebox.showerror("Error", msg)

    def apply_permissions(self):
        is_admin = (self.active_role == 'admin')
        s_admin = 'normal' if is_admin else 'disabled'
        s_staff = 'normal' if self.active_role in ['admin','staff'] else 'disabled'
        self.add_btn.config(state=s_admin)
        self.edit_btn.config(state=s_admin)
        self.delete_btn.config(state=s_admin)
        self.purchase_btn.config(state=s_admin)
        self.sale_btn.config(state=s_staff)
        # User Management tab: admin only
        self.notebook.tab(4, state='normal' if is_admin else 'disabled')

    def refresh_data(self):
        self.load_items()
        self.load_recent_transactions()
        self.load_stock_report()
        self.load_users()
        self.update_alert_badge()

    def update_alert_badge(self):
        rows = get_stock_summary()
        low = sum(1 for r in rows if 0 < r[6] <= LOW_STOCK_QTY)
        out = sum(1 for r in rows if r[6] == 0)
        if out:
            self.alert_label.config(text=f"⚠ {out} OUT OF STOCK  {low} LOW STOCK", bg=DANGER_BG)
        elif low:
            self.alert_label.config(text=f"⚠ {low} LOW STOCK ITEMS", bg=WARNING_BG)
        else:
            self.alert_label.config(text="", bg=HEADER_BG)

    def load_items(self, search_term=None, category=None, season=None,
                   color=None, size=None):
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
        items = search_items(search_term, category, season, color, size)
        for item in items:
            qty = item[7]
            tag = 'out' if qty == 0 else ('low' if qty <= LOW_STOCK_QTY else 'normal')
            profit = item[9] - item[8]
            self.items_tree.insert('','end', tags=(tag,), values=(
                item[0],item[1],item[2],item[3],item[4],item[5],item[6],
                qty, f"${item[8]:.2f}", f"${item[9]:.2f}", f"${profit:.2f}"
            ))

    def load_recent_transactions(self, limit=20):
        for item in self.txn_tree.get_children():
            self.txn_tree.delete(item)
        conn = get_connection()
        c = conn.cursor()
        c.execute("""SELECT t.txn_type,i.name,t.quantity,t.total_price,t.txn_date,t.performed_by
                     FROM transactions t JOIN items i ON t.item_id=i.id
                     ORDER BY t.txn_date DESC LIMIT ?""", (limit,))
        for row in c.fetchall():
            ds = datetime.fromisoformat(row[4]).strftime("%m/%d %H:%M")
            self.txn_tree.insert('','end', values=(
                row[0].capitalize(), row[1], row[2], f"${row[3]:.2f}", ds, row[5]
            ))
        conn.close()

    def load_stock_report(self):
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)
        rows = get_stock_summary()
        total_qty = 0; low_cnt = 0; out_cnt = 0; total_value = 0.0
        for r in rows:
            code,name,cat,season,sz,col,qty,pp,sp = r
            status = "OUT OF STOCK" if qty == 0 else ("LOW STOCK" if qty <= LOW_STOCK_QTY else "OK")
            tag = 'out' if qty == 0 else ('low' if qty <= LOW_STOCK_QTY else 'normal')
            profit = sp - pp
            self.stock_tree.insert('','end', tags=(tag,), values=(
                code,name,cat,season,sz,col,qty,
                f"${pp:.2f}",f"${sp:.2f}",f"${profit:.2f}",status
            ))
            total_qty += qty
            total_value += qty * pp
            if qty == 0:  out_cnt += 1
            elif qty <= LOW_STOCK_QTY: low_cnt += 1
        self.stat_total.config(text=str(total_qty))
        self.stat_low.config(text=str(low_cnt))
        self.stat_out.config(text=str(out_cnt))
        self.stat_value.config(text=f"${total_value:,.0f}")

    def search_items(self, event=None):
        term     = self.search_entry.get().strip()
        category = self.category_filter.get()
        season   = self.season_filter.get()
        size     = self.size_filter.get()
        color    = self.color_filter.get().strip()
        self.load_items(
            term or None,
            category if category != "All" else None,
            season   if season   != "All" else None,
            color    or None,
            size     if size     != "All" else None,
        )

    def on_item_select(self, event=None):
        sel = self.items_tree.selection()
        if not sel:
            self.selected_item = None
            self.preview_label.config(text="No image",image='')
            self.item_info.config(state='normal')
            self.item_info.delete('1.0',tk.END)
            self.item_info.insert('1.0',"Select an item to view details")
            self.item_info.config(state='disabled')
            return
        item_id = self.items_tree.item(sel[0])['values'][0]
        conn = get_connection(); c = conn.cursor()
        c.execute("SELECT * FROM items WHERE id=?", (item_id,))
        item = c.fetchone(); conn.close()
        if item:
            self.selected_item = {
                'id':item[0],'code':item[1],'name':item[2],'category':item[3],
                'season':item[4],'size':item[5],'color':item[6],'quantity':item[7],
                'purchase_price':item[8],'sale_price':item[9],'image_path':item[10]
            }
            self.item_info.config(state='normal')
            self.item_info.delete('1.0',tk.END)
            qty = item[7]
            stock_status = "OUT OF STOCK" if qty==0 else (f"⚠ LOW STOCK ({qty})" if qty<=LOW_STOCK_QTY else f"{qty} units")
            info = (f"📦 {item[2]} ({item[1]})\n"
                    f"Category: {item[3]}\nSeason: {item[4]}\n"
                    f"Size: {item[5]}  Color: {item[6]}\n"
                    f"Stock: {stock_status}\n"
                    f"Cost:   ${item[8]:.2f}\n"
                    f"Price:  ${item[9]:.2f}\n"
                    f"Profit: ${item[9]-item[8]:.2f} per unit")
            self.item_info.insert('1.0',info)
            self.item_info.config(state='disabled')
            if item[10] and os.path.exists(item[10]):
                try:
                    img = Image.open(item[10]); img.thumbnail((280,140))
                    self.preview_image = ImageTk.PhotoImage(img)
                    self.preview_label.config(image=self.preview_image, text='')
                except Exception:
                    self.preview_label.config(text="Error loading image",image='')
            else:
                self.preview_label.config(text="No image available",image='')

    def add_item(self):
        if self.active_role != 'admin':
            messagebox.showerror("Permission Denied","Only administrators can add items"); return
        dialog = ItemDialog(self, "Add New Item")
        self.wait_window(dialog)
        if dialog.result: self.refresh_data()

    def edit_item(self):
        if not self.selected_item:
            messagebox.showwarning("Select Item","Please select an item to edit"); return
        if self.active_role != 'admin':
            messagebox.showerror("Permission Denied","Only administrators can edit items"); return
        dialog = ItemDialog(self, "Edit Item", self.selected_item)
        self.wait_window(dialog)
        if dialog.result: self.refresh_data()

    def delete_item(self):
        if not self.selected_item:
            messagebox.showwarning("Select Item","Please select an item to delete"); return
        if self.active_role != 'admin':
            messagebox.showerror("Permission Denied","Only administrators can delete items"); return
        if messagebox.askyesno("Confirm Delete",
                               f"Delete '{self.selected_item['name']}'?", icon='warning'):
            ok, msg = delete_item(self.selected_item['id'])
            if ok: messagebox.showinfo("Success",msg); self.refresh_data()
            else:  messagebox.showerror("Error",msg)

    def record_transaction(self, txn_type):
        if not self.selected_item:
            messagebox.showwarning("Select Item",f"Please select an item to record {txn_type}"); return
        if txn_type == 'purchase' and self.active_role != 'admin':
            messagebox.showerror("Permission Denied","Only administrators can record purchases"); return
        if txn_type == 'sale' and self.active_role not in ['admin','staff']:
            messagebox.showerror("Permission Denied","You don't have permission to record sales"); return
        dialog = TransactionDialog(self, txn_type, self.selected_item)
        self.wait_window(dialog)
        if dialog.result: self.refresh_data()

    # ── Report Handlers ───────────────────────────────────────────────────
    def on_report_period_change(self, event=None):
        period = self.report_period.get()
        if period == "Custom":
            self.start_date.config(state='normal', bg='white', fg='black')
            self.end_date.config(state='normal',   bg='white', fg='black')
            for entry in (self.start_date, self.end_date):
                if entry.get() == "YYYY-MM-DD":
                    entry.delete(0, tk.END)
        else:
            for entry in (self.start_date, self.end_date):
                entry.config(state='normal')
                entry.delete(0, tk.END)
                entry.insert(0, "YYYY-MM-DD")
                entry.config(state='disabled',
                             disabledbackground="#e0e0e0",
                             disabledforeground="#aaaaaa")

    def _get_report(self):
        period = self.report_period.get().lower()
        start_date = end_date = None
        if period == 'custom':
            try:
                start_date = datetime.strptime(self.start_date.get(),"%Y-%m-%d").date()
                end_date   = datetime.strptime(self.end_date.get(),  "%Y-%m-%d").date()
            except ValueError:
                messagebox.showerror("Date Error","Enter dates as YYYY-MM-DD"); return None
        report = generate_report(period, start_date, end_date)
        if 'error' in report:
            messagebox.showerror("Error",report['error']); return None
        return report

    def generate_report(self):
        report = self._get_report()
        if not report: return
        self._last_report = report
        period_label = self.report_period.get()

        self.summary_text.delete('1.0',tk.END)
        summary = (f"📊 {period_label} Report Summary\n\n"
                   f"💵 Financial:\n"
                   f"  Total Sales:     ${report['total_sales']:.2f}\n"
                   f"  Total Purchases: ${report['total_purchases']:.2f}\n"
                   f"  Net Profit:      ${report['profit']:.2f}\n\n"
                   f"📦 Movement:\n"
                   f"  Qty Sold:        {report['qty_sold']} units\n"
                   f"  Qty Purchased:   {report['qty_purchased']} units\n\n"
                   f"📈 Per Item:\n")
        for item,data in report['per_item'].items():
            summary += (f"  {item}: Sold {data['sold']} (${data['sale_total']:.2f}), "
                        f"Purchased {data['purchased']} (${data['purchase_total']:.2f})\n")
        self.summary_text.insert('1.0',summary)

        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
        for txn in report['transactions']:
            ds = datetime.fromisoformat(txn[8]).strftime("%Y-%m-%d %H:%M")
            self.report_tree.insert('','end', values=(
                ds, txn[4].capitalize(), txn[3], txn[5],
                f"${txn[6]:.2f}", f"${txn[7]:.2f}", txn[9]
            ))

    def export_report(self):
        report = self._get_report()
        if not report: return
        fn = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files","*.csv"),("All files","*.*")],
            initialfile=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        if fn:
            export_report_csv(report, fn)
            messagebox.showinfo("Exported",f"Report saved to {fn}")

    def print_report(self):
        report = self._get_report()
        if not report: return
        period_label = self.report_period.get()
        text = build_report_text(report, f"{period_label} Report")
        ok, msg = print_text_report(text, period_label)
        if ok: messagebox.showinfo("Print",msg)
        else:  messagebox.showerror("Print Error",msg)

    def export_stock_report(self):
        fn = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files","*.csv"),("All files","*.*")],
            initialfile=f"stock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        if fn:
            export_stock_csv(fn)
            messagebox.showinfo("Exported",f"Stock report saved to {fn}")

    def print_stock_report(self):
        text = build_stock_report_text()
        ok, msg = print_text_report(text, "Stock Report")
        if ok: messagebox.showinfo("Print",msg)
        else:  messagebox.showerror("Print Error",msg)

# ---------- Dialogs ----------
class ItemDialog(tk.Toplevel):
    def __init__(self, parent, title, item_data=None):
        super().__init__(parent)
        self.title(title); self.geometry("520x580")
        self.resizable(False,False); self.configure(bg=FRAME_BG)
        self.parent = parent; self.item_data = item_data; self.result = False
        self.create_widgets()
        if item_data: self.load_data()

    def create_widgets(self):
        mf = StyledFrame(self); mf.pack(fill='both',expand=True,padx=20,pady=20)

        rows = [
            ("Item Name:",    'entry',   None),
            ("Category:",     'combo',   ["Men","Women","Kids"]),
            ("Season:",       'combo',   ["Summer","Winter"]),
            ("Size:",         'combo',   ["XS","S","M","L","XL","XXL"]),
            ("Color:",        'entry',   None),
            ("Quantity:",     'entry',   None),
            ("Purchase Price ($):", 'entry', None),
            ("Sale Price ($):",     'entry', None),
            ("Profit/unit ($):",    'readonly', None),
            ("Item Image:",   'image',  None),
        ]
        self.fields = {}
        for i,(label,wtype,opts) in enumerate(rows):
            tk.Label(mf,text=label,bg=FRAME_BG).grid(row=i,column=0,sticky='w',pady=4)
            if wtype == 'entry':
                w = tk.Entry(mf,width=30,font=('Arial',10))
                w.grid(row=i,column=1,pady=4,padx=(10,0),sticky='we')
                if label in ("Purchase Price ($):","Sale Price ($):"):
                    w.bind('<KeyRelease>', self.calc_profit)
            elif wtype == 'readonly':
                w = tk.Entry(mf,width=30,font=('Arial',10),state='readonly',
                             readonlybackground="#e8f8e8",fg=SUCCESS_BG)
                w.grid(row=i,column=1,pady=4,padx=(10,0),sticky='we')
            elif wtype == 'combo':
                w = ttk.Combobox(mf,values=opts,state="readonly",width=28)
                w.grid(row=i,column=1,pady=4,padx=(10,0),sticky='we')
            elif wtype == 'image':
                frm = StyledFrame(mf); frm.grid(row=i,column=1,pady=4,padx=(10,0),sticky='we')
                self.image_path = tk.StringVar()
                tk.Entry(frm,textvariable=self.image_path,width=22,font=('Arial',9)).pack(side='left')
                StyledButton(frm,text="Browse",command=self.browse_image).pack(side='left',padx=5)
                w = self.image_path
            self.fields[label] = w

        mf.columnconfigure(1,weight=1)
        bf = StyledFrame(mf); bf.grid(row=len(rows),column=0,columnspan=2,pady=16)
        SuccessButton(bf,text="Save",command=self.save).pack(side='left',padx=10)
        StyledButton(bf,text="Cancel",command=self.destroy).pack(side='left',padx=10)

    def calc_profit(self, event=None):
        """Auto-calculate and display profit when prices change."""
        try:
            pp = float(self.fields["Purchase Price ($):"].get())
            sp = float(self.fields["Sale Price ($):"].get())
            profit = sp - pp
            w = self.fields["Profit/unit ($):"]
            w.config(state='normal')
            w.delete(0,tk.END); w.insert(0,f"{profit:.2f}")
            w.config(state='readonly')
        except ValueError:
            pass

    def load_data(self):
        d = self.item_data
        self.fields["Item Name:"].insert(0, d['name'])
        self.fields["Category:"].set(d['category'])
        self.fields["Season:"].set(d['season'])
        self.fields["Size:"].set(d['size'])
        self.fields["Color:"].insert(0, d['color'])
        self.fields["Quantity:"].insert(0, str(d['quantity']))
        self.fields["Purchase Price ($):"].insert(0, str(d['purchase_price']))
        self.fields["Sale Price ($):"].insert(0, str(d['sale_price']))
        self.calc_profit()
        if d['image_path']: self.image_path.set(d['image_path'])

    def browse_image(self):
        fn = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Images","*.png *.jpg *.jpeg *.gif *.bmp")])
        if fn: self.image_path.set(fn)

    def save(self):
        try:
            name     = self.fields["Item Name:"].get().strip()
            category = self.fields["Category:"].get()
            season   = self.fields["Season:"].get()
            size     = self.fields["Size:"].get()
            color    = self.fields["Color:"].get().strip()
            quantity = int(self.fields["Quantity:"].get().strip())
            pp       = float(self.fields["Purchase Price ($):"].get().strip())
            sp       = float(self.fields["Sale Price ($):"].get().strip())
            if not all([name,category,season]): raise ValueError("Please fill required fields")
            if pp <= 0 or sp <= 0: raise ValueError("Prices must be positive")
            if quantity < 0: raise ValueError("Quantity cannot be negative")
        except ValueError as e:
            messagebox.showerror("Input Error",str(e)); return

        image_path = None
        src = self.image_path.get()
        if src and os.path.exists(src):
            ext  = os.path.splitext(src)[1]
            code = self.item_data['code'] if self.item_data else generate_item_code(name)
            dest = os.path.join(IMAGE_FOLDER, f"{code}{ext}")
            try:
                with open(src,'rb') as s, open(dest,'wb') as d: d.write(s.read())
                image_path = dest
            except Exception as e:
                messagebox.showerror("Image Error",str(e)); return

        if self.item_data:
            ok, msg = update_item(self.item_data['id'],name,category,season,size,color,
                                  quantity,pp,sp,image_path)
        else:
            ok, msg = add_item(name,category,season,size,color,quantity,pp,sp,image_path)

        if ok:
            messagebox.showinfo("Success",msg); self.result = True; self.destroy()
        else:
            messagebox.showerror("Error",msg)


class TransactionDialog(tk.Toplevel):
    def __init__(self, parent, txn_type, item_data):
        super().__init__(parent)
        self.title(f"Record {txn_type.capitalize()}")
        self.geometry("420x330"); self.resizable(False,False)
        self.configure(bg=FRAME_BG)
        self.parent = parent; self.txn_type = txn_type
        self.item_data = item_data; self.result = False
        self.create_widgets()

    def create_widgets(self):
        mf = StyledFrame(self); mf.pack(fill='both',expand=True,padx=20,pady=20)
        tk.Label(mf,text=f"Record {self.txn_type.capitalize()}",
                 font=("Helvetica",14,"bold"),bg=FRAME_BG).pack(pady=(0,12))

        inf = StyledFrame(mf); inf.pack(fill='x',pady=8)
        tk.Label(inf,text=f"Item: {self.item_data['name']}",
                 font=("Helvetica",12,"bold"),bg=FRAME_BG).pack(anchor='w')
        qty = self.item_data['quantity']
        color = DANGER_BG if qty == 0 else (WARNING_BG if qty <= LOW_STOCK_QTY else "black")
        tk.Label(inf,text=f"Current Stock: {qty} units",bg=FRAME_BG,fg=color).pack(anchor='w',pady=(4,0))

        inp = StyledFrame(mf); inp.pack(fill='x',pady=12)
        tk.Label(inp,text="Quantity:",font=("Helvetica",10),bg=FRAME_BG).grid(row=0,column=0,sticky='w',pady=8)
        self.qty_entry = tk.Entry(inp,width=20,font=("Helvetica",10))
        self.qty_entry.grid(row=0,column=1,pady=8,padx=(10,0),sticky='we')

        default_price = (self.item_data['purchase_price'] if self.txn_type == 'purchase'
                         else self.item_data['sale_price'])
        tk.Label(inp,text="Unit Price ($):",font=("Helvetica",10),bg=FRAME_BG).grid(row=1,column=0,sticky='w',pady=8)
        self.price_entry = tk.Entry(inp,width=20,font=("Helvetica",10))
        self.price_entry.insert(0,f"{default_price:.2f}")
        self.price_entry.grid(row=1,column=1,pady=8,padx=(10,0),sticky='we')
        inp.columnconfigure(1,weight=1)

        bf = StyledFrame(mf); bf.pack(fill='x',pady=16)
        bc = StyledFrame(bf); bc.pack(expand=True)
        color_bg = BUTTON_BG if self.txn_type == 'purchase' else WARNING_BG
        tk.Button(bc,text=f"Record {self.txn_type.capitalize()}",command=self.record,
                  bg=color_bg,fg="white",width=18).pack(side='left',padx=10)
        tk.Button(bc,text="Cancel",command=self.destroy,
                  bg="#95a5a6",fg="white",width=10).pack(side='left',padx=10)
        self.qty_entry.focus()
        self.bind('<Return>', lambda e: self.record())

    def record(self):
        try:
            qty  = int(self.qty_entry.get().strip())
            price= float(self.price_entry.get().strip())
            if qty   <= 0: raise ValueError("Quantity must be positive")
            if price <= 0: raise ValueError("Price must be positive")
        except ValueError as e:
            messagebox.showerror("Input Error",str(e)); return
        ok, msg = record_transaction(self.item_data['id'],self.txn_type,qty,price,self.parent.active_user)
        if ok:
            messagebox.showinfo("Success",msg); self.result = True; self.destroy()
        else:
            messagebox.showerror("Error",msg)


class ChangePasswordDialog(tk.Toplevel):
    def __init__(self, parent, username):
        super().__init__(parent)
        self.title("Change Password"); self.geometry("350x220")
        self.resizable(False,False); self.configure(bg=FRAME_BG)
        self.parent = parent; self.username = username
        self.create_widgets()

    def create_widgets(self):
        mf = StyledFrame(self); mf.pack(fill='both',expand=True,padx=30,pady=30)
        tk.Label(mf,text="Change Password",font=("Helvetica",14,"bold"),bg=FRAME_BG).pack(pady=8)
        tk.Label(mf,text="Old Password:",bg=FRAME_BG).pack(anchor='w',pady=(10,4))
        self.old_pw = tk.Entry(mf,show="*",width=28); self.old_pw.pack(fill='x',pady=4)
        tk.Label(mf,text="New Password:",bg=FRAME_BG).pack(anchor='w',pady=(10,4))
        self.new_pw = tk.Entry(mf,show="*",width=28); self.new_pw.pack(fill='x',pady=4)
        bf = StyledFrame(mf); bf.pack(pady=16)
        SuccessButton(bf,text="Change Password",command=self.change_password).pack(side='left',padx=10)
        StyledButton(bf,text="Cancel",command=self.destroy).pack(side='left',padx=10)

    def change_password(self):
        old = self.old_pw.get().strip()
        new = self.new_pw.get().strip()
        if not old or not new:
            messagebox.showwarning("Input Error","Please fill both fields"); return
        ok, msg = change_password(self.username, old, new)
        if ok:
            messagebox.showinfo("Success",msg); self.destroy()
        else:
            messagebox.showerror("Error",msg)

# ---------- Entry Point ----------
def main():
    init_db()
    app = ClothesManagementSystem()
    app.mainloop()

if __name__ == "__main__":
    main()