from ubuntu:22.04

WORKDIR /translator
COPY . /translator/

ENV DEBIAN_FRONTEND=noninteractive 

RUN apt-get update && apt-get install -y python3 python3-pip
RUN apt-get install -y /translator/translateLocally-v0.0.2+136745e-Ubuntu-20.04.x86-64.deb
RUN pip install -r /translator/requirements.txt

ENTRYPOINT [ "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "7725", "--workers", "6" ]