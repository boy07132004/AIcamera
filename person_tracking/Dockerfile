FROM python:3.9

COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
WORKDIR /code

CMD ["python", "main.py"]