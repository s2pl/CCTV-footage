FROM python:3.12-alpine

WORKDIR /app

COPY requirements-ubuntu.txt .

RUN pip install -r requirements-ubuntu.txt

COPY . .

RUN mkdir logs && touch logs/debug.log

RUN mkdir -p /staticfiles

RUN mkdir -p /media/users/avatar
RUN mkdir -p /media/logs
RUN mkdir -p /media/recordings
RUN mkdir -p /media/thumbnails


EXPOSE 8000 

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
