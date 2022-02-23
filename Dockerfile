FROM python:3.10-slim-buster

ADD main.py settings.py requirements.txt /

RUN pip install -r requirements.txt

CMD [ "python", "./main.py" ]