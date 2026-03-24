FROM python:3.12-slim

ARG TARGETARCH

WORKDIR /app

# Install Litestream for optional SQLite replication
RUN apt-get update && apt-get install -y --no-install-recommends wget ca-certificates && \
    wget -q "https://github.com/benbjohnson/litestream/releases/download/v0.3.13/litestream-v0.3.13-linux-${TARGETARCH}.deb" -O /tmp/litestream.deb && \
    dpkg -i /tmp/litestream.deb && \
    rm /tmp/litestream.deb && \
    apt-get purge -y wget && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_ENV=production

EXPOSE 5000

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
