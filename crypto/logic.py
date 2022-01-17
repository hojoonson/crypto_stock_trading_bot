from logger import logger
import utils
import datetime


def position_logic_5min_3tick(ohlcv, diff_thresh=4):
    diffs = list(ohlcv['close'] - ohlcv['open'])
    tick, last_index = get_tick(diffs, diff_thresh)
    logger.info(f'{datetime.datetime.utcnow()} LONG LOGIC tick: {tick}, last_index: {last_index}/{len(diffs[:-1])-1}')
    if tick >= 3 and last_index == len(diffs[:-1]) - 1:
        return 'long'

    diffs = [-x for x in diffs]
    tick, last_index = get_tick(diffs, diff_thresh * 0.8)
    logger.info(f'{datetime.datetime.utcnow()} SHORT LOGIC tick: {tick}, last_index: {last_index}/{len(diffs[:-1])-1}')
    # for short, tick thresh is 2
    if tick >= 2 and last_index == len(diffs[:-1]) - 1:
        return 'short'

    return 'hold'


def get_tick(diffs, diff_thresh):
    tick = 0
    accum_diff = 0
    last_index = 0
    for index, diff in enumerate(diffs[:-1]):
        if diff <= -diff_thresh:
            tick += 1
            last_index = index
        else:
            accum_diff += diff

        if accum_diff >= diff_thresh:
            tick = max(0, tick - 1)
            accum_diff = 0

        elif accum_diff <= -diff_thresh:
            tick += 1
            last_index = index
            accum_diff = 0
    return tick, last_index


def close_logic(position_info, distribution, order_amount, amount):
    new_amount = amount

    try:
        # Long이냐 Short이냐 보고 청산
        if position_info['side'] == 'long':
            utils.order(order_amount, 'sell')
        elif position_info['side'] == 'short':
            utils.order(order_amount, 'buy')
        new_amount = round(utils.get_max_order_amount() / distribution, 3)
        logger.info(f'{datetime.datetime.utcnow()} CLOSE! {utils.get_balance()}')
    except:
        logger.info(f'{datetime.datetime.utcnow()} CANNOT CLOSE! {utils.get_balance()}')
    return new_amount
