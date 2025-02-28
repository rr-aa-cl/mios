FROM ubuntu:20.04

RUN apt-get update
RUN apt-get install -y --no-install-recommends python3-pip
RUN pip3 install -U ifaddr

#RUN apt-get install -y git
#RUN git clone https://github.com/DEAP/deap.git
#RUN cd deap && python3 setup.py install && cd .. && rm -r deap


COPY ml_service/rpc_visualization  /vis/

EXPOSE 8002 8003 8004

WORKDIR vis

CMD ["python3", "-u", "./switcher.py"]
