FROM ubuntu:xenial
MAINTAINER Wei-Tsung Lin <fasthall@gmail.com>

RUN apt-get update
RUN apt-get install -y iperf wget build-essential
RUN wget https://www.openfabrics.org/downloads/qperf/qperf-0.4.9.tar.gz
RUN tar zxvf qperf-0.4.9.tar.gz
RUN rm qperf-0.4.9.tar.gz
WORKDIR /qperf-0.4.9
RUN ./configure
RUN make
RUN make install
WORKDIR /
RUN rm -rf /qperf-0.4.9
COPY ./download_large_file.sh /download_large_file.sh

EXPOSE 5001
