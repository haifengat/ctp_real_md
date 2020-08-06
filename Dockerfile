FROM haifengat/centos:8.1
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
