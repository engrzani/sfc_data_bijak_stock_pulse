import pandas as pd
import numpy as np
import os
from config import CSV_FILE
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from pathlib import Path

TOP_TICKERS = ['NVDA', 'MSFT', 'AAPL', 'GOOGL', 'AMZN', 'META', 'AVGO', 'TSM']

class DataLoader:
    def __init__(self):
        self.data = None
        self.anomalies = None
        self.load_data()

    def load_data(self):
        """Load and preprocess CSV (from .py logic)."""
        if not os.path.exists(CSV_FILE):
            raise FileNotFoundError(f"CSV not found at {CSV_FILE}. Place Stock_pulse.stock_db1.csv in static/data/.")
        
        self.data = pd.read_csv(CSV_FILE, index_col='date', parse_dates=True)
        self.data.index = pd.to_datetime(self.data.index)
        
        # Preprocess (simplified from .py)
        price_cols = ['open', 'high', 'low', 'close', 'adj_close', 'volume']
        for col in price_cols:
            if col in self.data.columns:
                self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
        self.data = self.data.dropna(subset=['close'])
        self.data = self.data.sort_index()
        
        # Filter anomalies
        self.anomalies = self.data[self.data['anomaly'] == 1].copy()
        
        print(f"Loaded {len(self.data)} rows for {len(TOP_TICKERS)} tickers. Anomalies: {len(self.anomalies)}")

    def get_ticker_data(self, ticker):
        """Get data for a ticker (from .py fetch logic simulation)."""
        return self.data[self.data['ticker'] == ticker].copy()

    def detect_anomalies_sample(self, df):
        """Sample anomaly detection (from .py; for demo)."""
        if len(df) < 100:
            return df  # Skip for small data
        features = ['close', 'volume']  # Simplified
        scaler = StandardScaler()
        X = scaler.fit_transform(df[features].fillna(0))
        iso = IsolationForest(contamination=0.05, random_state=42)
        df['anomaly'] = iso.fit_predict(X) == -1
        return df

# Global loader
loader = DataLoader()