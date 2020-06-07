FROM python:3.8

COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

WORKDIR /app
CMD python3 __main__.py configs/main.yaml