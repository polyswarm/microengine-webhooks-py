FROM nginx/unit:1.29.0-python3.11

COPY nginx/*.json /docker-entrypoint.d/

WORKDIR /usr/src/app

COPY requirements.txt .

RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml .
COPY src .
COPY tests .

EXPOSE 8080
