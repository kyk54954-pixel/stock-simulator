from datetime import datetime


def process_auto_orders(db, AutoOrder, Portfolio, Transaction, User, ticker, price):
    orders = AutoOrder.query.filter_by(ticker=ticker.upper(), status='ACTIVE').all()
    executed = []
    for order in orders:
        if not (price >= order.target_price if order.trigger == 'ABOVE' else price <= order.target_price):
            continue
        user = User.query.get(order.user_id)
        holding = Portfolio.query.filter_by(user_id=user.id, ticker=order.ticker).first()
        total = price * order.quantity
        if order.action == 'BUY':
            if user.cash < total:
                order.status = 'CANCELLED'; continue
            if holding:
                holding.average_price = ((holding.average_price * holding.shares) + total) / (holding.shares + order.quantity)
                holding.shares += order.quantity
            else: db.session.add(Portfolio(user_id=user.id, ticker=order.ticker, shares=order.quantity, average_price=price))
            user.cash -= total; profit = 0
        else:
            if not holding or holding.shares < order.quantity:
                order.status = 'CANCELLED'; continue
            profit = (price - holding.average_price) * order.quantity; holding.shares -= order.quantity; user.cash += total
            if holding.shares == 0: db.session.delete(holding)
        db.session.add(Transaction(user_id=user.id, ticker=order.ticker, action=order.action, price=price, quantity=order.quantity, total=total, realized_profit=profit))
        order.status, order.executed_at, order.executed_price = 'EXECUTED', datetime.utcnow(), price
        executed.append({'id': order.id, 'action': order.action, 'quantity': order.quantity, 'price': price})
    if executed or any(o.status == 'CANCELLED' for o in orders): db.session.commit()
    return executed
