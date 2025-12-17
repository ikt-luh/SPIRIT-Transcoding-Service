SERVER_IP=192.168.2.2  # Media Server from GPU1

for i in {0..3}; do
    docker run -d --gpus all \
        --name transcoder_worker_$i \
        -e REDIS_HOST=$SERVER_IP \
        -v /media:/media:ro \
        -v /media_cache:/media_cache \
        --network host \
        transcoder-worker:latest \
        python3 /app/src/transcoder_worker.py \
            --redis_host $SERVER_IP \
            --gpu_id 0 \
            --worker_id $i \
            --config_path /app/src/config.yaml
done