FROM python:3.6.12-slim
RUN mkdir -p ~/.pip/ \
&& echo '[global]\
timeout = 6000\
index-url = https://mirrors.aliyun.com/pypi/simple/\
trusted-host = mirrors.aliyun.com'\
> ~/.pip/pip.conf
COPY ../*.txt /home/
RUN pip install --no-cache-dir -r /home/requirements.txt

COPY ../*.py /home/
# docker-compose
COPY ../*.yml /home/
# COPY pgdata.tgz /home/ 改用csv
COPY ../*.csv /home/

ENV redis_addr 172.19.129.98:16379
ENV front_trade tcp://180.168.146.187:10101
ENV front_quote tcp://180.168.146.187:10111
ENV login_info 008105/1/9999/simnow_client_test/0000000000000000
ENTRYPOINT ["python", "/home/tick_ctp.py"]
