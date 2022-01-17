FROM python:3.9.6-slim

RUN apt update && apt install -y --no-install-recommends \
    nano\
    tzdata
RUN mkdir /code
RUN mkdir /code/log
WORKDIR /code
COPY requirements.txt ./
RUN pip install -U pip
RUN pip install -r requirements.txt
COPY . ./
ENV TZ Asia/Seoul

