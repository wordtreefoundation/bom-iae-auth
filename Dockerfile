FROM wordtree/python-flask

ADD app /opt/bom-iae-auth/

WORKDIR /opt/bom-iae-auth/

VOLUME ["/data"]

EXPOSE 5000

CMD ./run.sh