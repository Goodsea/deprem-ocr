FROM python:3.10-slim 

WORKDIR /app
RUN apt-get update && apt-get install -y python3-opencv
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
COPY . /app/

EXPOSE 8080

CMD ["python","-u","main.py"]