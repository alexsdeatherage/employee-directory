FROM python:3.11-slim

WORKDIR /code

# Copy requirements file first to take advantage of Docker caching
COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

EXPOSE 8000