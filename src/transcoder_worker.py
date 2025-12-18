import os
import time
import ast
import redis
import argparse

from rabbit import Transcoder, TranscoderConfig, BitstreamIO

def worker_process(redis_host="192.168.1.10", gpu_id=0, worker_id=0, configs=None, log_queue=None):
    """
    Polls Redis job queue, runs _worker_process2 style transcoding.
    """

    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)

    # Initialize default config
    default_cfg = configs["1"]
    transcoder = Transcoder(
        TranscoderConfig(
            use_cuda=default_cfg.get("cuda", True),
            geometry_qp=default_cfg.get("geoQP", 32),
            attribute_qp=default_cfg.get("attQP", 32),
            preset=default_cfg.get("preset", "p2"),
            gpuID=gpu_id,
        )
    )
    bitio = BitstreamIO()
    r = redis.Redis(host=redis_host, port=6379, decode_responses=True)

    def log(event, job_id=None):
        if log_queue is not None:
            print("Logging")
            log_queue.put({
                "timestamp": time.time(),
                "worker_gpu": gpu_id,
                "worker_id": worker_id,
                "event": event,
                "job_id": job_id,
            })
        else:
            print("timestamp {}, worker_GPU: {}, worker_id: {}, event {}, job_id {}".format(
                time.time(), gpu_id, worker_id, event, job_id
            ))

    while True:
        job_str = r.blpop("transcoder_jobs", timeout=5)
        if not job_str:
            continue  # timeout, poll again

        job_data = ast.literal_eval(job_str[1])  # safe because we control the format
        job_id = job_data["job_id"]
        src_path = job_data["src_path"]
        out_path = job_data["out_path"]
        config_id = job_data["cfg_id"]

        try:
            log("decode_start", job_id)
            contexts = bitio.read(src_path)
            log("decode_end", job_id)

            cfg_dict = configs[config_id]
            transcoder.set_config(
                TranscoderConfig(
                    use_cuda=cfg_dict.get("cuda", True),
                    geometry_qp=cfg_dict.get("geoQP", 32),
                    attribute_qp=cfg_dict.get("attQP", 32),
                    preset=cfg_dict.get("preset", "p2"),
                    gpuID=gpu_id,
                )
            )

            log("gpu_start", job_id)
            transcoder.transcode_contexts(contexts)
            log("gpu_end", job_id)

            log("write_start", job_id)
            bitio.write(contexts, out_path)
            os.sync()
            log("write_end", job_id)

            # push job completion to Redis
            #r.rpush("transcoder_done", job_id)
            r.setex(f"job_done:{job_id}", 60, "ok")

        except Exception as e:
            log(f"error: {e}", job_id)
            #r.rpush("transcoder_done", job_id)
            r.setex(f"job_done:{job_id}", 60, "ok")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GPU Transcoder Worker")
    parser.add_argument("--redis_host", type=str, required=True, help="IP of Redis backend")
    parser.add_argument("--gpu_id", type=int, default=0, help="GPU ID to use")
    parser.add_argument("--worker_id", type=int, default=0, help="Worker ID")
    parser.add_argument("--config_path", type=str, required=True, help="Path to transcoder config YAML")
    args = parser.parse_args()

    import yaml
    with open(args.config_path, "r") as f:
        configs = yaml.safe_load(f)["transcoder"]

    worker_process(
        redis_host=args.redis_host,
        gpu_id=args.gpu_id,
        worker_id=args.worker_id,
        configs=configs,
    )
