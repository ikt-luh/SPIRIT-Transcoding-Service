FROM pyrabbit-transcoder-hw

RUN pip install --no-cache-dir redis

RUN mkdir -p /media /media_cache /app/src

ENV MEDIA_DIR=/media
ENV TMP_DIR=/media_cache/tmp
ENV SOURCE_DIR=/app/src

COPY ./src/ /app/src/
WORKDIR /app/src

# Default command
CMD ["python3", "transcoder_worker.py"]
