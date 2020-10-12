FROM ubuntu:18.04

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
RUN apt-get install -y fping
COPY mios_package/ /mios/
COPY dependencies/ /dependencies/

EXPOSE 12000 12001 12002 8888 8889

ENV verbosity default_verbosity_value
ENV database_port default_database_port_value

WORKDIR mios/bin
CMD ["sh", "-c", "./mios.sh --verbosity=${verbosity} --database_port=${database_port}"]
