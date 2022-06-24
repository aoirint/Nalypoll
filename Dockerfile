FROM python:3.9

ENV PYTHONUNBUFFERED=1
ENV DJANGO_DEBUG=0
ENV DJANGO_STATIC_ROOT=/static

WORKDIR /code
ADD requirements.txt /code/

RUN pip install -r requirements.txt

ADD ./Nalypoll /code

CMD [ "gunicorn", "-w", "1", "Nalypoll.wsgi", "-b", "0.0.0.0:8000" ]
