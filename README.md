<<<<<<< HEAD
# Looph.co

<div align="center">

![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

**A minimalist clothing shop portfolio project built with Flask**

[View Demo](#) │ [Report Bug](../../issues) │ [Request Feature](../../issues)

</div>

---

## ─── About The Project

**Loophco** is a sleek, modern web-based clothing shop concept that demonstrates clean design principles and Flask backend integration. This portfolio project showcases how to build a structured, navigable web application with smooth routing and aesthetic appeal.

> 💡 **Note:** This is a conceptual demonstration project - not a full e-commerce platform, but a showcase of web development fundamentals and design sensibility.

### ─── Key Highlights

- ▸ **Minimalist Design** - Clean, responsive interface that puts content first
- ▸ **Flask-Powered** - Lightweight Python backend with efficient routing
- ▸ **Fully Responsive** - Seamless experience across all devices
- ▸ **Portfolio Ready** - Demonstrates real-world web development skills
- ▸ **Easy to Extend** - Structured architecture ready for additional features

---

## ─── Features

### Current Capabilities

- **Clean Navigation System** - Intuitive routing between Home, Products, and About pages
- **Template Rendering** - Flask-based HTML template integration
- **Internal Styling** - CSS embedded within templates for streamlined design
- **Responsive Layout** - Adapts beautifully to desktop, tablet, and mobile screens
- **Organized Structure** - Well-architected codebase following best practices

### ─── Future Enhancements

- Product database integration
- Shopping cart functionality
- User authentication system
- Admin dashboard for inventory management
- Payment gateway integration
- Order tracking features

---

## ─── Built With

### Frontend

- **HTML5** - Semantic markup and structure
- **CSS3** - Modern styling with responsive design
- **JavaScript** - Interactive functionality and dynamic content

### Backend

- **Flask** - Micro web framework for Python
- **Python 3.x** - Core programming language

### Development Tools

- **Git & GitHub** - Version control and collaboration
- **VS Code / Code::Blocks** - Development environment

---

## ─── Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Git

### Setup Instructions

1. **Clone the repository**

   ```bash
   git clone https://github.com/Strix-xy/Looph.co-WebApp.git
   cd Looph.co-WebApp
   ```

2. **Create a virtual environment** (recommended)

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install flask
   ```

4. **Run the application**

   ```bash
   python app.py
   ```

5. **Open your browser**
   ```
   Navigate to http://localhost:5000
   ```

---

## ─── Deploy To Vercel (GitHub) With Supabase + Clerk

Use this checklist to deploy without runtime errors.

### 1) Push to GitHub

- Commit and push this project to your GitHub repository.
- Keep `vercel.json` and `api/index.py` in the root (already included).

### 2) Create Supabase Database

- In Supabase, create a project.
- Copy the **Connection string** from Database settings.
- Use the full Postgres URI as `DATABASE_URL` in Vercel.
  - This project normalizes `postgres://` and `postgresql://` automatically.

### 3) Create Clerk App

- Create your Clerk application.
- Copy:
  - `CLERK_PUBLISHABLE_KEY`
  - `CLERK_SECRET_KEY`
- Add both as environment variables in Vercel.

### 4) Configure Vercel Project

In Vercel Project -> Settings -> Environment Variables, add:

- `FLASK_CONFIG=vercel`
- `SECRET_KEY=<strong-random-secret>`
- `DATABASE_URL=<your-supabase-postgres-url>`
- `CLERK_PUBLISHABLE_KEY=<from-clerk>`
- `CLERK_SECRET_KEY=<from-clerk>`
- `SUPABASE_URL=<https://your-project.supabase.co>`
- `SUPABASE_ANON_KEY=<from-supabase>`
- `SUPABASE_SERVICE_ROLE_KEY=<from-supabase>`
- Optional mail/captcha vars if you use those features.

### 5) Deploy

- Import the GitHub repo into Vercel.
- Trigger deploy.
- On first requests, the app initializes database tables automatically.

### 6) Post-Deploy Validation

Verify these routes load:

- `/`
- `/about`
- `/shop`
- `/auth/login`

If something fails, check Vercel function logs and confirm env var names exactly match.

### Notes

- Static assets are served through Flask and Vercel routing in this repo setup.
- Product image upload endpoint is intentionally limited on Vercel serverless; use image URLs for products in production.

---

## ─── Project Structure

```
Looph.co-WebApp/
├── templates/          # HTML templates
│   ├── index.html     # Home page
│   ├── products.html  # Products listing
│   └── about.html     # About page
├── static/            # Static assets (if applicable)
│   ├── css/
│   ├── images/
│   └── js/
└── README.md          # Project documentation
```

---

## ─── Design Philosophy

Loophco embraces a **minimalist aesthetic** that prioritizes:

- **Clarity** - Every element serves a purpose
- **Elegance** - Simple yet sophisticated visuals
- **User Experience** - Intuitive navigation and flow
- **Scalability** - Foundation for future expansion

---

## ─── Contributing

Contributions are what make the open-source community amazing! Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## ─── License

This project is created for **portfolio and educational purposes**.

---

## ─── Contact

**Strix** - [@Strix-xy](https://github.com/Strix-xy)

Project Link: [https://github.com/Strix-xy/Looph.co-WebApp](https://github.com/Strix-xy/Looph.co-WebApp)

---

## ─── Acknowledgments

- Flask documentation and community
- Design inspiration from modern e-commerce platforms
- Open-source community for continuous learning

---

<div align="center">

**⭐ Star this repo if you find it useful! ⭐**

Made by [Strix](https://github.com/Strix-xy)

</div>
=======
# 👕 Eterno — Flask Clothing Shop Website

Eterno is a personal portfolio project showcasing a modern and minimal clothing shop website built using **Flask (Python)** and **HTML/CSS**.  
The project focuses on clean design, smooth navigation, and functional routing between pages.

---

## 🌟 Overview
Eterno represents a conceptual online store for clothing enthusiasts, serving as a demonstration of web design and Flask backend integration for portfolio purposes.  
It’s not a full e-commerce system but a showcase of how product pages, layouts, and navigation work in a structured web app.

---

## 🧩 Features
- Responsive and minimalist design
- Flask backend for routing and rendering HTML templates
- Internal CSS styling (within HTML templates)
- Organized navigation (Home, Products, About)
- Ready to expand with product data or user features

---

## ⚙️ Tech Stack

**Frontend:**
- HTML5 — structure and layout  
- CSS3 (internal styling) — responsive and aesthetic design  

**Backend:**
- Flask (Python) — lightweight web framework for routing and rendering templates  

**Development Tools:**
- Git + GitHub — version control and hosting  
- VS Code / Code::Blocks — code editor used  

---

## 🧱 Folder Structure
>>>>>>> 46808a6923ccfab414901225ffdbe3e25be8fb11
