#!/usr/bin/env python
# -*- coding: utf-8 -*-
__title__ = '配置文档'
__author__ = 'HaiFeng'
__mtime__ = '20180821'

import sys, os
from redis import StrictRedis, ConnectionPool
# from pymongo import MongoClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from color_log import Logger

log = Logger()

redis_host, port = 'redis_tick', 6379
if 'redis_addr' in os.environ:
    redis_host = os.environ['redis_addr']
    if ':' in redis_host:
        redis_host, port =  redis_host.split(':')
log.info(f'connecting redis: {redis_host}:{port}')
pool = ConnectionPool(host=redis_host, port=port, db=0, decode_responses=True)
rds = StrictRedis(connection_pool=pool)

front_trade='tcp://180.168.146.187:10101'
if 'front_trade' in os.environ:
    front_trade = os.environ['front_trade']

front_quote='tcp://180.168.146.187:10111'
if 'front_quote' in os.environ:
    front_quote = os.environ['front_quote']

# investor/password/broker/appid/authcode
login_info='008105/1/9999/simnow_client_test/0000000000000000'
if 'login_info' in os.environ:
    login_info = os.environ['login_info']
investor, pwd, broker, appid, authcode = login_info.split('/')

