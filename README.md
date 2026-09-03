# 👕 AI-Powered Clothing & Inventory Management System
Its a simplete Fyp for my BSCS project but i make changes on github according to my Ai engineering skill i intregated ai feature and also deploy it.

[![Live Web Demo](https://img.shields.io/badge/🚀_Live_Demo-Streamlit_App-FF4B4B?style=for-the-badge)](https://clothe-management-system-web-application-i7qpfypguzynnux2tszqk.streamlit.app)
[![GitHub Repository](https://img.shields.io/badge/📁_Source_Code-GitHub-181717?style=for-the-badge&logo=github)](https://github.com/Sawaira-Mumtaz786/Clothe-management-system-Web-Application)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![Google Gemini API](https://img.shields.io/badge/AI-Gemini_2.5_Flash-4285F4?style=for-the-badge&logo=google)](https://aistudio.google.com/)

A comprehensive clothing management platform offering both a **live web demonstration** and a **full desktop application**. Built with Python, SQLite, Tkinter, and Google Gemini AI, this system automates product metadata extraction from catalog photos and manages inventory workflows.

---

## 🔗 Quick Links

- [🚀 Launch Live Web Application](https://clothe-management-system-web-application-i7qpfypguzynnux2tszqk.streamlit.app)
- [📁 GitHub Repository Source Code](https://github.com/Sawaira-Mumtaz786/Clothe-management-system-Web-Application)

---

## 🌟 Key Features

- **✨ Vision-Based AI Auto-Tagging:** Uses Google Gemini 2.5 Flash to automatically detect item name, category (Men/Women/Kids), season, size, and color from uploaded or repository product photos.
- **📦 Stock Tracking & Low-Stock Badges:** Real-time quantity monitoring with automated visual warnings for low-stock (≤5 units) and out-of-stock items.
- **📈 Financial Analytics:** Profit analysis displaying Gross Profit, Sales Revenue, and Cost of Goods Sold (COGS) with CSV export support.
- **🔐 Dual Interface Options:**
  - **Web Interface:** Accessible via browser on Streamlit Cloud.
  - **Desktop Client:** Feature-rich local UI built using Tkinter and SQLite.

---

## 🛠️ Tech Stack

- **Core Engine:** Python
- **Web App (Live Demo):** Streamlit
- **Desktop Client:** Tkinter / TTK
- **Database:** SQLite3
- **AI Integration:** Google GenAI SDK (`gemini-2.5-flash`)
- **Image Processing:** Pillow (PIL)

---

## 🚀 Local Desktop Installation

1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/Sawaira-Mumtaz786/Clothe-management-system-Web-Application.git](https://github.com/Sawaira-Mumtaz786/Clothe-management-system-Web-Application.git)
   cd Clothe-management-system-Web-Application

   Install Dependencies:

Bash
pip install -r requirements.txt
Configure Gemini API Key:

Windows Command Prompt:

DOS
set GEMINI_API_KEY="your_api_key_here"
Linux / Mac / Git Bash:

Bash
export GEMINI_API_KEY="your_api_key_here"
Launch Application:

Desktop App (Tkinter):

Bash
python Clothes_managementsys.py
Web App (Streamlit):

Bash
streamlit run app.py
👤 Default Credentials (Desktop App)
Username: admin

Password: admin123


---

**Push `README.md` to GitHub**

Run these commands in Command Prompt (`D:\Clothe-management-system-Web-Application`):

```cmd
git add README.md
git commit -m "Update README with live application redirect links and badges"
git push origin main
