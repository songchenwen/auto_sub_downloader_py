FROM python:2-onbuild

MAINTAINER me@songchenwen.com

RUN apt-get install ffmpeg

ENV INPUT=/input
ENV OUTPUT=/output
ENV INTERVAL=3600

VOLUME ['/input']
VOLUME ['/output']

CMD ["python", "run.py", ${INPUT}, ${OUTPUT}]
