#!/usr/bin/env python
# -*- coding: utf-8 -*-
__title__ = '配置文档'
__author__ = 'HaiFeng'
__mtime__ = '20180821'

import yaml
import sys, os
from redis import StrictRedis, ConnectionPool
# from pymongo import MongoClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from color_log import Logger


log = Logger()


# 检查配置
if 'redis_addr' not in os.environ:
    log.error('there is no config for redis!!!')
    sys.exit(-1)
if 'pg_addr' not in os.environ:
    log.error('there is no config for postgres!!!')
    sys.exit(-1)
if 'front_trade' not in os.environ:
    log.error('there is no config for CTP trade!!!')
    sys.exit(-1)
if 'front_quote' not in os.environ:
    log.error('there is no config for CTP quote!!!')
    sys.exit(-1)
if 'login_info' not in os.environ:
    log.error('there is no config for CTP login info!!!')
    sys.exit(-1)

port = 6379
redis_host = os.environ['redis_addr']
if ':' in redis_host:
    redis_host, port =  redis_host.split(':')
pool = ConnectionPool(host=redis_host, port=port, db=0, decode_responses=True)
rds = StrictRedis(connection_pool=pool)

pg_addr = os.environ['pg_addr']
pg: Engine = create_engine(pg_addr)

# ctp前置格式 tcp://xxx.xxx.xxx.xxx:nnnnn
front_trade = os.environ['front_trade']
front_quote = os.environ['front_quote']
# investor/password/broker/appid/authcode
login_info = os.environ['login_info']
investor, pwd, broker, appid, authcode = login_info.split('/')

