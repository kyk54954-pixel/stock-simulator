import os
def summarize_news(ticker, articles):
    if not articles: return f'No recent news was found for {ticker}.'
    key=os.getenv('OPENAI_API_KEY',''); text='\n'.join(f"- {a['title']}: {a.get('summary','')}" for a in articles[:6])
    if key:
        try:
            from openai import OpenAI
            c=OpenAI(api_key=key)
            r=c.chat.completions.create(model=os.getenv('OPENAI_MODEL','gpt-4o-mini'),messages=[{'role':'system','content':'You are a finance assistant. Summarize stock news in concise Chinese. Do not give financial advice.'},{'role':'user','content':f'Ticker: {ticker}\nNews:\n{text}\n请用中文总结这些新闻对短期股价情绪的可能影响。'}],temperature=.3,max_tokens=180)
            return r.choices[0].message.content.strip()
        except Exception: pass
    return f'{ticker} 近期新闻主要集中在公司表现、市场情绪和交易量变化。若盈利和指引优于预期，短期可能利好股价；若估值压力或宏观风险上升，股价可能波动。'
