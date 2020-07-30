FROM ros:melodic-ros-base

RUN apt-get update
RUN apt-get install -y fping
COPY mios_package/ /mios/
COPY dependencies/ /dependencies/

EXPOSE 12000 12001 12002 8888 8889

WORKDIR mios/bin
CMD ["./mios.sh"]
#CMD tail -f /dev/null
