FROM nginx/unit:1.19.0-python3.7

COPY nginx/*.json /docker-entrypoint.d/

WORKDIR /usr/src/app

COPY requirements.txt .

RUN apt update && apt install -y python3-pip \
    && pip3 install --no-cache-dir -r requirements.txt \
    && apt remove -y python3-pip \
    && apt autoremove --purge -y \
    && rm -rf /var/lib/apt/lists/* /etc/apt/sources.list.d/*.list

COPY setup.py .
COPY src .
COPY tests .

EXPOSE 8080
