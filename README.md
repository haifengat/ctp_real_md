# tick_from_ctp

## 项目介绍

使用ctp api接收行情生成实时分钟数据保存到redis


#### 数据处理
将镜像中带的postgres数据取出即可获得交易日历和品种交易时间数据库
```bash
docker run -itd --name tmp haifengat/ctp_real_md
docker cp tmp:/home/pgdata.tgz .
tar -xzf pgdata.tgz
docker rm -f tmp
docker-compose up -d
```


## Dockerfile
```dockerfile
FROM haifengat/pyctp:2.3.2
COPY *.py /home/
COPY *.txt /home/
COPY pgdata.tgz /home/
RUN pip install -r /home/requirements.txt
ENV redis_addr 172.19.129.98:16379
ENV pg_addr postgresql://postgres:123456@172.19.129.98:15432/postgres
ENV front_trade tcp://180.168.146.187:10101
ENV front_quote tcp://180.168.146.187:10111
ENV login_info 008105/1/9999/simnow_client_test/0000000000000000
ENTRYPOINT ["python", "/home/tick_ctp.py"]
```
### build
```bash
# 通过github git push触发 hub.docker自动build
docker pull haifengat/ctp_real_md && docker tag haifengat/ctp_real_md haifengat/ctp_real_md:`date +%Y%m%d` && docker push haifengat/ctp_real_md:`date +%Y%m%d`
#docker build -t haifengat/ctp_real_md:`date +%Y%m%d` . && docker push haifengat/ctp_real_md:`date +%Y%m%d`
#docker tag haifengat/ctp_real_md:`date +%Y%m%d` haifengat/ctp_real_md && docker push haifengat/ctp_real_md
```

### docker-compose.yaml
```bash
version: '3.1'
services:
  real_md:
    image: haifengat/ctp_real_md:0.0.1
    container_name: real_md
    restart: always
    environment:
      - TZ=Asia/Shanghai
    depends:
      - redis_tick
      - pg_tick

  redis_tick:
    image: redis:6.0.5
    container_name: redis_tick
    restart: always
    environment:
      - TZ=Asia/Shanghai
    volumes:
      - ./data:/data
  pg_tick:
    image: postgres:12
    container_name: pg_tick
    restart: always
    environment:
      - TZ=Asia/Shanghai
      - POSTGRES_PASSWORD=123456
    ports:
      - "15432:5432"
    volumes:
      - ./pgdata:/var/lib/postgresql/data
```
