FROM python:3.6.12-slim

ENV PROJECT=ctp_real_md

ENV DOWNLOAD_URL "https://github.com/haifengat/${PROJECT}/archive/master.zip"
WORKDIR /
RUN set -ex; \
    apt-get update && apt-get install -y --no-install-recommends wget unzip; \
    wget -O master.zip "${DOWNLOAD_URL}"; \
    unzip master.zip; \
    rm master.zip -rf;

WORKDIR /${PROJECT}-master
RUN pip install --no-cache-dir -r ./requirements.txt

ENTRYPOINT ["python", "tick_ctp.sh"]
