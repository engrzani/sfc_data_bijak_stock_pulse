# # config.py
# MONGO_URI = "mongodb+srv://admin:admin@cluster0.n3rclmy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
# MONGO_DB_NAME = "Stock_pulse"
# MONGO_COLLECTION = "stock_db1"

# SQLALCHEMY_DATABASE_URI = "sqlite:///stockpulse.db"
# SQLALCHEMY_TRACK_MODIFICATIONS = False
# FLASK_SECRET = "change-me"

import os

# MongoDB (from original .py)
MONGO_URI = "mongodb+srv://admin:admin@cluster0.n3rclmy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGO_DB_NAME = "Stock_pulse"
MONGO_COLLECTION = "stock_db1"

# SQLAlchemy (SQLite for app metadata)
SQLALCHEMY_DATABASE_URI = "sqlite:///sfc_databank.db"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask
SECRET_KEY = os.environ.get('FLASK_SECRET') or 'your-updated-secret-key-change-in-prod'  # Updated from 'change-me'

# App paths
DATA_PATH = os.path.join(os.path.dirname(__file__), 'static', 'data')
CSV_FILE = os.path.join(DATA_PATH, 'Stock_pulse.stock_db1.csv')