############################################################
# Dockerfile to build sandbox for executing user code
# Based on Ubuntu 16.04
############################################################

FROM ubuntu:16.04
MAINTAINER crazyX

# set noninteractive env
ENV DEBIAN_FRONTEND noninteractive

# Update the source list
# Install all the languages/compilers we are supporting.
# default: c, c++, python, ruby, go, java7
RUN apt-get update && \
    apt-get install -y gcc && \
	apt-get install -y g++ && \
	apt-get install -y python && \
	apt-get install -y ruby && \
	apt-get install -y golang-go

RUN apt-get install -y time

# Install java8 (auto accept licence)
RUN apt-get install -y  software-properties-common && \
	add-apt-repository ppa:webupd8team/java -y && \
    echo debconf shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && \
    echo debconf shared/accepted-oracle-license-v1-1 seen true | debconf-set-selections && \
	apt-get update && \
	apt-get install -y oracle-java8-installer && \
	apt-get clean && \
	apt-get autoremove


