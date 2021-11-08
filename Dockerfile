FROM python:3.9.1

MAINTAINER Your Name "olga.kavvada@engie.com"

RUN apt-get update -y && \
    apt-get install -y python-pip python-dev

RUN apt-get install -y sqlite3 libsqlite3-dev

ADD . /python-flask
WORKDIR /python-flask

RUN pip install -r requirements.txt
