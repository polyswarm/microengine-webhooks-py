FROM nginx/unit:1.19.0-python3.7

COPY nginx/*.json /docker-entrypoint.d/

WORKDIR /usr/src/app

COPY requirements.txt .

RUN apt update && apt install -y python3-pip \
    && pip3 install --no-cache-dir -r requirements.txt \
    && apt remove -y python3-pip \
    && apt autoremove --purge -y \
    && rm -rf /var/lib/apt/lists/* /etc/apt/sources.list.d/*.list
    && useradd -ms /bin/bash worker \
    && chown -R worker:worker /usr/src/app \

COPY --chown=worker setup.py .
COPY --chown=worker src .
COPY --chown=worker tests .

USER worker

EXPOSE 8080
