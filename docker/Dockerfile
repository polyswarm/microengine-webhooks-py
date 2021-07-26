FROM nginx/unit:1.19.0-python3.7

COPY nginx/*.json /docker-entrypoint.d/

WORKDIR /usr/src/app

COPY requirements.txt .

RUN apt update && apt install -y python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir -r requirements.txt

COPY setup.py .
COPY src .
COPY tests .

EXPOSE 8080
