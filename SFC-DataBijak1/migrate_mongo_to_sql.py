from pymongo import MongoClient
import pandas as pd
import logging
from config import MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION
from models import db, Ticker, Anomaly
from app import create_app
from sqlalchemy.exc import IntegrityError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_from_mongo(mongo_uri=None):
    mongo_uri = mongo_uri or MONGO_URI
    if not mongo_uri:
        return "Mongo URI not configured. Set MONGO_URI in environment or config.py"

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.server_info()  # Test connection
        db_m = client.get_database(MONGO_DB_NAME)
        coll = db_m.get_collection(MONGO_COLLECTION)

        docs = list(coll.find({}))
        if not docs:
            return "No documents found in Mongo collection."

        app = create_app()
        with app.app_context():
            db.create_all()

            # Insert or update tickers
            symbols = set(d.get('ticker') for d in docs if d.get('ticker'))
            for sym in symbols:
                if not sym or sym not in {'NVDA', 'MSFT', 'AAPL', 'GOOGL', 'AMZN', 'META', 'AVGO', 'TSM'}:
                    logger.warning(f"Skipping invalid ticker: {sym}")
                    continue
                t = Ticker.query.filter_by(symbol=sym).first()
                if not t:
                    t = Ticker(symbol=sym)
                    db.session.add(t)
            db.session.commit()
            logger.info(f"Initialized {len(symbols)} tickers in SQL.")

            # Bulk import anomalies
            anomalies_to_add = []
            imported = 0
            for d in docs:
                sym = d.get('ticker')
                if not sym:
                    logger.warning("Skipping document with no ticker.")
                    continue
                t = Ticker.query.filter_by(symbol=sym).first()
                if not t:
                    logger.warning(f"Ticker {sym} not found in SQL.")
                    continue

                date_str = d.get('date')
                try:
                    date_dt = pd.to_datetime(date_str).date()
                except (ValueError, TypeError):
                    logger.error(f"Invalid date for ticker {sym}: {date_str}")
                    continue

                # Check for existing record to avoid duplicates
                exists = Anomaly.query.filter_by(ticker_id=t.id, date=date_dt).first()
                if exists:
                    logger.info(f"Skipping existing anomaly for {sym} on {date_dt}")
                    continue

                # Prepare anomaly record
                meta = {k: v for k, v in d.items() if k not in ('_id', 'ticker', 'date', 'timestamp', 'close', 'anomaly', 'anomaly_score')}
                a = Anomaly(
                    ticker_id=t.id,
                    date=date_dt,
                    timestamp=pd.to_datetime(d.get('timestamp')) if d.get('timestamp') else None,
                    close=float(d.get('close')) if d.get('close') is not None else None,
                    anomaly=int(d.get('anomaly')) if d.get('anomaly') is not None else None,
                    anomaly_score=float(d.get('anomaly_score')) if d.get('anomaly_score') is not None else None,
                    meta=meta
                )
                anomalies_to_add.append(a)
                imported += 1

                # Commit in batches for performance
                if len(anomalies_to_add) >= 1000:
                    try:
                        db.session.bulk_save_objects(anomalies_to_add)
                        db.session.commit()
                        logger.info(f"Committed batch of {len(anomalies_to_add)} anomalies.")
                        anomalies_to_add = []
                    except IntegrityError as e:
                        db.session.rollback()
                        logger.error(f"Batch commit failed: {e}")
                        break

            # Commit remaining records
            if anomalies_to_add:
                try:
                    db.session.bulk_save_objects(anomalies_to_add)
                    db.session.commit()
                    logger.info(f"Committed final batch of {len(anomalies_to_add)} anomalies.")
                except IntegrityError as e:
                    db.session.rollback()
                    logger.error(f"Final commit failed: {e}")

            return f"Imported {imported} anomalies into SQL DB."

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return f"Migration failed: {str(e)}"
    finally:
        client.close()

if __name__ == '__main__':
    result = import_from_mongo()
    print(result)