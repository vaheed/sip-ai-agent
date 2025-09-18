FROM python:3.9-slim

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
COPY app/ .

# Expose ports
EXPOSE 8080
EXPOSE 5060/udp
EXPOSE 16000-16100/udp

CMD ["python", "agent.py"]
