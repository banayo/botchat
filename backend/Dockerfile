# ใช้ Python 3.11 เวอร์ชั่น slim
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        unzip \
        libaio1t64 \
    && ln -sf /usr/lib/x86_64-linux-gnu/libaio.so.1t64 /usr/lib/x86_64-linux-gnu/libaio.so.1 \
    && rm -rf /var/lib/apt/lists/*

# Instant Client 19 สามารถต่อ Oracle 11g+ ได้ (thick mode)
ENV ORACLE_CLIENT_LIB_DIR=/opt/oracle/instantclient_19_19
ENV LD_LIBRARY_PATH=${ORACLE_CLIENT_LIB_DIR}

RUN mkdir -p /opt/oracle \
    && curl -fsSL -o /tmp/instantclient.zip \
        https://download.oracle.com/otn_software/linux/instantclient/1919000/instantclient-basiclite-linux.x64-19.19.0.0.0dbru.zip \
    && unzip -q /tmp/instantclient.zip -d /opt/oracle \
    && rm /tmp/instantclient.zip \
    && echo "${ORACLE_CLIENT_LIB_DIR}" > /etc/ld.so.conf.d/oracle-instantclient.conf \
    && ldconfig

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
