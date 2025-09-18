FROM node:20 AS frontend-builder

WORKDIR /frontend

COPY web/package*.json ./
RUN npm ci

COPY web/ ./
RUN npm run build

FROM python:3.9-slim AS backend

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpcap-dev \
    portaudio19-dev \
    python3-dev \
    wget \
    git \
    swig \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install PJSIP and pjsua2 bindings using the helper script
COPY scripts/install_pjsua2.py scripts/install_pjsua2.py
RUN python scripts/install_pjsua2.py

# Install other Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir "werkzeug<3.0.0" "flask<3.0.0"

# Copy application code
COPY app/ ./
COPY --from=frontend-builder /frontend/dist ./static/dashboard

# Expose ports
EXPOSE 8080
EXPOSE 5060/udp
EXPOSE 16000-16100/udp

CMD ["python", "agent.py"]

FROM nginx:1.25-alpine AS dashboard

COPY deploy/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-builder /frontend/dist /usr/share/nginx/html

EXPOSE 80
