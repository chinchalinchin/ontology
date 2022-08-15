FROM python:3.8

RUN cd /home/ && \
    git clone https://github.com/chinchalinchin/ontology.git && \
    cd ontology && \
    pip install -r requirements.txt



