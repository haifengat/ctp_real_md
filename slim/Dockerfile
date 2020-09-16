FROM python:3.6.12-slim
RUN mkdir -p ~/.pip/ \
&& echo '[global]\
timeout = 6000\
index-url = https://mirrors.aliyun.com/pypi/simple/\
trusted-host = mirrors.aliyun.com'\
> ~/.pip/pip.conf
ENV DOWNLOAD_URL https://github.com/haifengat/ctp_real_md/archive/master.zip
WORKDIR /real_md
RUN set -ex; \
    apt-get update && apt-get install -y --no-install-recommends wget unzip; \
    wget -O master.zip "${DOWNLOAD_URL}"; \
    unzip master.zip; \
    rm master.zip; \
    pip install --no-cache-dir -r ./ctp_real_md-master/requirements.txt

ENTRYPOINT ["python", "./ctp_real_md-master/tick_ctp.py"]
