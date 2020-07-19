#!/usr/bin/env python
# -*- coding: utf-8 -*-
__title__ = '订阅ctp行情并入库'
__author__ = 'HaiFeng'
__mtime__ = '20180723'

import threading
import sys, csv, json
import getpass
from time import sleep
from datetime import datetime, timedelta

from py_ctp.enums import InstrumentStatus
from py_ctp.trade import CtpTrade
from py_ctp.quote import CtpQuote
from py_ctp.structs import InfoField, Tick, InstrumentField
from queue import Queue
import config as cfg


class TickCtp(object):
    """"""

    def __init__(self):
        """初始化"""
        self.inst_mins = {}
        self.received_tick = []
        self.trade_time = {}
        self.trading_days = []

        self.TradingDay = ''
        self.Actionday = ''
        self.Actionday1 = ''
        # tick时间
        self.tick_time = ''

        # 计算指数相关
        self.product_time = {}
        self.product_rate = {}

        self.inst_queue = Queue(0)

        self.t = CtpTrade()
        self.q = CtpQuote()

    def OnFrontConnected(self, obj):
        cfg.log.war('t:connected')
        self.t.ReqUserLogin(cfg.investor, cfg.pwd, cfg.broker, '@haifeng', cfg.appid, cfg.authcode)

    def OnFrontDisConnected(self, obj: CtpTrade, reason: int):
        cfg.log.war('t:disconnectd:{}'.format(reason))

    def OnRspUserLogin(self, obj: CtpTrade, info: InfoField):
        cfg.log.info('t:{}'.format(info))

        if info.ErrorID == 0:
            self.TradingDay = obj.tradingday
            self.received_tick.clear()
            self.inst_mins.clear()
            threading.Thread(target=self.start_quote).start()

    def start_quote(self):
        """"""
        self.get_actionday()
        self.get_trading_time()
        # 品种交易时间==>合约交易时间
        for inst, info in self.t.instruments.items():
            proc = info.ProductID
            if proc in self.trade_time:
                self.trade_time[inst] = self.trade_time[proc]
            else:
                self.trade_time[inst] = self.trade_time['default']

        # 隔夜时:行情重新登录后会重新获取夜盘的数据
        # if len(self.inst_pre_vol) == 0:
        cfg.log.info(f'req connect quote front address: {cfg.front_quote}')
        self.q.OnConnected = self.q_OnFrontConnected
        self.q.OnDisconnected = self.q_OnDisConnected
        self.q.OnUserLogin = self.q_OnRspUserLogin
        self.q.OnTick = self.q_OnTick

        self.q.ReqConnect(cfg.front_quote)

    def q_OnFrontConnected(self, obj):
        cfg.log.war('q:connected')
        self.q.ReqUserLogin(cfg.investor, cfg.pwd, cfg.broker)

    def q_OnDisConnected(self, obj, nReason: int):
        cfg.log.war('q:disconnected')

    def q_OnRspUserLogin(self, obj, info):
        cfg.log.info('q:{}'.format(info))
        for proc in [p.ProductID for p in self.t.instruments.values()]:
            self.inst_mins[proc + '_000'] = {'pre_vol': 0}
        for inst in [i.InstrumentID for i in self.t.instruments.values() if i.ProductType != 'EFP' and i.ProductType != 'Combination']:
            self.inst_mins[inst] = {'pre_vol': 0}
            if cfg.rds:
                if cfg.rds.exists(inst):
                    self.inst_mins[inst] = json.loads(cfg.rds.lindex(inst, -1).replace('\'', '"'))
                    if 'pre_vol' not in self.inst_mins[inst]:
                        self.inst_mins[inst]['pre_vol'] = 0
            self.q.ReqSubscribeMarketData(inst)
        # self.q.ReqSubscribeMarketData('rb1901')
        cfg.log.info('sub count:{}'.format(len(self.inst_mins)))

    def q_OnTick(self, obj: CtpQuote, tick: Tick):
        # 某个合约报 most recent call last 错误: 尝试改为线程处理
        if sys.float_info.max == tick.LastPrice:  # or sys.float_info.max == tick.AskPrice or sys.float_info.max == tick.BidPrice or sys.float_info.max == tick.LowerLimitPrice:
            return
        threading.Thread(target=self.run_tick, args=(tick,)).start()
        # 非线程模式,导致数据延时
        # self.run_tick(tick)

    def run_tick(self, tick: Tick):
        # 对tick时间进行修正处理
        ut = tick.UpdateTime[0:6] + '00'
        mins_dict = self.trade_time[tick.Instrument]
        # 由下面的 updatetime[-2:0] != '00' 处理
        if ut not in mins_dict['Mins']:
            # 开盘/收盘
            if ut in mins_dict['Opens']:
                ut = (datetime.strptime(ut, '%H:%M:%S') + timedelta(minutes=1)).strftime('%H:%M:%S')
            elif ut in mins_dict['Ends']:
                # 重新登录会收到上一节的最后tick
                tick_dt = datetime.strptime('{} {}'.format(datetime.now().strftime('%Y%m%d'), tick.UpdateTime), '%Y%m%d %H:%M:%S')
                now_dt = datetime.now()
                diff_snd = 0
                if tick_dt > now_dt:
                    diff_snd = (tick_dt - now_dt).seconds
                else:
                    diff_snd = (now_dt - tick_dt).seconds
                if diff_snd > 30:
                    return
                ut = (datetime.strptime(ut, '%H:%M:%S') + timedelta(minutes=-1)).strftime('%H:%M:%S')
            else:
                return
        # 首tick不处理(新开盘时会收到之前的旧数据)
        if tick.Instrument not in self.received_tick:
            self.received_tick.append(tick.Instrument)
            return
        proc: InstrumentField = self.t.instruments.get(tick.Instrument)
        if not proc:
            return
        # 合约合成分钟
        self.tick_min(tick, ut)

        # 指数合约合成分成
        # pre_time = self.product_time.get(proc.ProductID)
        # if not pre_time:
        #     self.product_time[proc.ProductID] = tick.UpdateTime
        # elif pre_time != tick.UpdateTime and tick.UpdateTime[-2:0] != '00':  # 整分时等下一秒再处理,以处理小节收盘单tick的问题
        #     self.product_time[proc.ProductID] = tick.UpdateTime

        #     # 计算合约权重
        #     ticks = [f for k, f in self.q.inst_tick.items() if self.t.instruments[k].ProductID == proc.ProductID]
        #     sum_oi = sum([f.OpenInterest for f in ticks])
        #     if sum_oi == 0:
        #         return

        #     rate = json.loads('{{{}}}'.format(','.join(['"{}":{}'.format(f.Instrument, f.OpenInterest / sum_oi) for f in ticks])))
        #     # 计算000
        #     tick000: Tick = Tick()
        #     tick000.Instrument = proc.ProductID + '_000'
        #     tick000.UpdateTime = tick.UpdateTime
        #     for inst, rate in rate.items():
        #         f: Tick = self.q.inst_tick[inst]
        #         tick000.AskPrice += f.AskPrice * rate
        #         tick000.BidPrice += f.BidPrice * rate
        #         tick000.LastPrice += f.LastPrice * rate
        #         tick000.AveragePrice += f.AveragePrice * rate
        #         tick000.LowerLimitPrice += f.LowerLimitPrice * rate
        #         tick000.UpperLimitPrice += f.UpperLimitPrice * rate
        #         tick000.AskVolume += f.AskVolume
        #         tick000.BidVolume += f.BidVolume
        #         tick000.Volume += f.Volume
        #         tick000.OpenInterest += f.OpenInterest
        #     try:
        #         # 防止因值为 sys.float_info.max 而报错: 只有lastprice参与分钟数据计算
        #         # tick000.AskPrice = round(tick000.AskPrice / proc.PriceTick) * proc.PriceTick
        #         # tick000.BidPrice = round(tick000.BidPrice / proc.PriceTick) * proc.PriceTick
        #         tick000.LastPrice = round(tick000.LastPrice / proc.PriceTick) * proc.PriceTick
        #         # tick000.AveragePrice = round(tick000.AveragePrice / proc.PriceTick) * proc.PriceTick
        #         # tick000.LowerLimitPrice = round(tick000.LowerLimitPrice / proc.PriceTick) * proc.PriceTick
        #         # tick000.UpperLimitPrice = round(tick000.UpperLimitPrice / proc.PriceTick) * proc.PriceTick
        #     except Exception as identifier:
        #         cfg.log.error(str(identifier))
        #         # cfg.log.error('tick:{0}-{1},000:{2},rate:{3}'.format(tick.Instrument, tick.AskPrice, tick000.AskPrice, proc.PriceTick))
        #     self.tick_min(tick000, ut)

    def tick_min(self, tick: Tick, ut: str):
        actionday = self.TradingDay
        if ut[0:2] > '20':
            actionday = self.Actionday
        elif ut[0:2] < '04':
            actionday = self.Actionday1
        # 分钟入库
        cur_min = self.inst_mins[tick.Instrument]

        if '_id' not in cur_min or cur_min['_id'][11:] != ut:
            cur_min['_id'] = actionday[0:4] + '-' + actionday[4:6] + '-' + actionday[6:] + ' ' + ut
            cur_min['TradingDay'] = self.TradingDay
            cur_min['Low'] = cur_min['Close'] = cur_min['High'] = cur_min['Open'] = tick.LastPrice
            cur_min['OpenInterest'] = tick.OpenInterest
            # cur_min['AveragePrice'] = tick.AveragePrice
            # 首个tick不计算成交量, 否则会导致隔夜的早盘第一个分钟的成交量非常大
            cur_min['Volume'] = tick.Volume - cur_min['pre_vol']
            cur_min['pre_vol'] = tick.Volume
            if cfg.rds:
                cfg.rds.rpush(tick.Instrument, json.dumps(cur_min))
        else:
            cur_min['High'] = max(cur_min['High'], tick.LastPrice)
            cur_min['Low'] = min(cur_min['Low'], tick.LastPrice)
            cur_min['Close'] = tick.LastPrice
            cur_min['OpenInterest'] = tick.OpenInterest
            cur_min['Volume'] = tick.Volume - cur_min['pre_vol']
            if cfg.rds:
                cfg.rds.lset(tick.Instrument, -1, json.dumps(cur_min))
        self.tick_time = tick.UpdateTime


    def get_actionday(self):
        with open('./calendar.csv') as f:
            reader = csv.DictReader(f)
            for r in reader:
                if r['tra'] == 'false':
                    continue
                self.trading_days.append(r['day'])
        # 接口未登录,不计算Actionday
        if self.TradingDay == '':
            return

        self.Actionday = self.TradingDay if self.trading_days.index(self.TradingDay) == 0 else self.trading_days[self.trading_days.index(self.TradingDay) - 1]
        self.Actionday1 = (datetime.strptime(self.Actionday, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')

    def get_trading_time(self):
        self.trade_time.clear()
        tmp = {}
        # conn = cfg.pg.raw_connection()
        # cursor = conn.cursor()
        # cursor.execute('select "GroupId", "WorkingTimes" from (select "GroupId", "OpenDate",  "WorkingTimes", row_number() over(partition by "GroupId" order by "OpenDate" desc) as row_no from future.tradingtime) a where row_no=1')
        # g = cursor.fetchall()
        with open('./tradingtime.csv') as f:
            reader = csv.DictReader(f)
            proc_day = {}
            for r in reader:
                # 按时间排序, 确保最后实施的时间段作为依据.
                if r['GroupId'] not in proc_day or r['OpenDate'] > proc_day[r['GroupId']]:
                    tmp[r['GroupId']] = r['WorkingTimes']
                proc_day[r['GroupId']] = r['OpenDate']
        # 根据时间段设置,生成 opens; ends; mins盘中时间
        for g_id, section  in tmp.items():
            opens = []
            ends = []
            mins = []
            for s in json.loads(section):
                opens.append((datetime.strptime(s['Begin'], '%H:%M:%S') + timedelta(minutes=-1)).strftime('%H:%M:00'))
                ends.append(s['End'])
                t_begin = datetime.strptime('20180101' + s['Begin'], '%Y%m%d%H:%M:%S')
                s_end = datetime.strptime('20180101' + s['End'], '%Y%m%d%H:%M:%S')
                if t_begin > s_end:  # 夜盘
                    s_end += timedelta(days=1)
                while t_begin < s_end:
                    mins.append(t_begin.strftime('%H:%M:00'))
                    t_begin = t_begin + timedelta(minutes=1)
            self.trade_time[g_id] = {'Opens': opens, 'Ends': ends, 'Mins': mins}

    def run(self):
        """"""
        self.t.OnConnected = self.OnFrontConnected
        self.t.OnUserLogin = self.OnRspUserLogin
        self.t.OnDisConnected = self.OnFrontDisConnected
        self.t.OnInstrumentStatus = lambda x, y, z: str(z)
        cfg.log.info(f'req connect trade front address: {cfg.front_trade}')
        self.t.ReqConnect(cfg.front_trade)

    def run_seven(self):
        """7*24"""
        if cfg.investor != '':
            cfg.log.info('investor:' + cfg.investor)
        else:
            cfg.investor = input('investor:')
        if cfg.pwd == '':
            cfg.pwd = getpass.getpass()
        threading.Thread(target=self._run_seven).start()

    def _run_seven(self):
        print_time = ''
        while True:
            day = datetime.now().strftime('%Y%m%d')
            left_days = list(filter(lambda x: x > day, self.trading_days))
            if len(left_days) == 0:
                self.get_actionday()
                self.get_trading_time()
                left_days = list(filter(lambda x: x > day, self.trading_days))
            next_trading_day = left_days[0]
            has_hight = (datetime.strptime(next_trading_day, '%Y%m%d') - datetime.strptime(day, '%Y%m%d')).days in [1, 3]

            now_time = datetime.now().strftime('%H%M%S')
            if not self.t.logined:
                # 当前非交易日
                if day not in self.trading_days:
                    # 昨天有夜盘:今天凌晨有数据
                    if now_time <= '020000' and (datetime.today() + timedelta.days(-1)).strftime('%Y%m%d') in self.trading_days:
                        sleep(1)
                    else:
                        cfg.log.info('{} is not tradingday.'.format(day))
                        cfg.log.info('continue after {}'.format(next_trading_day + ' 08:30:00'))
                        sleep((datetime.strptime(next_trading_day + '08:31:00', '%Y%m%d%H:%M:%S') - datetime.now()).total_seconds())
                elif now_time <= '083000':
                    cfg.log.info('continue after {}'.format(day + ' 08:30:00'))
                    sleep((datetime.strptime(day + '08:31:00', '%Y%m%d%H:%M:%S') - datetime.now()).total_seconds())
                elif now_time >= '153000':
                    if has_hight:
                        if datetime.now().strftime('%H%M%S') < '203000':
                            cfg.log.info('continue after {}'.format(day + ' 20:30:00'))
                            sleep((datetime.strptime(day + '20:31:00', '%Y%m%d%H:%M:%S') - datetime.now()).total_seconds())
                    else:
                        cfg.log.info('continue after {}'.format(next_trading_day + ' 08:30:00'))
                        sleep((datetime.strptime(next_trading_day + '08:31:00', '%Y%m%d%H:%M:%S') - datetime.now()).total_seconds())
                self.run()
                sleep(10)
            # 已收盘
            elif sum([1 if x != InstrumentStatus.Closed else 0 for x in self.t.instrument_status.values()]) == 0:
                self.t.ReqUserLogout()
                self.q.ReqUserLogout()
                if has_hight:
                    cfg.log.info('continue after {}'.format(day + ' 20:30:00'))
                    sleep((datetime.strptime(day + '20:31:00', '%Y%m%d%H:%M:%S') - datetime.now()).total_seconds())
                else:
                    cfg.log.info('continue after {}'.format(next_trading_day + ' 08:30:00'))
                    sleep((datetime.strptime(next_trading_day + '08:31:00', '%Y%m%d%H:%M:%S') - datetime.now()).total_seconds())
                # if cfg.mongo:
                #     cfg.mongo.conn.drop_database('future_real_min')
                if cfg.rds:
                    cfg.rds.flushdb()

            # 夜盘全部非交易
            elif now_time < '030000' and sum([1 if x == InstrumentStatus.Continous else 0 for x in self.t.instrument_status.values()]) == 0:
                cur_trading_day = self.t.tradingday
                self.t.ReqUserLogout()
                self.q.ReqUserLogout()
                # cur_trading_day = self.trading_days[self.trading_days.index(next_trading_day) - 1] 周末时取值不对
                cfg.log.info('continue after {}'.format(cur_trading_day + ' 08:30:00'))
                sleep((datetime.strptime(cur_trading_day + '08:31:00', '%Y%m%d%H:%M:%S') - datetime.now()).total_seconds())
            else:
                # 没有行情时不会显示
                if print_time != self.tick_time:
                    actionday = self.TradingDay
                    if self.tick_time[0:2] > '20':
                        actionday = self.Actionday
                    elif self.tick_time[0:2] < '04':
                        actionday = self.Actionday1
                    print_time = self.tick_time
                    cfg.log.info('tick time:{} [diff]{}s'.format(print_time, (datetime.strptime(actionday + print_time, '%Y%m%d%H:%M:%S') - datetime.now()).total_seconds()))
                sleep(60)


def main():
    p = TickCtp()
    threading.Thread(target=p._run_seven).start()


if __name__ == '__main__':
    main()
    while True:
        sleep(60)
