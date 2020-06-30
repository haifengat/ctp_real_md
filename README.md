# tick_from_ctp

## 项目介绍

<del> 使用ctp api 从期货公司前置接收tick数据=>落地到csv文件=>合成分钟数据=>插入mongo库中 </del>

使用ctp api接收行情生成实时分钟数据保存到redis

## 逻辑

1. onRspLogin中取当前交易日TradingDay
2. onRspInstrument中取当前交易日对应的actionday; 取交易时间段设置; 启动行情接口; 启动查询[持仓/权益]
3. <del> 查询确认结算时间,判断是否为隔夜启动,以决定是否清除原有数据. 确认日期为实际日期,并非交易日. </del>
4. 登录成功后取tradingday与现有Tradingday比对,不相等即表示新的交易日登录

#### 安装教程

`pip install -r requirements.txt`

#### 使用说明

1. 配置环境变量
```bash
export redis_addr=127.0.0.1:16379 # redis连接: 
export pg_addr=postgresql://postgres:123456@127.0.0.1:15432/postgres  #postgresql 连接
export front_trade=tcp://180.168.146.187:10101 #交易前置
export front_quote=tcp://180.168.146.187:10111 # 行情前置
export login_info=008105/1/9999/simnow_client_test/0000000000000000 # investor/password/broker/appid/authcode #登录信息
```
3. 7*24运行, python main.py

## Dockerfile
```dockerfile
FROM haifengat/pyctp:2.3.2
COPY *.py /home/
COPY *.txt /home/
RUN pip install -r /home/requirements.txt
ENV redis_addr 172.19.129.98:16379
ENV pg_addr postgresql://postgres:123456@172.19.129.98:15432/postgres
ENV front_trade tcp://180.168.146.187:10101
ENV front_quote tcp://180.168.146.187:10111
ENV login_info 008105/1/9999/simnow_client_test/0000000000000000
ENTRYPOINT ["python", "/home/tick_ctp.py"]
```
### run
```bash
docker run -itd --name md --privileged ctp_real_md:0.0.1
docker logs -f md
```
