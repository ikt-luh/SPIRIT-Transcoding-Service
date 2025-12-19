import time
import uuid
import asyncio
import redis
import ast
from pathlib import Path

class RedisTranscoderPool:
    """
    Submits jobs to Redis for distributed workers, keeps logging.
    """

    def __init__(self, redis_host: str, logger, redis_port: int = 6379):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.logger = logger  # CSVLogger instance
        self.inflight = set()
        self.lock = asyncio.Lock()

    async def submit(self, cfg_id: str, src_path: str, out_path: str):
        job_id = uuid.uuid4().hex

        with open(src_path, "rb") as f:
            file_bytes = f.read()  # read file into memory

        job_data = {
            "job_id": job_id,
            "cfg_id": cfg_id,
            "file_bytes": file_bytes.hex(),
            "src_path": src_path,
            "out_path": out_path,
        }
        self.r.rpush("transcoder_jobs", str(job_data))
        async with self.lock:
            self.inflight.add(job_id)

        # Logging
        self.logger.queue.put({
            "timestamp": time.time(),
            "worker_gpu": None,
            "worker_id": None,
            "event": "submitted",
            "job_id": job_id,
            "q_decode": None,
            "q_gpu": None,
        })
        return job_id

    async def wait_job(self, job_id: str, timeout: float = 30):
        key = f"job_done:{job_id}"
        start = time.time()
    
        while True:
            if self.r.exists(key):
                result_str = self.r.get(key)
                if result_str:
                    result_data = ast.literal_eval(result_str)
                else:
                    return False

                async with self.lock:
                    self.inflight.discard(job_id)

                if "error" in result_data:
                    # Worker failed
                    raise RuntimeError(f"Worker failed for job {job_id}: {result_data['error']}")

                # Write output file
                out_path = result_data.get("out_path") 
                file_bytes = bytes.fromhex(result_data["file_bytes"])
                print(out_path)
                Path(out_path).parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "wb") as f:
                    f.write(file_bytes)

                return out_path
    
            if time.time() - start > timeout:
                async with self.lock:
                    self.inflight.discard(job_id)
                return False
    
            await asyncio.sleep(0.05)

    def current_queue_length(self):
        return self.r.llen("transcoder_jobs") + len(self.inflight)
