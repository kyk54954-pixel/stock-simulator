"""Malaysia-company news feeds for Bursa Malaysia paper trading."""
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET
import os
import requests

COMPANIES = {
    '1155.KL':'Malayan Banking Berhad Maybank', '1295.KL':'Public Bank Berhad',
    '1023.KL':'CIMB Group Holdings', '5819.KL':'Hong Leong Bank Berhad',
    '5347.KL':'Tenaga Nasional Berhad', '4863.KL':'Telekom Malaysia Berhad',
    '6947.KL':'CelcomDigi Berhad', '4715.KL':'Genting Berhad',
    '3182.KL':'Genting Malaysia Berhad', '4197.KL':'Sime Darby Berhad',
    '1961.KL':'IOI Corporation Berhad', '5284.KL':'IHH Healthcare Berhad',
    '1066.KL':'RHB Bank Berhad', '5168.KL':'Hartalega Holdings Berhad',
    '7084.KL':'QL Resources Berhad'
}

MALAYSIAN_NEWS_SITES = (
    '(site:theedgemalaysia.com OR site:thestar.com.my OR site:bernama.com '
    'OR site:themalaysianreserve.com OR site:nst.com.my/business '
    'OR site:malaymail.com/news/money OR site:freemalaysiatoday.com/category/business '
    'OR site:businesstoday.com.my OR site:bursamalaysia.com)'
)

def _article(title, source, url, summary='', published_at=''):
    return {'title':title, 'source':source, 'url':url, 'summary':summary,
            'published_at':published_at or datetime.utcnow().strftime('%Y-%m-%d %H:%M')}

def _google_malaysia_news(company):
    """Search the Malaysia edition of Google News for local-business reporting."""
    query = f'{company} Bursa Malaysia {MALAYSIAN_NEWS_SITES}'
    response = requests.get('https://news.google.com/rss/search', params={
        'q':query, 'hl':'en-MY', 'gl':'MY', 'ceid':'MY:en'
    }, headers={'User-Agent':'Mozilla/5.0'}, timeout=10)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    articles = []
    for item in root.findall('./channel/item')[:8]:
        title = item.findtext('title', 'Malaysia market update')
        link = item.findtext('link', '')
        source_node = item.find('source')
        source = source_node.text if source_node is not None else 'Google News Malaysia'
        published = item.findtext('pubDate', '')
        try: published = parsedate_to_datetime(published).strftime('%Y-%m-%d %H:%M')
        except Exception: pass
        if link: articles.append(_article(title, source, link, item.findtext('description', ''), published))
    return articles

def get_finance_news(ticker):
    symbol = ticker.upper().strip()
    company = COMPANIES.get(symbol, symbol.replace('.KL', '') + ' Bursa Malaysia')
    try:
        articles = _google_malaysia_news(company)
        if articles: return articles
    except Exception:
        pass
    # Optional paid news APIs can be configured in .env, but never generate fake headlines.
    key = os.getenv('NEWS_API_KEY', '')
    if key:
        try:
            response = requests.get('https://newsapi.org/v2/everything', params={
                'q':company, 'language':'en', 'sortBy':'publishedAt', 'pageSize':8, 'apiKey':key
            }, timeout=10)
            response.raise_for_status()
            return [_article(item.get('title') or 'Malaysia market update', item.get('source', {}).get('name') or 'NewsAPI',
                             item.get('url', ''), item.get('description', ''), item.get('publishedAt', '')[:16])
                    for item in response.json().get('articles', []) if item.get('url')]
        except Exception:
            pass
    return []
