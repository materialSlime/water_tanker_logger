FROM python:3.11.6-alpine3.18
COPY . /root/app
WORKDIR /root/app/

RUN cd /root/app
RUN pip install --upgrade pip
RUN pip install -r requirments.txt
RUN pip install pymysql


CMD ["python","main.py"]