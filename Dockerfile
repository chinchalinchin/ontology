FROM python:3.8.13

RUN /usr/local/bin/python -m pip install --upgrade pip && \
    cd /home/ && \
    git clone https://github.com/chinchalinchin/ontology.git 

WORKDIR /home/ontology

RUN pip install -r requirements.txt




