FROM ubuntu:18.04


RUN apt-get update && apt-get install -y --no-install-recommends python3-pip

RUN pip3 install numpy scipy requests json-rpc werkzeug pymongo
RUN pip3 install setuptools
RUN pip3 install pyDOE scikit-optimize

COPY learner/ /learner/
COPY start.py .

WORKDIR /learner/methods/deap
RUN python3 setup.py install

WORKDIR /

EXPOSE 9002

#CMD tail -f /dev/null
CMD python3 -u start.py
