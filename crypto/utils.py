import ccxt
import pandas as pd
from key import api_key, secret
from logger import logger
import datetime

target_crypto = 'ETH'
target_currency = 'USDT'
target_symbol = f'{target_crypto}/{target_currency}'
defaultType = 'margin'
leverage = 1

# API 연동
binance = ccxt.binance(
    config={'apiKey': api_key, 'secret': secret, 'enableRateLimit': True, 'options': {'defaultType': defaultType}}
)

markets = binance.load_markets()
market = binance.market(target_symbol)
resp = binance.fapiPrivate_post_leverage({'symbol': market['id'], 'leverage': leverage})


# 잔고 확인
def get_balance(target='USDT'):
    balance = binance.fetch_balance(params={'type': defaultType})[target]
    return balance


# 현재 주문가능 수량 확인
def get_max_order_amount():
    free = get_balance()['free']
    current = get_current()
    return round(free / current * leverage, 3)


# 주문
def order(amount, type):
    order_success = False
    try:
        if type == 'long':
            binance.create_market_buy_order(symbol=target_symbol, amount=amount)
        elif type == 'short':
            binance.create_market_sell_order(symbol=target_symbol, amount=amount)
        while True:
            if is_open_order():
                logger.info(f'{datetime.datetime.utcnow()} Cannot {type}, still open')
            else:
                break
        order_success = True

    except Exception as e:
        logger.error(e)

    return order_success


# 미체결 True or False
def is_open_order():
    return True if binance.fetch_open_orders(symbol=target_symbol) else False


# 포지션 조회
def get_position():
    try:
        positions = binance.fetch_positions()
        for position in positions:
            if position['symbol'] == target_symbol:
                return {**position['info'], 'side': position['side']}
        return {}
    except Exception as e:
        logger.error(e)
        return {}


# 현재가 조회
def get_current():
    crypto = binance.fetch_ticker(target_symbol)['last']
    return crypto


# 과거 데이터 조회
def get_ohlcv(timeframe='5m', limit=50):
    crypto = binance.fetch_ohlcv(symbol=target_symbol, timeframe=timeframe, since=None, limit=limit)
    df = pd.DataFrame(crypto, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    return df

def get_amount(distribution):
    return round((get_balance(target_currency)['total'] / get_current() * leverage + get_balance(target_crypto)['total'])/ distribution, 3)
