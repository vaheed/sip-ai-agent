FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpcap-dev \
    portaudio19-dev \
    python3-dev \
    wget \
    git \
    swig \
    ffmpeg \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install PJSIP and pjsua2
RUN cd /tmp && \
    wget https://github.com/pjsip/pjproject/archive/2.12.tar.gz && \
    tar -xzf 2.12.tar.gz && \
    cd pjproject-2.12 && \
    ./configure --enable-shared && \
    make dep && \
    make && \
    make install && \
    ldconfig && \
    cd pjsip-apps/src/swig && \
    make python && \
    cd python && \
    python setup.py install

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python packages (excluding pjsua2 which is built above)
RUN sed -i '/pjsua2==2.12/d' requirements.txt && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Copy test configuration script
COPY test_config.py .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/healthz', timeout=5)"

# Expose ports
EXPOSE 8080
EXPOSE 9090
EXPOSE 5060/udp
EXPOSE 16000-16100/udp

# Use the enhanced agent
CMD ["python", "agent.py"]
