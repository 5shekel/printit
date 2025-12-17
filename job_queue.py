import queue
import threading
import time
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

logger = logging.getLogger("sticker_factory.job_queue")

@dataclass
class PrintJob:
    id: str
    image: Any  # PIL Image
    params: Dict[str, Any]
    status: str = "pending"  # pending, processing, completed, failed
    error: Optional[str] = None
    created_at: datetime = None
    completed_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class PrintQueue:
    def __init__(self):
        self.queue = queue.Queue()
        self.jobs = {}  # Store all jobs for status tracking
        self.lock = threading.Lock()
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        self.is_processing = False
        self._cleanup_thread = threading.Thread(target=self._cleanup_old_jobs, daemon=True)
        self._cleanup_thread.start()

    def _cleanup_old_jobs(self):
        """Periodically clean up old completed jobs"""
        while True:
            time.sleep(3600)  # Run every hour
            with self.lock:
                now = datetime.now()
                # Keep only jobs from the last 24 hours
                self.jobs = {
                    job_id: job for job_id, job in self.jobs.items()
                    if (job.status in ["pending", "processing"] or 
                        (now - job.created_at).total_seconds() < 86400)
                }

    def add_job(self, image, **params) -> str:
        """Add a new print job to the queue"""
        job_id = str(uuid.uuid4())
        job = PrintJob(
            id=job_id,
            image=image,
            params=params
        )
        self.jobs[job_id] = job
        self.queue.put(job)
        return job_id

    def get_job_status(self, job_id: str) -> Optional[PrintJob]:
        """Get the status of a specific job"""
        return self.jobs.get(job_id)

    def get_queue_status(self):
        """Get overall queue status"""
        with self.lock:
            # Filter and sort jobs
            active_jobs = {
                job_id: job for job_id, job in self.jobs.items()
                if (
                    # Keep jobs that are pending or processing
                    job.status in ["pending", "processing"] or
                    # Keep completed/failed jobs from the last hour
                    (job.completed_at and (datetime.now() - job.completed_at).total_seconds() < 3600)
                )
            }
            
            # Sort jobs by creation time (most recent first)
            sorted_jobs = dict(sorted(
                active_jobs.items(),
                key=lambda x: x[1].created_at if x[1].created_at else datetime.min,
                reverse=True
            ))

            return {
                "queue_size": self.queue.qsize(),
                "is_processing": self.is_processing,
                "jobs": {
                    job_id: {
                        "status": job.status,
                        "created_at": job.created_at,
                        "completed_at": job.completed_at,
                        "error": job.error
                    } for job_id, job in sorted_jobs.items()
                }
            }

    def _process_queue(self):
        """Worker thread to process print jobs"""
        while True:
            try:
                job = self.queue.get()
                if job is None:
                    continue

                with self.lock:
                    self.is_processing = True
                    job.status = "processing"

                try:
                    # Import here to make it mockable in tests
                    from printer_utils import process_print_job
                    
                    # Process the print job using our printer handler
                    success, error = process_print_job(
                        job.image,
                        job.params["printer_info"],
                        job.params["temp_file_path"],
                        rotate=job.params.get("rotate", 0),
                        dither=job.params.get("dither", False),
                        label_type=job.params.get("label_type", "102")
                    )

                    if success:
                        job.status = "completed"
                        job.completed_at = datetime.now()
                    else:
                        job.status = "failed"
                        job.error = error

                except Exception as e:
                    job.status = "failed"
                    job.error = str(e)
                    logger.error(f"Error processing job {job.id}: {e}")

                finally:
                    self.is_processing = False
                    self.queue.task_done()

            except Exception as e:
                logger.error(f"Error in queue processor: {e}")
                time.sleep(1)  # Prevent tight loop on repeated errors

# Global print queue instance
print_queue = PrintQueue() 