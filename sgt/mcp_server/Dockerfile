FROM python:3.12.12-slim
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive
ENV ACCEPT_EULA=Y
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    gcc \
    g++ \
    unixodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
    | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
    > /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

RUN sed -i 's/\[openssl_init\]/[openssl_init]\nssl_conf = ssl_sect/' /etc/ssl/openssl.cnf \
    && echo "\n[ssl_sect]\nsystem_default = system_default_sect\n\n[system_default_sect]\nMinProtocol = TLSv1\nCipherString = DEFAULT@SECLEVEL=0\nOptions = UnsafeLegacyRenegotiation" \
    >> /etc/ssl/openssl.cnf

RUN pip install uv
COPY requirements.txt .
RUN uv init
RUN uv add -r requirements.txt
COPY . .
ENV PORT=8123
EXPOSE 8123
CMD uv run main.py

