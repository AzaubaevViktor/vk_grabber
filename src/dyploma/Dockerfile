FROM python:3.8

COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

COPY src /app

CMD python3 /app