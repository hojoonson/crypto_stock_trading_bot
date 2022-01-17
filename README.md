# Introduction
This repository is for automatic trading of crypto and stock.

Stock trading uses Shinhan Investment Corp API.

Crypto trading uses Binance Futures API.

# Crypto
1. Make key.py file.
```
api_key = {YOUR BINANCE API KEY}
secret = {YOUR BINANCE SECRET KEY}
```

2. Docker compose up
```
docker-compose --build up
```

# Stock
1. Make config.py file
```
ACCOUNT = {YOUR ACCOUNT NUMBER STR}
PASSWORD = {PASSWORD STR}
ID = {SHINHAN-i-indi ID}
PW = {SHINHAN-i-indi PASSWORD}
ADMIN_PW = {ACCREDITED CERTIFICATE PASSWORD}
SLACKER_KEY = {SLACKER KEY}
SLACK_MESSAGE_KEY = {SLACK_MESSAGE_KEY}
```

2. Run main.py
```
python main.py
```