from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# UserSession model (from initial context)
class UserSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    last_ticker = db.Column(db.String(10), default='NVDA')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<UserSession {self.session_id}: {self.last_ticker}>'

# Ticker model (for migration)
class Ticker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), unique=True, nullable=False)
    anomalies = db.relationship('Anomaly', backref='ticker', lazy=True)

    def __repr__(self):
        return f'<Ticker {self.symbol}>'

# Anomaly model (for migration)
class Anomaly(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker_id = db.Column(db.Integer, db.ForeignKey('ticker.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    timestamp = db.Column(db.DateTime)
    close = db.Column(db.Float)
    anomaly = db.Column(db.Integer)  # 1 or 0
    anomaly_score = db.Column(db.Float)
    meta = db.Column(db.JSON)  # Store extra fields like volume, open, etc.

    def __repr__(self):
        return f'<Anomaly {self.ticker_id} on {self.date}>'