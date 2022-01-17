from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtWidgets import QMainWindow
import datetime
import utils


class IndiWindow(QMainWindow):
    def __init__(self, ACCOUNT, PASSWORD, contain_num):
        super(IndiWindow, self).__init__()

        self.account = ACCOUNT
        self.password = PASSWORD

        # 인디의 TR을 처리할 변수 생성
        # self.IndiTR = QAxWidget("GIEXPERTCONTROL64.GiExpertControl64Ctrl.1")
        self.IndiTR = QAxWidget("GIEXPERTCONTROL.GiExpertControlCtrl.1")

        # Indi API event
        self.IndiTR.ReceiveData.connect(self.receive_data)
        self.IndiTR.ReceiveSysMsg.connect(self.receive_sysmsg)
        self.rqidD = {}  # TR 관리를 위한 Dict

        self.TARGET_SYMBOL_LIST = []
        self.contain_num = contain_num
        self.price_info = {}

        self.holding_info = {}
        self.available_money = 0
        self.total_money = 0

    def login(self, id, pw, admin_pw):
        while True:
            login = self.IndiTR.StartIndi(id, pw, admin_pw, 'C:\SHINHAN-i\indi\giexpertstarter.exe')
            if login:
                print('Login...')
                break

    def logout(self):
        while True:
            logout = self.IndiTR.CloseIndi()
            if logout:
                print('Logout Success!')
                break

    def request_data(self, request_type, target_symbol=None, count=None, order_price=None):
        input_data, tran_id = [], ''

        # 거래량 기반 종목 선정. (TR: TR_1864)
        if request_type == 'symbol':
            input_data, tran_id = utils.request_symbol()

        # 현재가. (TR: SC)
        if request_type == 'price_info':
            input_data, tran_id = utils.request_price_info(target_symbol)

        # 보유 종목 잔고. (TR:SABA200QB)
        if request_type == 'holding_info':
            input_data, tran_id = utils.request_holding_info(self.account, self.password)

        # 예수금. (TR: SABA602Q1)
        if request_type == 'check_money':
            input_data, tran_id = utils.request_check_money(self.account, self.password)

        # 매수 요청. (TR: SABA101U1)
        if request_type == 'buy':
            input_data, tran_id = utils.request_buy(self.account, self.password, target_symbol, count, order_price)
            now = datetime.datetime.now()
            utils.send_to_slack(f"[{now}] Request Buy : {count} {order_price}")

        # 매도 요청. (TR: SABA101U1)
        if request_type == 'sell':
            input_data, tran_id = utils.request_sell(self.account, self.password, target_symbol, count)
            now = datetime.datetime.now()
            utils.send_to_slack(f"[{now}] Request Sell : {count} {order_price}")

        # 매수 체결내역(TR: SABA231Q1)
        if request_type == 'check_buy_order':
            input_data, tran_id = utils.request_check_buy_order(self.account, self.password, target_symbol)

        # 매도 체결내역(TR: SABA231Q1)
        if request_type == 'check_sell_order':
            input_data, tran_id = utils.request_check_sell_order(self.account, self.password, target_symbol)

        # 종목별 손익 (TR: SABC820Q1)
        if request_type == 'check_yield':
            input_data, tran_id = utils.request_check_yield(self.account, self.password)

        self.request_module(input_data, tran_id, request_type, target_symbol)

    def request_module(self, input_data, tran_id, request_type, target_symbol):
        ret = self.IndiTR.dynamicCall("SetQueryName(QString)", tran_id)
        if ret:
            for data in input_data:
                ret = self.IndiTR.dynamicCall(data[0], data[1], data[2])
                if not ret:
                    break
            else:
                rqid = self.IndiTR.dynamicCall("RequestData()")
                self.rqidD[rqid] = (request_type, target_symbol)

    def receive_data(self, rqid):
        try:
            request_type, target_symbol = self.rqidD[rqid]
            # 거래량 기반 종목 선정. (TR: TR_1864)
            if request_type == "symbol":
                single_result, multi_result = utils.receive_symbol()
                nCnt = self.IndiTR.dynamicCall("GetMultiRowCount()")

                # 데이터들을 초기화 해주고 append해야함
                count = 0
                message = ""
                self.TARGET_SYMBOL_LIST = []
                for i in range(0, nCnt):
                    ISIN_CODE = self.IndiTR.dynamicCall("GetMultiData(int, int)", i, 0)
                    result = {}
                    for key, value in multi_result.items():
                        result[key] = self.IndiTR.dynamicCall("GetMultiData(int, int)", i, value)
                    # 금액 필터링, 인버스/레버리지/ETN/선물 필터링
                    if float(result['price']) <= 15000 and \
                            '인버스' not in result['Name'] and \
                            '레버리지' not in result['Name'] and \
                            'ETN' not in result['Name'] and \
                            '선물' not in result['Name']:
                        symbol = result['symbol']
                        message += str(f"[{symbol}], {result['Name']}\n")
                        self.TARGET_SYMBOL_LIST.append(symbol)
                        count += 1
                    if count == self.contain_num:
                        utils.send_to_slack(message)
                        break

            # 현재가. (TR: SC)
            if request_type == "price_info":
                single_result, multi_result = utils.receive_price_info()
                self.price_info[target_symbol]['current_price'] = float(self.IndiTR.dynamicCall("GetSingleData(int)", single_result['Close']))

            # 보유 종목 잔고. (TR:SABA200QB)
            if request_type == "holding_info":
                temp_holding_info = {}
                single_result, multi_result = utils.receive_holding_info()
                nCnt = self.IndiTR.dynamicCall("GetMultiRowCount()")
                for i in range(0, nCnt):
                    ISIN_CODE = self.IndiTR.dynamicCall("GetMultiData(int, int)", i, 0)
                    temp_holding_info[ISIN_CODE] = {}
                    for key, value in multi_result.items():
                        temp_holding_info[ISIN_CODE][key] = self.IndiTR.dynamicCall("GetMultiData(int, int)", i, value)
                self.holding_info = temp_holding_info

            # 예수금. (TR: SABA602Q1)
            if request_type == "check_money":
                single_result, multi_result = utils.receive_check_money()
                self.available_money = float(self.IndiTR.dynamicCall("GetSingleData(int)", single_result['Available_Money']))
                D_2 = float(self.IndiTR.dynamicCall("GetSingleData(int)", single_result['D+2']))
                Eval = float(self.IndiTR.dynamicCall("GetSingleData(int)", single_result['Eval']))
                self.total_money = D_2 + Eval

            # 매수 요청. (TR: SABA101U1)
            if request_type == "buy":
                DATA = {}
                DATA['Order_Num'] = self.IndiTR.dynamicCall("GetSingleData(int)", 0)  # 주문번호
                DATA['Num'] = self.IndiTR.dynamicCall("GetSingleData(int)", 2)  # 메시지 구분
                DATA['Msg1'] = self.IndiTR.dynamicCall("GetSingleData(int)", 3)  # 메시지1
                DATA['Msg2'] = self.IndiTR.dynamicCall("GetSingleData(int)", 4)  # 메시지2
                DATA['Msg3'] = self.IndiTR.dynamicCall("GetSingleData(int)", 5)  # 메시지3
                now = datetime.datetime.now()
                utils.send_to_slack(f"[{now}] Buy Result {str(DATA)}")

            # 매도 요청. (TR: SABA101U1)
            if request_type == "sell":
                DATA = {}
                DATA['Order_Num'] = self.IndiTR.dynamicCall("GetSingleData(int)", 0)  # 주문번호
                DATA['Num'] = self.IndiTR.dynamicCall("GetSingleData(int)", 2)  # 메시지 구분
                DATA['Msg1'] = self.IndiTR.dynamicCall("GetSingleData(int)", 3)  # 메시지1
                DATA['Msg2'] = self.IndiTR.dynamicCall("GetSingleData(int)", 4)  # 메시지2
                DATA['Msg3'] = self.IndiTR.dynamicCall("GetSingleData(int)", 5)  # 메시지3
                now = datetime.datetime.now()
                utils.send_to_slack(f"[{now}] Sell Result {str(DATA)}")

            # 매수 체결내역(TR: SABA231Q1)
            if request_type == "check_buy_order":
                print("check buy order")
                single_result, multi_result = utils.receive_check_buy_order()
                nCnt = self.IndiTR.dynamicCall("GetMultiRowCount()")
                for i in range(0, nCnt):
                    for key, value in multi_result.items():
                        print(self.IndiTR.dynamicCall("GetMultiData(int, int)", i, value))

            # 매도 체결내역(TR: SABA231Q1)
            if request_type == "check_sell_order":
                print("check sell order")
                single_result, multi_result = utils.receive_check_sell_order()
                nCnt = self.IndiTR.dynamicCall("GetMultiRowCount()")
                for i in range(0, nCnt):
                    for key, value in multi_result.items():
                        print(self.IndiTR.dynamicCall("GetMultiData(int, int)", i, value))

            # 종목별 수익률
            if request_type == "check_yield":
                print("check_yield")
                single_result, multi_result = utils.receive_check_yield()
                nCnt = self.IndiTR.dynamicCall("GetMultiRowCount()")
                print(nCnt)
                for i in range(0, nCnt):
                    for key, value in multi_result.items():
                        print(self.IndiTR.dynamicCall("GetMultiData(int, int)", i, value))
            self.rqidD.__delitem__(rqid)

        except Exception as e:
            utils.send_to_slack(str(e))

    # 시스템 메시지를 받은 경우 출력합니다.
    def receive_sysmsg(self, msg_id):
        pass
        # print("System Message Received = ", msg_id)
