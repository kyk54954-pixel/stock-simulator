"""Yahoo Finance-backed Bursa Malaysia quotes for personal coursework use only."""
from datetime import date, datetime, timedelta
from functools import lru_cache
from html import unescape
import math
from pathlib import Path
import re
import time

import requests
import yfinance as yf

# yfinance stores ticker time zones in SQLite. Keep that cache in the project
# instead of the user profile so it also works in restricted school computers.
_YFINANCE_CACHE = Path(__file__).resolve().parent.parent / 'instance' / 'yfinance'
_YFINANCE_CACHE.mkdir(parents=True, exist_ok=True)
yf.set_tz_cache_location(str(_YFINANCE_CACHE))

STOCKS = [
    {'ticker':'1155.KL','company':'Malayan Banking Berhad','exchange':'BURSA','sector':'Financial Services'}, {'ticker':'1295.KL','company':'Public Bank Berhad','exchange':'BURSA','sector':'Financial Services'},
    {'ticker':'1023.KL','company':'CIMB Group Holdings Berhad','exchange':'BURSA','sector':'Financial Services'}, {'ticker':'5819.KL','company':'Hong Leong Bank Berhad','exchange':'BURSA','sector':'Financial Services'},
    {'ticker':'5347.KL','company':'Tenaga Nasional Berhad','exchange':'BURSA','sector':'Utilities'}, {'ticker':'4863.KL','company':'Telekom Malaysia Berhad','exchange':'BURSA','sector':'Telecommunications'},
    {'ticker':'6947.KL','company':'CelcomDigi Berhad','exchange':'BURSA','sector':'Telecommunications'}, {'ticker':'4715.KL','company':'Genting Berhad','exchange':'BURSA','sector':'Consumer Services'},
    {'ticker':'3182.KL','company':'Genting Malaysia Berhad','exchange':'BURSA','sector':'Consumer Services'}, {'ticker':'4197.KL','company':'Sime Darby Berhad','exchange':'BURSA','sector':'Industrials'},
    {'ticker':'1961.KL','company':'IOI Corporation Berhad','exchange':'BURSA','sector':'Plantation'}, {'ticker':'5284.KL','company':'IHH Healthcare Berhad','exchange':'BURSA','sector':'Healthcare'},
    {'ticker':'1066.KL','company':'RHB Bank Berhad','exchange':'BURSA','sector':'Financial Services'}, {'ticker':'5168.KL','company':'Hartalega Holdings Berhad','exchange':'BURSA','sector':'Healthcare'},
    {'ticker':'7084.KL','company':'QL Resources Berhad','exchange':'BURSA','sector':'Consumer Staples'}]
INDEXES = [{'ticker':'^KLSE','company':'FTSE Bursa Malaysia KLCI','exchange':'INDEX','sector':'Index'}]
QUOTE_TTL_SECONDS = 60
BURSA_DIVIDEND_TTL_SECONDS = 6 * 60 * 60

def _catalogue(symbol): return next((item for item in STOCKS + INDEXES if item['ticker'] == symbol), None)

def _number(value, default=0):
    try: return float(value) if value is not None and not math.isnan(float(value)) else default
    except (TypeError, ValueError): return default

def _unavailable(symbol, message='Yahoo Finance quote is unavailable right now.'):
    return {'ticker':symbol,'company':symbol,'exchange':'BURSA','price':0,'previous_close':0,'change':0,'change_percent':0,'market_cap':0,'volume':0,'open':0,'day_high':0,'day_low':0,'bid':0,'ask':0,'sector':'N/A','industry':'N/A','website':'','pe_ratio':0,'eps':0,'dividend_yield':0,'fifty_two_week_high':0,'fifty_two_week_low':0,'summary':'Delayed Yahoo Finance data for personal coursework only.','data_available':False,'data_error':message}

def _plain_text(markup):
    return re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', ' ', markup))).strip()

@lru_cache(maxsize=128)
def _bursa_ttm_dividend_per_share(symbol, cache_slot):
    """Get the last 12 months of declared cash dividends from Bursa Malaysia."""
    code = symbol.removesuffix('.KL')
    try:
        profile_url = ('https://www.bursamalaysia.com/trade/trading_resources/'
                       f'listing_directory/company-profile?stock_code={code}')
        profile = requests.get(profile_url, timeout=8,
                               headers={'User-Agent': 'StockSimulator/1.0'}).text
        announcement_ids = list(dict.fromkeys(re.findall(
            r'announcement_details\?ann_id=(\d+)&(?:amp;)?corporate_action=1', profile)))
        if not announcement_ids:
            return None

        cutoff = date.today() - timedelta(days=365)
        total = 0.0
        found = False
        for announcement_id in announcement_ids[:6]:
            notice = requests.get(
                f'https://disclosure.bursamalaysia.com/FileAccess/viewHtml?e={announcement_id}',
                timeout=8, headers={'User-Agent': 'StockSimulator/1.0'}).text
            text = _plain_text(notice)
            ex_date_match = re.search(r'Ex-Date\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})', text)
            amount_match = re.search(
                r'Entitlement in Currency\s+Malaysian Ringgit\s*\(MYR\)\s+([0-9]+(?:\.[0-9]+)?)',
                text)
            if not ex_date_match or not amount_match:
                continue
            ex_date = datetime.strptime(ex_date_match.group(1), '%d %b %Y').date()
            if cutoff <= ex_date <= date.today():
                total += float(amount_match.group(1))
                found = True
        return round(total, 4) if found else 0.0
    except (requests.RequestException, ValueError):
        return None

def _bursa_dividend_yield(symbol, price):
    if price <= 0:
        return None
    dividend = _bursa_ttm_dividend_per_share(
        symbol, int(time.time() // BURSA_DIVIDEND_TTL_SECONDS))
    return round(dividend / price * 100, 2) if dividend is not None else None

@lru_cache(maxsize=128)
def _quote_cached(symbol, cache_slot):
    stock = _catalogue(symbol)
    if not stock: return _unavailable(symbol, 'This symbol is not in the Bursa catalogue.')
    try:
        ticker = yf.Ticker(symbol); fast = ticker.fast_info
        history = ticker.history(period='5d', interval='1d', auto_adjust=False)
        if history.empty: return _unavailable(symbol)
        latest = history.iloc[-1]; previous = history.iloc[-2] if len(history) > 1 else latest
        price = _number(fast.get('last_price'), _number(latest.get('Close'))); previous_close = _number(fast.get('previous_close'), _number(previous.get('Close')))
        change = price - previous_close; info = ticker.info
        return {'ticker':symbol,'company':info.get('longName') or stock['company'],'exchange':stock['exchange'],'price':round(price,2),'previous_close':round(previous_close,2),'change':round(change,2),'change_percent':round((change / previous_close * 100) if previous_close else 0,2),'market_cap':round(_number(fast.get('market_cap'),_number(info.get('marketCap'))),2),'volume':int(_number(fast.get('last_volume'),_number(latest.get('Volume')))),'open':round(_number(fast.get('open'),_number(latest.get('Open'))),2),'day_high':round(_number(fast.get('day_high'),_number(latest.get('High'))),2),'day_low':round(_number(fast.get('day_low'),_number(latest.get('Low'))),2),'bid':0,'ask':0,'sector':info.get('sector') or stock['sector'],'industry':info.get('industry') or stock['sector'],'website':info.get('website',''),'pe_ratio':round(_number(info.get('trailingPE')),2),'eps':round(_number(info.get('trailingEps')),2),'dividend_yield':_bursa_dividend_yield(symbol, price),'dividend_yield_source':'Bursa Malaysia (TTM)','fifty_two_week_high':round(_number(info.get('fiftyTwoWeekHigh')),2),'fifty_two_week_low':round(_number(info.get('fiftyTwoWeekLow')),2),'summary':'Yahoo Finance delayed market data for personal coursework only.','data_available':price > 0,'data_error':''}
    except Exception: return _unavailable(symbol)

def get_quote(ticker): return _quote_cached(ticker.upper().strip(), int(time.time() // QUOTE_TTL_SECONDS))

def _chart(symbol, period, interval, date_format):
    if not _catalogue(symbol): return {'labels':[], 'prices':[], 'data_available':False}
    try:
        rows = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=False)
        if rows.empty: return {'labels':[], 'prices':[], 'data_available':False}
        return {'labels':[item.strftime(date_format) for item in rows.index],'prices':[round(_number(value),2) for value in rows['Close']],'data_available':True}
    except Exception: return {'labels':[], 'prices':[], 'data_available':False}

def get_history(ticker): return _chart(ticker.upper().strip(), '2mo', '1d', '%Y-%m-%d')
def get_intraday_simulation(ticker): return _chart(ticker.upper().strip(), '1d', '30m', '%H:%M')

def get_historical_intraday(ticker, days_ago):
    symbol=ticker.upper().strip()
    if not _catalogue(symbol) or not 0 <= days_ago <= 29:
        return {'labels':[], 'prices':[], 'data_available':False}
    try:
        # The slider represents the most recent 30 *trading* days, not calendar
        # days. This prevents weekends and Bursa holidays from producing empty charts.
        daily=yf.Ticker(symbol).history(period='3mo', interval='1d', auto_adjust=False)
        if len(daily) <= days_ago:
            return {'labels':[], 'prices':[], 'data_available':False}
        target_day=daily.index[-(days_ago + 1)].date()
        rows=yf.Ticker(symbol).history(start=target_day,end=target_day+timedelta(days=1),interval='30m',auto_adjust=False)
        if rows.empty: return {'labels':[], 'prices':[], 'date':target_day.isoformat(), 'data_available':False}
        return {'labels':[item.strftime('%Y-%m-%d %H:%M') for item in rows.index],'prices':[round(_number(value),2) for value in rows['Close']],'date':target_day.isoformat(),'data_available':True}
    except Exception: return {'labels':[], 'prices':[], 'data_available':False}

def search_stocks(query):
    term=query.upper().strip(); return [item for item in STOCKS if not term or term in item['ticker'] or term in item['company'].upper()]
def get_all_stocks(): return sorted(STOCKS, key=lambda item:item['ticker'])
def get_market_overview(): return [get_quote(item['ticker']) for item in INDEXES]
def get_market_stocks(limit=12):
    """Return selected market shares together with their daily change."""
    rows = []
    for stock in get_all_stocks()[:limit]:
        quote = get_quote(stock['ticker'])
        # Guarantee the fields used by Markets if a quote response is incomplete.
        rows.append({**stock, **quote, 'price': quote.get('price', 0),
                     'change': quote.get('change', 0),
                     'change_percent': quote.get('change_percent', 0)})
    return rows
