FROM debian:12

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y \
    build-essential \
    curl

WORKDIR /root

COPY ./install.sh /root
RUN chmod +x /root/install.sh

#CMD ["bash", "-c", "./install.sh; bash"]
CMD ["bash", "-c", "./install.sh --verbose; bash"]

# docker build --no-cache -t debian -f install_test/linux/Dockerfile . && docker run -it debian