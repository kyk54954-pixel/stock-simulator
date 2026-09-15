from datetime import date
from functools import wraps
import sys
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from config import Config
db = SQLAlchemy()
sys.modules.setdefault('app', sys.modules[__name__])

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    from models.user import User
    from models.portfolio import Portfolio
    from models.transaction import Transaction
    from models.watchlist import Watchlist
    from models.auto_order import AutoOrder
    from services.stock_service import get_quote, get_history, get_intraday_simulation, get_historical_intraday, search_stocks, get_all_stocks, get_market_overview, get_market_stocks
    from services.news_service import get_finance_news
    from services.ai_summary import summarize_news
    from services.auto_trade_service import process_auto_orders
    with app.app_context(): db.create_all()

    def login_required(fn):
        @wraps(fn)
        def wrap(*a, **kw):
            if 'user_id' not in session:
                flash('Please login first.', 'warning'); return redirect(url_for('login'))
            return fn(*a, **kw)
        return wrap

    def current_user(): return User.query.get(session.get('user_id')) if session.get('user_id') else None

    def stats_for(user):
        positions=[]; portfolio_value=0
        for p in Portfolio.query.filter_by(user_id=user.id).all():
            q=get_quote(p.ticker); mv=q['price']*p.shares; cost=p.average_price*p.shares; profit=mv-cost; portfolio_value+=mv
            positions.append({'ticker':p.ticker,'company':q['company'],'shares':p.shares,'average_price':p.average_price,'current_price':q['price'],'market_value':mv,'profit':profit,'profit_percent':profit/cost*100 if cost else 0,'market_cap':q['market_cap'],'volume':q['volume']})
        today=Transaction.query.filter(Transaction.user_id==user.id, db.func.date(Transaction.created_at)==date.today().isoformat()).all()
        total=user.cash+portfolio_value
        return {'cash':user.cash,'portfolio_value':portfolio_value,'total_asset':total,'today_profit':sum(t.realized_profit for t in today),'overall_profit':total-user.initial_cash,'positions':positions}

    @app.route('/')
    def index(): return redirect(url_for('dashboard' if session.get('user_id') else 'login'))

    @app.route('/register', methods=['GET','POST'])
    def register():
        if request.method=='POST':
            username=request.form.get('username','').strip(); email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
            if len(username)<3 or len(password)<6 or '@' not in email:
                flash('Invalid input. Password must be at least 6 characters.', 'danger'); return render_template('register.html')
            if User.query.filter((User.username==username)|(User.email==email)).first():
                flash('Username or email already exists.', 'danger'); return render_template('register.html')
            db.session.add(User(username=username,email=email,password_hash=generate_password_hash(password))); db.session.commit(); flash('Account created. Please login.', 'success'); return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/login', methods=['GET','POST'])
    def login():
        if request.method=='POST':
            user=User.query.filter_by(username=request.form.get('username','').strip()).first()
            if user and check_password_hash(user.password_hash, request.form.get('password','')):
                session.clear(); session['user_id']=user.id; session['username']=user.username; return redirect(url_for('dashboard'))
            flash('Invalid username or password.', 'danger')
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout(): session.clear(); return redirect(url_for('login'))

    @app.route('/markets')
    @login_required
    def markets():
        return render_template('markets.html', indexes=get_market_overview(), stocks=get_market_stocks())

    @app.route('/watchlist')
    @login_required
    def watchlist():
        rows=Watchlist.query.filter_by(user_id=session['user_id']).order_by(Watchlist.ticker).all()
        quotes=[get_quote(row.ticker) for row in rows]
        return render_template('watchlist.html', quotes=quotes)

    @app.route('/watchlist/add/<ticker>')
    @login_required
    def add_watchlist(ticker):
        symbol=ticker.upper().strip()
        if symbol and not Watchlist.query.filter_by(user_id=session['user_id'], ticker=symbol).first():
            db.session.add(Watchlist(user_id=session['user_id'], ticker=symbol)); db.session.commit()
        return redirect(request.referrer or url_for('watchlist'))

    @app.route('/watchlist/remove/<ticker>')
    @login_required
    def remove_watchlist(ticker):
        row=Watchlist.query.filter_by(user_id=session['user_id'], ticker=ticker.upper().strip()).first()
        if row: db.session.delete(row); db.session.commit()
        return redirect(url_for('watchlist'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        user=current_user(); s=stats_for(user); leaderboard=[]
        for u in User.query.all():
            user_stats=stats_for(u); leaderboard.append({'username':u.username,'asset':user_stats['total_asset'],'profit':user_stats['overall_profit']})
        leaderboard.sort(key=lambda x:x['profit'], reverse=True)
        return render_template('dashboard.html', user=user, stats=s, leaderboard=leaderboard)

    @app.route('/trade', methods=['GET','POST'])
    @login_required
    def trade():
        user=current_user(); ticker=request.values.get('ticker','1155.KL').strip().upper()
        if request.method=='POST':
            action=request.form.get('action'); ticker=request.form.get('ticker','').strip().upper()
            try: qty=int(request.form.get('quantity','0'))
            except ValueError: qty=0
            if not ticker or qty<=0: flash('Enter a valid ticker and quantity.', 'danger'); return redirect(url_for('trade', ticker=ticker or '1155.KL'))
            q=get_quote(ticker); price=q['price']; total=price*qty; h=Portfolio.query.filter_by(user_id=user.id,ticker=ticker).first()
            if action=='BUY':
                if user.cash<total: flash('Not enough cash.', 'danger'); return redirect(url_for('trade', ticker=ticker))
                if h: h.average_price=((h.average_price*h.shares)+total)/(h.shares+qty); h.shares+=qty
                else: db.session.add(Portfolio(user_id=user.id,ticker=ticker,shares=qty,average_price=price))
                user.cash-=total; db.session.add(Transaction(user_id=user.id,ticker=ticker,action='BUY',price=price,quantity=qty,total=total))
            elif action=='SELL':
                if not h or h.shares<qty: flash('Not enough shares.', 'danger'); return redirect(url_for('trade', ticker=ticker))
                profit=(price-h.average_price)*qty; h.shares-=qty; user.cash+=total
                if h.shares==0: db.session.delete(h)
                db.session.add(Transaction(user_id=user.id,ticker=ticker,action='SELL',price=price,quantity=qty,total=total,realized_profit=profit))
            db.session.commit(); return redirect(url_for('trade', ticker=ticker))
        q=get_quote(ticker); news=get_finance_news(ticker)
        return render_template('trade.html', quote=q, chart_data=get_history(ticker), news=news)

    @app.route('/auto-orders', methods=['GET', 'POST'])
    @login_required
    def auto_orders():
        user = current_user()
        if request.method == 'POST':
            ticker = request.form.get('ticker', '').upper().strip()
            action = request.form.get('action', 'BUY').upper()
            trigger = request.form.get('trigger', 'BELOW').upper()
            try:
                quantity = int(request.form.get('quantity', '0'))
                target_price = float(request.form.get('target_price', '0'))
            except ValueError:
                quantity, target_price = 0, 0
            if ticker and action in {'BUY', 'SELL'} and trigger in {'ABOVE', 'BELOW'} and quantity > 0 and target_price > 0:
                db.session.add(AutoOrder(user_id=user.id, ticker=ticker, action=action, quantity=quantity, trigger=trigger, target_price=target_price))
                db.session.commit(); flash('Automatic order is now active.', 'success')
            else: flash('Enter a valid symbol, quantity, and trigger price.', 'danger')
            return redirect(url_for('auto_orders'))
        orders = AutoOrder.query.filter_by(user_id=user.id).order_by(AutoOrder.created_at.desc()).all()
        return render_template('auto_orders.html', orders=orders)

    @app.route('/auto-orders/<int:order_id>/cancel', methods=['POST'])
    @login_required
    def cancel_auto_order(order_id):
        order = AutoOrder.query.filter_by(id=order_id, user_id=session['user_id'], status='ACTIVE').first_or_404()
        order.status = 'CANCELLED'; db.session.commit(); flash('Automatic order cancelled.', 'success')
        return redirect(url_for('auto_orders'))

    @app.route('/portfolio')
    @login_required
    def portfolio():
        s=stats_for(current_user()); key=request.args.get('sort','ticker'); key=key if key in {'ticker','shares','market_value','profit'} else 'ticker'
        return render_template('portfolio.html', stats=s, positions=sorted(s['positions'], key=lambda x:x[key], reverse=key!='ticker'), sort_key=key)

    @app.route('/history')
    @login_required
    def history(): return render_template('history.html', transactions=Transaction.query.filter_by(user_id=session['user_id']).order_by(Transaction.created_at.desc()).all())

    @app.route('/news')
    @login_required
    def news():
        ticker=request.args.get('ticker','1155.KL').strip().upper(); articles=get_finance_news(ticker)
        return render_template('news.html', ticker=ticker, articles=articles, quote=get_quote(ticker), chart_data=get_history(ticker))

    @app.route('/api/quote/<ticker>')
    @login_required
    def api_quote(ticker):
        quote = get_quote(ticker.upper())
        executed = process_auto_orders(db, AutoOrder, Portfolio, Transaction, User, quote['ticker'], quote['price']) if quote.get('data_available') else []
        return jsonify({**quote, 'auto_orders_executed': executed})
    @app.route('/api/history/<ticker>')
    @login_required
    def api_history(ticker): return jsonify(get_history(ticker.upper()))
    @app.route('/api/intraday/<ticker>')
    @login_required
    def api_intraday(ticker): return jsonify(get_intraday_simulation(ticker.upper()))
    @app.route('/api/history-day/<ticker>/<int:days_ago>')
    @login_required
    def api_history_day(ticker, days_ago): return jsonify(get_historical_intraday(ticker.upper(), days_ago))
    @app.route('/api/stocks')
    @login_required
    def api_stocks(): return jsonify(get_all_stocks())

    @app.route('/api/search')
    @login_required
    def api_search(): return jsonify(search_stocks(request.args.get('q','')))
    @app.route('/api/news/<ticker>')
    @login_required
    def api_news(ticker):
        articles=get_finance_news(ticker.upper()); return jsonify({'articles':articles,'summary':summarize_news(ticker.upper(),articles)})
    return app

if __name__=='__main__': create_app().run(debug=True)
