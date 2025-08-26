
# Budget Management App

This is a web application built with **Flask** and **SQLite** that allows users to manage budgets easily and efficiently.  
It was designed to be lightweight, simple, and easy to deploy.

## 🚀 Features
- Manage budgets with CRUD operations (Create, Read, Update, Delete).
- User roles:
  - **Admin**: Full control of the application.
  - **Client**: Can access and extract budgets.
- Responsive design for desktop and mobile devices.
- Persistent data storage using SQLite SQLite locally
  for development, but switches to PostgreSQL in production.

## 🛠️ Technologies Used
- **Python 3.12** – Main programming language
- **Flask 3.1** – Web framework
- **Flask-SQLAlchemy** – ORM for database interactions
- **SQLite** – Local development database
- **PostgreSQL** – Production database (Railway)
- **Gunicorn** – WSGI HTTP server for deployment
- **psycopg2-binary** – PostgreSQL driver
- **python-dotenv** – Environment variables management
- **Flask-Limiter** – Rate limiting for security
- **Flask-Talisman** – Security headers (CSP, HTTPS, etc.)

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/budget-app.git
   cd budget-app
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   flask run
   ```

4. Access the app in your browser at:
   ```
   http://127.0.0.1:5000
   ```

## 🔑 Default Users
Upon the first deployment, the database creates two users:
- **Admin** → `admin / admin123`
- **Client** → `client / client123`

> ⚠️ It is highly recommended to **change the default passwords immediately** after deployment for security reasons.

## 📂 Project Structure
```
budget-app/
│── app/                # Main application package
│   ├── templates/      # HTML templates
│   ├── routes          # App routes
│   ├── models          # Database models
│   ├── helpers.py      # Auxiliary functions
│── instance/           # SQLite database (presupuestos.db)
│── run.py              # App entry point
│── requirements.txt    # Project dependencies
│── README.md           # Documentation
```

## ☁️ Deployment
The application can be deployed easily on **Railway** or other platforms that support Flask + SQLite.

## 📜 License
This project is open-source and available under the MIT License.
