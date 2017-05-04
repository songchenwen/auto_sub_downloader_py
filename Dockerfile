FROM python:2-onbuild

MAINTAINER me@songchenwen.com

RUN sed -i "s/jessie main/jessie main contrib non-free/" /etc/apt/sources.list
RUN echo "deb http://http.debian.net/debian jessie-backports main contrib non-free" >> /etc/apt/sources.list
RUN apt-get update && apt-get install -y \
    ffmpeg

RUN apt-get install -y locales && \
    locale-gen C.UTF-8 && \
    /usr/sbin/update-locale LANG=C.UTF-8

ENV LC_ALL C.UTF-8

RUN ffmpeg -codecs

ENV TMP_DIR=/tmp/sub_downloader
RUN mkdir -p ${TMP_DIR}

ENV INPUT=/input
ENV OUTPUT=/output
ENV INTERVAL=3600

VOLUME ['/input']
VOLUME ['/output']

CMD ["python", "run.py", ${INPUT}, ${OUTPUT}]
