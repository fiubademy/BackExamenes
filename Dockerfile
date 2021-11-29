FROM ubuntu
WORKDIR /app
RUN apt-get -y update 
RUN apt-get -y install python3
RUN apt-get -y install python3-pip
COPY requirements.txt /app/
RUN pip3 install -r requirements.txt
EXPOSE 8001
COPY Commands.sh /app/
COPY service/. /app/
CMD ./Commands.sh

