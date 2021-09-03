FROM python:3.9-slim-bullseye

ENV PROCESS_TYPE="celery" \
    PROCFILE="docker/Procfile" \
    FLASK_APP="tests.integration.base"

WORKDIR /usr/src/app

RUN apt-get update -y \
    && apt-get install -qy --no-install-recommends apt-utils \
    && apt-get install -qy --no-install-recommends \
        ca-certificates \
        gnupg2 \
        coreutils netbase \
        procps \
        tar bzip2 xz-utils ncompress unzip \
        gcc libc-dev pkg-config make file \
        git-core \
        wget \
        g++ \
    && useradd -ms /bin/bash worker \
    && chown -R worker:worker /usr/src/app \
    && pip install --no-cache-dir honcho

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

USER worker

COPY . .
RUN pip install .

EXPOSE 5000

CMD ["sh", "-c", "exec honcho -f $PROCFILE start --no-prefix $PROCESS_TYPE"]
