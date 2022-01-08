From python

RUN apt-get update

RUN apt-get -y install python3-pip
RUN pip3 install flask
RUN pip3 install waitress
RUN pip3 install requests

WORKDIR /usr/src/app

COPY . .

CMD python3 server.py

EXPOSE 5000