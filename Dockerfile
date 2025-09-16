# Multi-stage build for optimized PJSIP + Python
FROM python:3.11-slim as builder

# Install build dependencies
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
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install PJSIP with minimal features (no video, no SSL, no ICE)
RUN cd /tmp && \
    wget https://github.com/pjsip/pjproject/archive/2.12.tar.gz && \
    tar -xzf 2.12.tar.gz && \
    cd pjproject-2.12 && \
    ./configure --enable-shared --disable-video --disable-sound --disable-ffmpeg --disable-ssl --disable-ice --disable-sound --disable-video && \
    make dep && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    cd pjsip-apps/src/swig && \
    make python && \
    cd python && \
    python setup.py install

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    libpcap0.8 \
    portaudio19-dev \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy only essential PJSIP libraries and Python packages
COPY --from=builder /usr/local/lib/libpj* /usr/local/lib/
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/include/pj* /usr/local/include/

# Set working directory
WORKDIR /app

# Copy application code
COPY app/ .

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/healthz || exit 1

# Expose ports
EXPOSE 8080 9090
EXPOSE 5060/udp
EXPOSE 16000-16100/udp

# Use the enhanced agent
CMD ["python", "agent.py"]