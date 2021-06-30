FROM ubuntu:20.04

RUN apt-get update
RUN apt-get install -y --no-install-recommends python3-pip
RUN pip3 install -U setuptools
RUN pip3 install -U numpy
RUN pip3 install -U scipy
RUN pip3 install -U pymongo
RUN pip3 install -U sklearn
RUN pip3 install -U requests
RUN pip3 install -U pyDOE scikit-optimize
RUN pip3 install -U websockets

RUN apt-get install -y git
RUN git clone https://github.com/DEAP/deap.git
RUN cd deap && python3 setup.py install && cd .. && rm -r deap

COPY ml_service/ /mios_mls/

EXPOSE 8000 8001

WORKDIR mios_mls

CMD ["python3", "./start_interface.py"]
