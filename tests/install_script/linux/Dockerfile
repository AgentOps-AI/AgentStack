FROM debian:12

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y \
    build-essential \
    git \
    # \ 
    #curl
    wget

#    build-essential \


WORKDIR /root

COPY ./install.sh /root
RUN chmod +x /root/install.sh

#CMD ["bash", "-c", "./install.sh; bash"]
#CMD ["bash", "-c", "./install.sh --verbose; bash"]
#CMD ["bash", "-c", "./install.sh --version=\"0.3.4\"; bash"]
#CMD ["bash", "-c", "./install.sh --dev-branch=main; bash"]
CMD ["bash", "-c", "./install.sh --dev-branch=\"pull/318/head:pr-318\"; bash"]

# docker build -t debian -f tests/install_script/linux/Dockerfile . && docker run -it debian