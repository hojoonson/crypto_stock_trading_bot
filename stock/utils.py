from PyQt5 import QtTest
from slacker import Slacker
from config import SLACKER_KEY, SLACK_MESSAGE_KEY
import datetime
slack = Slacker(SLACKER_KEY)

# slack message send
def send_to_slack(message):
    try:
        print(message)
        slack.chat.post_message(SLACK_MESSAGE_KEY, message)
    except Exception as e:
        print(e)

def calculate_delta(this_price):
    # 어느정도 마진을 둬서 delta를 정함. 가격이 넘어가버릴수도 있기 때문.
    if this_price < 900:
        delta = 1
    elif 900 <= this_price < 4900:
        delta = 5
    elif 4900 <= this_price < 9900:
        delta = 10
    elif 9900 <= this_price < 49500:
        delta = 50
    elif 49500 <= this_price < 99500:
        delta = 100
    elif 99500 <= this_price < 490000:
        delta = 500
    else:
        delta = 1000
    return delta

def buy(IndiWindow, TARGET_SYMBOL, available_money, current_price, cost):
    DELTA = calculate_delta(current_price)
    order_price = int(current_price + cost) + DELTA - int(current_price + cost) % DELTA

    # # 넉넉한 조건에 부합하지 못하면 order count를 낮춤
    order_count = int(available_money/order_price)
    if (order_price + cost) * order_count + 1000 > available_money:
        order_count -= 1
    # order_count = 1  # 일단 1개씩 사는걸로 테스트
    IndiWindow.request_data(request_type='buy', target_symbol=TARGET_SYMBOL, count=order_count, order_price=order_price)
    send_to_slack = True
    return order_count, send_to_slack

def sell(IndiWindow, TARGET_SYMBOL, order_count):
    IndiWindow.request_data(request_type='sell', target_symbol=TARGET_SYMBOL, count=order_count)
    order_count = 0
    send_to_slack = True
    return order_count, send_to_slack

# PyQt Thread 용 sleep 함수
def sleep(n):
    QtTest.QTest.qWait(n)

# 거래량 기반 종목 선정.
def request_symbol():
    result = [
        ["SetSingleData(int, QString)", 0, 0],
        ["SetSingleData(int, QString)", 1, 1],
        ["SetSingleData(int, QString)", 2, 1],
        ["SetSingleData(int, QString)", 3, 0],
        ["SetSingleData(int, QString)", 4, '1'],
        ["SetSingleData(int, QString)", 5, 1000],
    ]
    tran_id = "TR_1864"
    return result, tran_id

def receive_symbol():
    single_result = {
    }
    multi_result = {
        'Rank': 0,          # 순위
        'symbol': 1,        # 단축코드
        'Name': 2,          # 종목명
        'price': 3,         # 현재가
        'sell': 9,          # 매도1호가
        'buy': 10,          # 매수1호가
    }
    return single_result, multi_result

# 현재가
def request_price_info(target_symbol):
    result = [
        ["SetSingleData(int, QString)", 0, target_symbol],
    ]
    tran_id = "SC"
    return result, tran_id

def receive_price_info():
    single_result = {
        'ISIN_CODE': 0,         # 표준코드
        'CODE': 1,              # 단축코드
        'Time': 2,              # 채결시간
        'Close': 3,             # 현재가
        'Vol': 7,               # 누적거래량
        'TRADING_VALUE': 8,     # 누적거래대금
        'ContQty': 9,           # 단위채결량
        'Open': 10,             # 시가
        'High': 11,             # 고가
        'Low': 12               # 저가
    }
    multi_result = {}
    return single_result, multi_result


# 보유 종목 잔고
def request_holding_info(account, password):
    result = [
        ["SetSingleData(int, QString)", 0, account],
        ["SetSingleData(int, QString)", 1, "01"],
        ["SetSingleData(int, QString)", 2, password]
    ]
    tran_id = "SABA200QB"
    return result, tran_id

def receive_holding_info():
    single_result = {}
    multi_result = {
        'ISIN_CODE': 0,             # 표준코드
        'NAME': 1,                  # 종목명
        'NUM': 2,                   # 결재일 잔고 수량
        'SELL_UNFINISHED_NUM': 3,   # 매도 미체결 수량
        'BUY_UNFINISHED_NUM': 4,    # 매수 미체결 수량
        'CURRENT_PRC': 5,           # 현재가
        'AVG_PRC': 6,               # 평균단가
        'CREDIT_NUM': 7,            # 신용잔고수량
        'KOSPI_NUM': 8,             # 코스피대용수량
    }
    return single_result, multi_result

# 증거금
def request_check_money(account, password):
    result = [
        ["SetSingleData(int, QString)", 0, account],
        ["SetSingleData(int, QString)", 1, "01"],
        ["SetSingleData(int, QString)", 2, password]
    ]
    tran_id = "SABA609Q1"
    return result, tran_id

def receive_check_money():
    single_result = {
        'Available_Money': 12,          # 주문가능총금액
        'D+2': 8,                       # D+2 추정예수금
        'Eval': 18                      # 주식평가금액

    }
    multi_result = {}
    return single_result, multi_result


# 매수 주문
def request_buy(account, password, target_symbol, count, order_price):
    print(order_price)
    result = [
        ["SetSingleData(int, QString)", 0, str(account)],               # 계좌번호
        ["SetSingleData(int, QString)", 1, "01"],                       # 상품구분
        ["SetSingleData(int, QString)", 2, str(password)],              # 비밀번호
        ["SetSingleData(int, QString)", 5, '0'],                        # 선물대용매도구분
        ["SetSingleData(int, QString)", 6, '00'],                       # 신용거래구분
        ["SetSingleData(int, QString)", 7, 2],                          # 매수매도 구분. 매도 : 1, 매수 : 2
        ["SetSingleData(int, QString)", 8, 'A' + str(target_symbol)],   # 종목코드
        ["SetSingleData(int, QString)", 9, str(count)],                 # 주문수량
        ["SetSingleData(int, QString)", 10, str(order_price)],          # 주문가격
        ["SetSingleData(int, QString)", 11, '1'],                       # 정규장
        ["SetSingleData(int, QString)", 12, '2'],                       # 호가유형, 1: 시장가, X:최유리, Y:최우선
        ["SetSingleData(int, QString)", 13, '0'],                       # 주문조건, 0:일반, 3:IOC, 4:FOK
        ["SetSingleData(int, QString)", 14, '0'],                       # 신용대출
        ["SetSingleData(int, QString)", 20, '31'],                      # 프로그램매매 여부
        ["SetSingleData(int, QString)", 21, 'Y'],                       # 결과 출력 여부
    ]
    tran_id = "SABA101U1"
    return result, tran_id


# 매도 주문
def request_sell(account, password, target_symbol, count):
    result = [
        ["SetSingleData(int, QString)", 0, str(account)],               # 계좌번호
        ["SetSingleData(int, QString)", 1, "01"],                       # 상품구분
        ["SetSingleData(int, QString)", 2, str(password)],              # 비밀번호
        ["SetSingleData(int, QString)", 5, '0'],                        # 선물대용매도구분
        ["SetSingleData(int, QString)", 6, '00'],                       # 신용거래구분
        ["SetSingleData(int, QString)", 7, 1],                          # 매수매도 구분. 매도 : 1, 매수 : 2
        ["SetSingleData(int, QString)", 8, 'A' + str(target_symbol)],   # 종목코드
        ["SetSingleData(int, QString)", 9, str(count)],                 # 주문수량
        # ["SetSingleData(int, QString)", 10, str(price)],              # 주문가격
        ["SetSingleData(int, QString)", 11, '1'],                       # 정규장
        ["SetSingleData(int, QString)", 12, 1],                         # 호가유형, 1: 시장가, X:최유리, Y:최우선
        ["SetSingleData(int, QString)", 13, '0'],                       # 주문조건, 0:일반, 3:IOC, 4:FOK
        ["SetSingleData(int, QString)", 14, '0'],                       # 신용대출
        ["SetSingleData(int, QString)", 20, '31'],                      # 프로그램매매 여부
        ["SetSingleData(int, QString)", 21, 'Y'],                       # 결과 출력 여부
    ]
    tran_id = "SABA101U1"
    return result, tran_id

# 매수 체결내역
def request_check_buy_order(account, password, target_symbol):
    today = datetime.datetime.today()
    result = [
        ["SetSingleData(int, QString)", 0, f'{today.year}{str(today.month).zfill(2)}{str(today.day).zfill(2)}'],
        ["SetSingleData(int, QString)", 1, account],
        ["SetSingleData(int, QString)", 2, password],
        ["SetSingleData(int, QString)", 3, "12"],
        ["SetSingleData(int, QString)", 4, "0"],
        ["SetSingleData(int, QString)", 5, "0"],
        ["SetSingleData(int, QString)", 6, "*"],
    ]
    tran_id = "SABA231Q1"
    return result, tran_id

def receive_check_buy_order():
    single_result = {}
    multi_result = {
        'ORDER_NUM': 0,                     # 주문번호
        'UNFINISHED': 26,                   # 미체결 수량
    }
    return single_result, multi_result

# 매도 체결내역
def request_check_sell_order(account, password, target_symbol):
    today = datetime.datetime.today()
    result = [
        ["SetSingleData(int, QString)", 0, f'{today.year}{str(today.month).zfill(2)}{str(today.day).zfill(2)}'],
        ["SetSingleData(int, QString)", 1, account],
        ["SetSingleData(int, QString)", 2, password],
        ["SetSingleData(int, QString)", 3, "11"],
        ["SetSingleData(int, QString)", 4, "0"],
        ["SetSingleData(int, QString)", 5, "0"],
        ["SetSingleData(int, QString)", 6, "*"],
    ]
    tran_id = "SABA231Q1"
    return result, tran_id

def receive_check_sell_order():
    single_result = {}
    multi_result = {
        'ORDER_NUM': 0,                     # 주문번호
        'UNFINISHED': 26,                   # 미체결 수량
    }
    return single_result, multi_result

def request_check_yield(account, password):
    today = datetime.datetime.today()
    print(f'{today.year}{str(today.month).zfill(2)}{str(today.day).zfill(2)}')
    result = [
        ["SetSingleData(int, QString)", 0, f'{today.year}{str(today.month).zfill(2)}{str(today.day).zfill(2)}'],
        ["SetSingleData(int, QString)", 1, account],
        ["SetSingleData(int, QString)", 2, password],
    ]
    tran_id = "SABC820Q1"
    return result, tran_id

def receive_check_yield():
    single_result = {}
    multi_result = {
        'CODE': 0,                     # 종목번호
        'YIELD': 12                    # 총 손익 금액
    }
    return single_result, multi_result
