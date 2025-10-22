FROM ubuntu:20.04

RUN apt-get update
RUN apt-get install -y --no-install-recommends python3-pip
RUN pip3 install -Iv 'setuptools==57.5.0'
RUN pip3 install -U numpy
RUN pip3 install -U scipy
RUN pip3 install -U pymongo
RUN pip3 install -U scikit-learn
RUN pip3 install -U requests
RUN pip3 install -U pyDOE scikit-optimize
RUN pip3 install -U websockets
RUN pip3 install -U deap
RUN pip3 install -U ifaddr



COPY ml_service/ /mios_mls/

EXPOSE 8000 8001

WORKDIR mios_mls

CMD ["python3", "./start_interface.py"]
