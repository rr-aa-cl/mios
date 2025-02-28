FROM ubuntu:20.04

RUN apt-get update
RUN apt-get install -y --no-install-recommends python3-pip
RUN pip3 install -U numpy
RUN pip3 install -U scipy
RUN pip3 install -U pymongo
RUN pip3 install -U scikit-learn
RUN pip3 install -U requests
RUN pip3 install -U pyDOE scikit-optimize
RUN pip3 install -U websockets
RUN pip3 install -U deap
RUN pip3 install -U ifaddr
# RUN pip install torch==2.0.0 --index-url https://download.pytorch.org/whl/cpu
RUN pip3 install torch==1.9.0+cpu torchvision==0.10.0+cpu torchaudio==0.9.0 -f https://download.pytorch.org/whl/torch_stable.html

COPY docker/cpu_cuda/py/ /cuda_py/

# EXPOSE 8000 8001

WORKDIR cuda_py

CMD ["python3", "./test_cuda.py"]