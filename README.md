# tick_from_ctp

## 项目介绍

使用ctp api接收行情生成实时分钟数据保存到redis


## Dockerfile
```dockerfile
FROM haifengat/pyctp:2.3.2
COPY *.py /home/
COPY *.txt /home/
# docker-compose
COPY *.yml /home/
# COPY pgdata.tgz /home/ 改用csv
COPY *.csv /home/
RUN pip install -r /home/requirements.txt
ENV redis_addr 172.19.129.98:16379
ENV front_trade tcp://180.168.146.187:10101
ENV front_quote tcp://180.168.146.187:10111
ENV login_info 008105/1/9999/simnow_client_test/0000000000000000
ENTRYPOINT ["python", "/home/tick_ctp.py"]
```

### build
```bash
# 通过github git push触发 hub.docker自动build
docker pull haifengat/ctp_real_md && docker tag haifengat/ctp_real_md haifengat/ctp_real_md:`date +%Y%m%d` && docker push haifengat/ctp_real_md:`date +%Y%m%d`
```

### docker-compose.yaml
```bash
version: '3.1'
services:
  real_md:
    image: haifengat/ctp_real_md
    container_name: real_md
    restart: always
    environment:
      - "TZ=Asia/Shanghai"
      - "redis_addr=redis_tick:6379"
      - "front_trade=tcp://180.168.146.187:10101"
      - "front_quote=tcp://180.168.146.187:10111"
      - "login_info=008105/1/9999/simnow_client_test/0000000000000000"
    depends_on:
      - redis_tick

  redis_tick:
    image: redis:6.0.5
    container_name: redis_tick
    restart: always
    environment:
      - TZ=Asia/Shanghai
    ports:
      - "16379:6379"      
```
