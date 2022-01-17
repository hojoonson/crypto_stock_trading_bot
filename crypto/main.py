import utils
import pandas as pd
from copy import deepcopy
from logic import position_logic_5min_3tick
from logger import logger
import time
import datetime

distribution = 25
ohlcv_limit = 12
logger.info(f'{datetime.datetime.utcnow()} START CRYPTO TRADING')
amount = utils.get_amount(distribution)
logger.info(f'{datetime.datetime.utcnow()} amount : {amount}')
prev_ohlcv = utils.get_ohlcv(limit=ohlcv_limit)
while True:
    ohlcv = utils.get_ohlcv(limit=ohlcv_limit)
    # every 5 mins
    if not pd.DataFrame.equals(ohlcv['open'], prev_ohlcv['open']):
        diff_thresh = list(ohlcv['open'])[-1] / 650
        # get position logic
        long_or_short = position_logic_5min_3tick(ohlcv, diff_thresh=diff_thresh)
        logger.info(f'{datetime.datetime.utcnow()} {long_or_short}')

        # Order
        if utils.order(amount, long_or_short):
            logger.info(f'{datetime.datetime.utcnow()} {long_or_short}!! {utils.get_balance()}')
        else:
            logger.info(f'{datetime.datetime.utcnow()} CANNOT ORDER! {utils.get_balance()}')
        amount = utils.get_amount(distribution)

    prev_ohlcv = deepcopy(ohlcv)
    time.sleep(0.5)
