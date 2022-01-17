import numpy as np
def buy_it_now(price_buffer, current_price):
    # (1) Simple Logic
    target_price = (np.min(price_buffer) + np.mean(price_buffer)) / 2

    # 저점 반등 매수
    if (current_price >= target_price) and np.min(price_buffer) in price_buffer[int(len(price_buffer)*0.5):int(len(price_buffer)*0.9)]:
        return True
    else:
        return False

def sell_it_now(price_buffer, current_price, bought_price, cost_rate):
    # (1) Simple Logic
    upper_target_price = bought_price * (1 + cost_rate * 5)
    lower_target_price = bought_price * (1 - cost_rate * 5)

    # 타겟 고점 매도 혹은 손절
    if current_price >= upper_target_price or current_price <= lower_target_price:
        return True
    else:
        return False
