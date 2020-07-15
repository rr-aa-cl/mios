FROM ubuntu:18.04

COPY mios_package/ /mios/
COPY dependencies/ /dependencies/

EXPOSE 12000 12001 12002 8888 8889

WORKDIR mios/bin
CMD ["./_mios.sh"]
#CMD tail -f /dev/null
