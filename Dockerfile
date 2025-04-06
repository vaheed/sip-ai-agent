FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0 ffmpeg \
    && pip install --no-cache-dir pjsua sounddevice websockets numpy

WORKDIR /app
COPY ./app /app
