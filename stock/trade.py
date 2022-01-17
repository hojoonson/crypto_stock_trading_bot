import utils
import logic
import datetime
import os
class Trade():
    def __init__(self, TARGET_SYMBOL, ACCOUNT, PASSWORD, diverse_ratio, buffersize, cost_rate=0.00229):
        self.TARGET_SYMBOL = TARGET_SYMBOL
        self.ACCOUNT = ACCOUNT
        self.PASSWORD = PASSWORD
        self.diverse_ratio = diverse_ratio
        self.buffersize = buffersize
        self.cost_rate = cost_rate

        self.order_count = -1
        self.bought_price = 100000000
        self.send_to_slack = False
        self.price_buffer = []

        self.sellCnt = 0
        self.sellTh = 1
        self.logfile = open(os.path.join('log', f'{str(datetime.date.today())}_{self.TARGET_SYMBOL}.log'), 'w')

        self.status = 'waiting'

    def run_single_loop(self, IndiWindow, trading_limit):
        # IndiWindow.request_data(request_type='check_buy_order', target_symbol=self.TARGET_SYMBOL)
        # utils.sleep(10)

        # IndiWindow.request_data(request_type='check_sell_order', target_symbol=self.TARGET_SYMBOL)
        # utils.sleep(10)

        # 현재가 체크
        IndiWindow.request_data(request_type='price_info', target_symbol=self.TARGET_SYMBOL)
        utils.sleep(10)

        current_price = IndiWindow.price_info[self.TARGET_SYMBOL]['current_price']
        cost = round(current_price * self.cost_rate, 2)

        if current_price == 1000000000:
            return 'ignore'

        # 종목 들고있는지 체크
        holding_info = IndiWindow.holding_info
        holding = True if 'A'+self.TARGET_SYMBOL in holding_info else False

        # 총 자산, 사용가능 금액 체크
        total_money = min(IndiWindow.total_money, trading_limit)
        available_money = min(total_money*self.diverse_ratio, IndiWindow.available_money)

        # 종목 들고있을때 각종 파라미터 업데이트
        if holding and self.order_count != 0 and int(holding_info['A'+self.TARGET_SYMBOL]['BUY_UNFINISHED_NUM']) == 0:
            # 들어오자마자 들고 있으면!
            if self.order_count == -1:
                self.order_count = int(holding_info['A'+self.TARGET_SYMBOL]['NUM'])

            # 산 가격
            self.bought_price = float(holding_info['A'+self.TARGET_SYMBOL]['AVG_PRC'])

            # 종목 들고있는데 send_to_slack 일때
            if self.send_to_slack:
                self.status = 'waiting'
                message = str(holding_info['A'+self.TARGET_SYMBOL])
                utils.send_to_slack(message)
                self.send_to_slack = False

            # 종목 들고있는데 장마감 다가오면 장마감 전에 팔기 (3시 8분지나면 팔기)
            if datetime.datetime.now().hour == 15 and datetime.datetime.now().minute >= 8:
                self.order_count, self.send_to_slack = utils.sell(IndiWindow, self.TARGET_SYMBOL, self.order_count)
                utils.sleep(1000)

        # 종목 안들고있는데
        if not holding and self.order_count <= 0:
            #  send_to_slack 일때 (팔았을 때)
            if self.send_to_slack:
                self.status = 'waiting'
                message = f"total_money: {total_money}"
                utils.send_to_slack(message)
                self.send_to_slack = False
                self.sellCnt += 1
                if datetime.datetime.now().hour >= 14:
                    utils.send_to_slack(f'[{datetime.datetime.now()}] End Trading: {self.TARGET_SYMBOL}')
                    return 'end'

            # 그냥 안들고 있을때
            # 장마감 다가오거나 하루에 3번이상 팔면(수익이 났으므로) 그냥 나감.
            if (datetime.datetime.now().hour == 15 and datetime.datetime.now().minute >= 8) or self.sellCnt >= self.sellTh:
                utils.send_to_slack(f'[{datetime.datetime.now()}] End Trading: {self.TARGET_SYMBOL}')
                return 'end'

        # accumalte previous prices
        self.price_buffer = [current_price] + self.price_buffer
        # print(len(self.price_buffer), self.TARGET_SYMBOL, available_money, current_price, cost, self.order_count, holding)
        if len(self.price_buffer) > self.buffersize:
            self.price_buffer = self.price_buffer[:self.buffersize]

            # 버퍼가 다 쌓이면 살거냐 팔거냐 판단.

            # buy logic
            if not holding and (available_money >= current_price + cost and self.order_count <= 0):
                if logic.buy_it_now(self.price_buffer, current_price):
                    self.order_count, self.send_to_slack = utils.buy(IndiWindow, self.TARGET_SYMBOL, available_money, current_price, cost)
                    self.status = 'buying'
                    utils.sleep(1000)

            # sell logic
            if holding and self.status != 'buying' and self.order_count > 0:
                if logic.sell_it_now(self.price_buffer, current_price, self.bought_price, self.cost_rate):
                    self.order_count, self.send_to_slack = utils.sell(IndiWindow, self.TARGET_SYMBOL, self.order_count)
                    self.bought_price = 100000000
                    self.status = 'selling'
                    utils.sleep(1000)

        # 로그파일에 정보 저장
        now = datetime.datetime.now()
        log_line = f'[{now}] {{target symbol: {self.TARGET_SYMBOL}, current price: {current_price}, available_money: {available_money}, holding: {holding}, expected cost: {cost}}}\n'
        self.logfile.write(log_line)
        return self.status
