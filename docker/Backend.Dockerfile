FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl git build-essential cmake pkg-config libclang-dev vim \
    python3 python3-dev python3-distutils python3-pip \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir fastapi uvicorn redis pyyaml numpy

RUN mkdir -p /media /media_cache /app/src

ENV MEDIA_DIR=/media
ENV TMP_DIR=/media_cache/tmp
ENV SOURCE_DIR=/app/src

COPY ./src/ /app/src/
WORKDIR /app/src

EXPOSE 8000

CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]