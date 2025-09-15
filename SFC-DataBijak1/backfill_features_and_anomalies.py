# backfill_features_and_anomalies.py
import pandas as pd
import numpy as np
from app import create_app
from models import db, Ticker, Anomaly
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime
import math

# Toggle whether to compute anomaly_score via IsolationForest
RUN_ANOMALY_MODEL = True
ISOLATION_CONTAMINATION = 0.01  # tune

# RSI helper
def compute_rsi(series, window=14):
    # series: pd.Series of prices (float)
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def backfill_for_ticker(ticker_symbol):
    app = create_app()
    with app.app_context():
        t = Ticker.query.filter_by(symbol=ticker_symbol).first()
        if not t:
            print("Ticker not found:", ticker_symbol)
            return

        # Read anomaly rows for this ticker into DataFrame
        rows = Anomaly.query.filter_by(ticker_id=t.id).order_by(Anomaly.date.asc()).all()
        if not rows:
            print("No rows to process for", ticker_symbol)
            return

        df = pd.DataFrame([r.as_dict() for r in rows])
        # Parse date
        df['date'] = pd.to_datetime(df['date']).dt.date
        df = df.sort_values('date').reset_index(drop=True)

        # if 'close' is None for some rows, try to find non-null closes (otherwise abort)
        if df['close'].isna().all():
            print(f"Ticker {ticker_symbol}: no close prices available — cannot compute features.")
            return

        # We'll compute on float series
        df['close_f'] = pd.to_numeric(df['close'], errors='coerce')

        # Returns
        df['returns'] = df['close_f'].pct_change()

        # Moving averages on close
        df['ma_50'] = df['close_f'].rolling(window=50, min_periods=1).mean()
        df['ma_200'] = df['close_f'].rolling(window=200, min_periods=1).mean()

        # Volatility (rolling std of returns) - Vol_20
        df['vol_20'] = df['returns'].rolling(window=20, min_periods=1).std()

        # Volume-based features: try to use 'volume' if present in df; otherwise set NaN
        if 'volume' in df.columns:
            df['volume_f'] = pd.to_numeric(df['volume'], errors='coerce')
            df['volume_ma_20'] = df['volume_f'].rolling(window=20, min_periods=1).mean()
        else:
            df['volume_f'] = np.nan
            df['volume_ma_20'] = np.nan

        # RSI_14
        df['rsi_14'] = compute_rsi(df['close_f'], window=14)

        # Prepare model features (select numeric features, fillna)
        feature_cols = ['returns', 'ma_50', 'ma_200', 'vol_20', 'volume_ma_20', 'rsi_14']
        X = df[feature_cols].copy()
        # Replace infinities and NaNs with column median
        X = X.replace([np.inf, -np.inf], np.nan)
        for c in X.columns:
            median = X[c].median(skipna=True)
            if math.isnan(median):
                median = 0.0
            X[c] = X[c].fillna(median)

        # compute anomaly scores with IsolationForest if requested
        if RUN_ANOMALY_MODEL:
            scaler = StandardScaler()
            Xs = scaler.fit_transform(X)
            model = IsolationForest(contamination=ISOLATION_CONTAMINATION, random_state=42)
            model.fit(Xs)
            # decision_function: higher --> more normal, lower --> more anomalous
            scores = model.decision_function(Xs)  # larger = less anomalous
            # For readability invert so large = more anomalous (optional)
            anomaly_scores = -scores
            preds = model.predict(Xs)  # -1 anomaly, 1 normal
            df['anomaly_score_new'] = anomaly_scores
            df['anomaly_pred'] = preds
            # Convert preds to 1=anomaly, 0=normal
            df['anomaly_new'] = df['anomaly_pred'].apply(lambda v: 1 if int(v) == -1 else 0)
        else:
            df['anomaly_score_new'] = np.nan
            df['anomaly_new'] = df['anomaly'].apply(lambda v: int(v) if v is not None else None)

        # Now update the SQL rows (one-by-one) — safe and clear
        updated = 0
        for _, row in df.iterrows():
            date_val = pd.to_datetime(row['date']).date()
            a = Anomaly.query.filter_by(ticker_id=t.id, date=date_val).first()
            if not a:
                continue
            # map and update fields
            a.returns = float(row['returns']) if pd.notna(row['returns']) else None
            a.ma_50 = float(row['ma_50']) if pd.notna(row['ma_50']) else None
            a.ma_200 = float(row['ma_200']) if pd.notna(row['ma_200']) else None
            a.vol_20 = float(row['vol_20']) if pd.notna(row['vol_20']) else None
            a.volume_ma_20 = float(row['volume_ma_20']) if pd.notna(row['volume_ma_20']) else None
            a.rsi_14 = float(row['rsi_14']) if pd.notna(row['rsi_14']) else None
            # Optionally update open/high/low/adj_close/volume if present in df
            for col_map in [('open','open'), ('high','high'), ('low','low'),
                            ('adj_close','adj_close'), ('volume','volume'),
                            ('dividends','dividends'), ('stock_splits','stock_splits')]:
                field = col_map[0]
                if field in row and pd.notna(row[field]):
                    try:
                        setattr(a, field, float(row[field]))
                    except:
                        pass
            # anomaly fields from model
            if pd.notna(row.get('anomaly_score_new')):
                a.anomaly_score = float(row['anomaly_score_new'])
            # set anomaly flag if model computed, else keep existing
            if not pd.isna(row.get('anomaly_new')):
                a.anomaly = int(row['anomaly_new'])
            # save meta optionally
            # a.meta = a.meta or {}
            db.session.add(a)
            updated += 1

        db.session.commit()
        print(f"[{ticker_symbol}] Updated {updated} rows with derived features and anomaly scores.")

def main():
    app = create_app()
    with app.app_context():
        symbols = [t.symbol for t in Ticker.query.all()]
    print("Tickers to process:", symbols)
    for sym in symbols:
        backfill_for_ticker(sym)

if __name__ == "__main__":
    main()
