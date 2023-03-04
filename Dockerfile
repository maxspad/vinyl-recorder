FROM python:3.11.2-slim-bullseye

COPY requirements.txt /app/

WORKDIR /app

RUN pip install -r requirements.txt

COPY src/* /app/

CMD [ "streamlit", "run", "/app/app.py" ] 


