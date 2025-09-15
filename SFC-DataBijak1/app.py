# # app.py
# from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
# import config
# import io, csv, pandas as pd
# from datetime import datetime
# import pipeline_stub  # keep your pipeline stub here
# from types import SimpleNamespace

# # import models inside factory to avoid circular imports on import-time
# def create_app():
#     from models import db, Ticker, Anomaly, RunLog

#     app = Flask(__name__)
#     app.config.from_object('config')
#     app.secret_key = getattr(config, 'FLASK_SECRET', 'dev-secret')
#     db.init_app(app)

#     # Ensure tables exist
#     with app.app_context():
#         db.create_all()

#     # Routes (defined inside factory)
#     @app.route('/')
#     def index():
#         tickers = Ticker.query.all()
#         counts = {t.symbol: len(t.anomalies) for t in tickers}
#         return render_template('index.html', tickers=tickers, counts=counts)

#     @app.route('/ticker/<symbol>')
#     def view_ticker(symbol):
#         ticker = Ticker.query.filter_by(symbol=symbol).first_or_404()
#         try:
#             page = int(request.args.get('page', 1))
#             if page < 1:
#                 page = 1
#         except:
#             page = 1
#         per_page = 50

#         base_q = Anomaly.query.filter_by(ticker_id=ticker.id).order_by(Anomaly.date.desc())
#         total = base_q.count()
#         items = base_q.offset((page - 1) * per_page).limit(per_page).all()

#         pagination = SimpleNamespace(
#             items=items,
#             page=page,
#             per_page=per_page,
#             total=total,
#             has_prev=page > 1,
#             has_next=(page * per_page) < total,
#             prev_num=page - 1 if page > 1 else None,
#             next_num=page + 1 if (page * per_page) < total else None
#         )

#         return render_template('ticker.html', ticker=ticker, anomalies=pagination)

#     @app.route('/anomalies')
#     def anomalies_list():
#         symbol = request.args.get('ticker')
#         date_from = request.args.get('from')
#         date_to = request.args.get('to')
#         q = Anomaly.query
#         if symbol:
#             t = Ticker.query.filter_by(symbol=symbol).first()
#             if t:
#                 q = q.filter_by(ticker_id=t.id)
#         if date_from:
#             q = q.filter(Anomaly.date >= pd.to_datetime(date_from).date())
#         if date_to:
#             q = q.filter(Anomaly.date <= pd.to_datetime(date_to).date())
#         results = q.order_by(Anomaly.date.desc()).limit(100).all()
#         rows = [r.as_dict() for r in results]
#         return render_template('anomalies.html', anomalies=rows)
#     @app.route('/download/anomalies.csv')
#     def download_anomalies_csv():
#         symbol = request.args.get('ticker')
#         q = Anomaly.query
#         if symbol:
#             t = Ticker.query.filter_by(symbol=symbol).first()
#             if t:
#                 q = q.filter_by(ticker_id=t.id)
#         rows = q.order_by(Anomaly.date.desc()).all()

#         cols = ['ticker','date','timestamp','open','high','low','close','adj_close','volume',
#                 'dividends','stock_splits','returns','ma_50','ma_200','vol_20','volume_ma_20',
#                 'rsi_14','anomaly_score','anomaly']

#         si = io.StringIO()
#         cw = csv.writer(si)
#         cw.writerow(cols)
#         for r in rows:
#             d = r.as_dict()
#             cw.writerow([d.get(c) for c in cols])
#         output = io.BytesIO()
#         output.write(si.getvalue().encode('utf-8'))
#         output.seek(0)
#         filename = f"anomalies_{symbol or 'all'}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
#         return send_file(output, mimetype='text/csv', as_attachment=True, download_name=filename)


#     @app.route('/api/anomalies/<symbol>')
#     def api_anomalies_symbol(symbol):
#         t = Ticker.query.filter_by(symbol=symbol).first_or_404()
#         rows = Anomaly.query.filter_by(ticker_id=t.id).order_by(Anomaly.date.desc()).limit(500).all()
#         return jsonify([r.as_dict() for r in rows])

#     @app.route('/trigger/<symbol>', methods=['POST'])
#     def trigger_pipeline(symbol):
#         t = Ticker.query.filter_by(symbol=symbol).first_or_404()
#         log = RunLog(ticker_id=t.id, action='pipeline_run', status='started')
#         db.session.add(log); db.session.commit()
#         try:
#             res = pipeline_stub.run_pipeline(symbol)
#             log.status = 'success'
#             log.message = res
#             db.session.commit()
#             flash(f"Pipeline run triggered for {symbol}: {res}", "success")
#         except Exception as e:
#             log.status = 'failed'
#             log.message = str(e)
#             db.session.commit()
#             flash(f"Pipeline run failed: {e}", "danger")
#         return redirect(url_for('view_ticker', symbol=symbol))

#     @app.route('/import/mongo-to-sql', methods=['POST'])
#     def import_mongo_to_sql():
#         from migrate_mongo_to_sql import import_from_mongo
#         result = import_from_mongo()
#         flash(result, "info")
#         return redirect(url_for('index'))
    
#     @app.route('/api/price_anomalies/<symbol>')
#     def api_price_anomalies(symbol):
#         t = Ticker.query.filter_by(symbol=symbol).first_or_404()
#         rows = Anomaly.query.filter_by(ticker_id=t.id).order_by(Anomaly.date.asc()).all()
#         data = []
#         for r in rows:
#             d = r.as_dict()
#             data.append(d)
#         return jsonify({"symbol": symbol, "data": data})



#     return app

# # Only run server when executing this file directly
# if __name__ == '__main__':
#     application = create_app()
#     application.run(debug=True, host='0.0.0.0', port=5000)
from flask import Flask, render_template, jsonify, request
from models import db, UserSession
from data_loader import loader, TOP_TICKERS
from config import MONGO_URI  # Optional Mongo
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

app = Flask(__name__)
app.config.from_pyfile('config.py')
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    """Nasdaq-like dashboard: Summary stats, top tickers table."""
    summary = {
        'total_rows': len(loader.data),
        'total_anomalies': len(loader.anomalies),
        'tickers': len(TOP_TICKERS),
        'top_tickers': loader.data.groupby('ticker')['close'].last().to_dict()
    
    }
    return render_template('index.html', summary=summary, tickers=TOP_TICKERS)



@app.route('/ticker/<symbol>')
def ticker(symbol):
    """Ticker details: Chart with anomalies (Nasdaq-style)."""
    if symbol not in TOP_TICKERS:
        return render_template('404.html'), 404
    
    df = loader.get_ticker_data(symbol)
    if df.empty:
        return render_template('404.html'), 404
    
    # Plotly chart (from .py plot_all_tickers logic, normalized)
    fig = make_subplots(specs=[[{"secondary_y": False}]])
    fig.add_trace(go.Scatter(x=df.index, y=df['close'], mode='lines', name='Close Price',
                             line=dict(color='#003366')), secondary_y=False)
    anomalies = df[df['anomaly'] == 1]
    if not anomalies.empty:
        fig.add_trace(go.Scatter(x=anomalies.index, y=anomalies['close'], mode='markers',
                                 name='Anomalies', marker=dict(color='red', size=10, symbol='x')), secondary_y=False)
    
    fig.update_layout(title=f'{symbol} Stock Price & Anomalies', 
                      xaxis_title='Date', yaxis_title='Price (USD)',
                      template='plotly_white', height=600)
    chart_html = fig.to_html(full_html=False)
    print(df.tail().to_dict('records'))
    return render_template('ticker.html', symbol=symbol, chart=chart_html, data=df.tail().to_dict('records'))

@app.route('/anomalies')
def anomalies():
    """Anomalies table with filters (search by ticker/date)."""
    df = loader.anomalies.copy()
    ticker_filter = request.args.get('ticker', '')
    if ticker_filter:
        df = df[df['ticker'] == ticker_filter]
    
    return render_template('anomalies.html', anomalies=df.to_dict('records'), tickers=TOP_TICKERS)

@app.route('/reports')
def reports():
    """Anomaly detection metrics summary (from .py results)."""
    # Hardcoded sample metrics from .py (in prod, load from saved CSV/JSON)
    # Add metrics for all tickers in TOP_TICKERS (dummy values for illustration)
    metrics = [
        {'ticker': ticker, 'precision': round(0.8 + i*0.01, 2), 'recall': round(0.75 + i*0.01, 2), 'f1': round(0.77 + i*0.01, 2)}
        for i, ticker in enumerate(TOP_TICKERS)
    ]
    return render_template('reports.html', metrics=metrics)

@app.route('/api/anomalies/<ticker>')
def api_anomalies(ticker):
    """JSON API for anomalies (for dynamic charts)."""
    df = loader.anomalies[loader.anomalies['ticker'] == ticker]
    return jsonify(df.to_dict('records'))

# In app.py
def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    from models import db
    db.init_app(app)  # Move here
    with app.app_context():
        db.create_all()
    return app

if __name__ == '__main__':
    app.run(debug=True)