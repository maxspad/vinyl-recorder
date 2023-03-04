FROM python:3.11.2-slim-bullseye

COPY requirements.txt /app/

WORKDIR /app

RUN apt-get update -y && \
    apt-get install -y \
        alsa-utils \
        libportaudio2 \
        pulseaudio && \
    apt-get clean

RUN pip install -r requirements.txt

CMD [ "streamlit", "run", "/app/app.py" ] 


