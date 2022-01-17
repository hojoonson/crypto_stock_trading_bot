from trade import Trade
from indiwindow import IndiWindow
from PyQt5.QtWidgets import QApplication
import sys
import datetime
import utils
from config import ACCOUNT, PASSWORD, ID, PW, ADMIN_PW
app = QApplication(sys.argv)

cost_rate = 0.00229  # 세금 가정
buffersize = 1200
contain_num = 3   # 타겟 종목 개수
trading_limit = 100000  # 거래 한도. 이 이상은 거래 안함.
TARGET_SYMBOL_LIST = []

IndiWindow = IndiWindow(ACCOUNT, PASSWORD, contain_num)
IndiWindow.login(ID, PW, ADMIN_PW)
IndiWindow.rqidD = {}
print('Login....')
utils.sleep(20000)

print('Wait Trading')
while datetime.datetime.now().hour <= 8 or (datetime.datetime.now().hour == 9 and datetime.datetime.now().minute <= 30):
    pass
print(f'Start Trading {datetime.datetime.now()}')

# 거래량 급등 기반으로, 타겟 종목 자동 선정.
print('Selecting Targets...')
while len(TARGET_SYMBOL_LIST) < contain_num:
    IndiWindow.request_data(request_type='symbol')
    utils.sleep(5000)
    TARGET_SYMBOL_LIST = IndiWindow.TARGET_SYMBOL_LIST
utils.send_to_slack(str(TARGET_SYMBOL_LIST))

diverse_ratio = round(1/len(TARGET_SYMBOL_LIST), 1)


for TARGET_SYMBOL in TARGET_SYMBOL_LIST:
    print(TARGET_SYMBOL)
    IndiWindow.price_info[TARGET_SYMBOL] = {
        'current_price': 1000000000
    }

# 종목별 trade agent 생성
agent_list = []
for TARGET_SYMBOL in TARGET_SYMBOL_LIST:
    trade_agent = Trade(TARGET_SYMBOL, ACCOUNT, PASSWORD, diverse_ratio, buffersize)
    agent_list.append(trade_agent)

# agent 별로 트레이딩 시작
status = "ignore"
while True:
    IndiWindow.request_data(request_type='holding_info')
    utils.sleep(100)

    IndiWindow.request_data(request_type='check_money')
    utils.sleep(100)

    for agent in agent_list:
        status = agent.run_single_loop(IndiWindow, trading_limit)
        # print(status)
        if status == 'end':
            agent.logfile.close()
            agent_list.remove(agent)
        print(status)
    print(IndiWindow.holding_info)
    print(IndiWindow.price_info)
    if len(agent_list) == 0:
        break

utils.sleep(10000)
IndiWindow.logout()
sys.exit()
# app.exec_()
