# 👕 Clothes Management System

A desktop application built with **Python** and **Tkinter** to help retail shop owners manage clothing inventory, track sales and purchases, handle stock updates, and generate automated reports.

---

## 📌 Project Overview

The **Clothes Management System** is designed to streamline inventory management for clothing stores. It organizes items by category (Men, Women, Kids) and season (Summer, Winter), provides fast search, automatically updates stock after each sale or purchase, calculates profit, and generates daily/weekly/monthly/yearly reports. The system supports two user roles: **Admin** (full control) and **Salesman** (sales and search).

---

## ✨ Key Features

- **User Authentication** – Secure login/logout for Admin and Salesman.
- **User Registration** – Admin can register new users.
- **Clothing Item Management** – Add, update, delete clothing items (name, category, season, purchase price, sale price, quantity, unique ID).
- **Item Search** – Search by name, ID, category, season, or price.
- **Sales Management** – Record sales, automatically reduce stock, prevent out-of-stock sales.
- **Purchase Management** – Record new stock arrivals, automatically increase inventory.
- **Auto Stock Update** – Real‑time stock adjustments after every sale or purchase.
- **Auto Profit Calculation** – Profit computed automatically based on purchase and sale prices.
- **Report Generation** – Generate and export (print/save) reports for daily, weekly, monthly, and yearly sales, purchases, stock, and profit.
- **Centralized Database** – All data stored in a single DB for consistency.

---

## 🛠️ Technologies Used

| Category       | Technology                                      |
|----------------|-------------------------------------------------|
| Language       | Python                                          |
| GUI Framework  | Tkinter (built-in)                             |
| Database       | SQLite3 (or any relational DB like MySQL)      |
| Development Environment | Any Python IDE (VS Code, PyCharm, etc.) |

---

## 🚀 How to Run the Project

### Prerequisites
- Python 3.7 or higher installed on your system.
- Required libraries: `tkinter` (usually included), `sqlite3` (included).

### Setup Instructions

1. **Clone the repository**  
   ```bash
   git clone https://github.com/Sawaira-Mumtaz786/Clothe-management-system-Web-Application.git
   cd Clothe-management-system-Web-Application
   pip install -r requirements.txt   # if a requirements file exists
   python main.py
   Clothes-Management-System/
├── main.py               # Entry point of the application
├── database/
│   └── clothes.db        # SQLite database file (auto-generated)
├── modules/
│   ├── login.py
│   ├── inventory.py
│   ├── sales.py
│   ├── purchase.py
│   ├── reports.py
│   └── users.py
├── assets/               # Icons, images, etc.
├── requirements.txt      # Python dependencies (if any)
└── README.md             # This file
👥 User Roles
Role	Permissions
Admin	Full access: manage items, users, purchases, reports, view all sales.
Salesman	Search items, record sales, view stock levels (no add/delete/modify).
📊 Reports Available
Daily / Weekly / Monthly / Yearly Sales Report

Daily / Weekly / Monthly / Yearly Purchase Report

Current Stock Level Report

Profit Summary Report (automatically calculated)

🔧 Future Improvements (Optional)
Add barcode scanning for faster checkout.

Integrate with a web dashboard for remote stock monitoring.

Low‑stock alerts via email/SMS.

Multi‑store support.

👩‍💻 Author
Sawaira Mumtaz
BC220408093
Virtual University of Pakistan

📄 License
This project is developed as a Final Year Project for academic purposes.
All rights reserved.

🙏 Acknowledgments
Supervisor: Asadullah

Virtual University of Pakistan – Software Projects & Research Section

All teachers and family who supported this work.
