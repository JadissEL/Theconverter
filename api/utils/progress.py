"""
Progress tracking for long-running conversions
"""

import asyncio
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ConversionStatus(str, Enum):
    """Conversion status enumeration"""
    PENDING = "pending"
    UPLOADING = "uploading"
    VALIDATING = "validating"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ConversionProgress:
    """Progress information for a conversion job"""
    job_id: str
    status: ConversionStatus
    progress: float  # 0-100
    message: str
    filename: str
    output_format: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    output_path: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'job_id': self.job_id,
            'status': self.status.value,
            'progress': self.progress,
            'message': self.message,
            'filename': self.filename,
            'output_format': self.output_format,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error,
            'output_path': self.output_path
        }


class ProgressTracker:
    """
    Track progress of conversion jobs
    Useful for long-running conversions with WebSocket support
    """
    
    def __init__(self):
        """Initialize progress tracker"""
        self.jobs: Dict[str, ConversionProgress] = {}
        self.callbacks: Dict[str, list[Callable]] = {}
    
    def create_job(
        self,
        job_id: str,
        filename: str,
        output_format: str
    ) -> ConversionProgress:
        """
        Create a new conversion job
        
        Args:
            job_id: Unique job identifier
            filename: Input filename
            output_format: Output format
        
        Returns:
            ConversionProgress instance
        """
        progress = ConversionProgress(
            job_id=job_id,
            status=ConversionStatus.PENDING,
            progress=0.0,
            message="Job created",
            filename=filename,
            output_format=output_format,
            started_at=datetime.utcnow()
        )
        
        self.jobs[job_id] = progress
        return progress
    
    async def update_progress(
        self,
        job_id: str,
        status: Optional[ConversionStatus] = None,
        progress: Optional[float] = None,
        message: Optional[str] = None
    ):
        """
        Update job progress
        
        Args:
            job_id: Job identifier
            status: New status
            progress: Progress percentage (0-100)
            message: Status message
        """
        if job_id not in self.jobs:
            return
        
        job = self.jobs[job_id]
        
        if status is not None:
            job.status = status
        
        if progress is not None:
            job.progress = min(100.0, max(0.0, progress))
        
        if message is not None:
            job.message = message
        
        # Trigger callbacks
        if job_id in self.callbacks:
            for callback in self.callbacks[job_id]:
                try:
                    await callback(job)
                except Exception:
                    pass
    
    def complete_job(
        self,
        job_id: str,
        output_path: Optional[str] = None
    ):
        """
        Mark job as completed
        
        Args:
            job_id: Job identifier
            output_path: Path to output file
        """
        if job_id not in self.jobs:
            return
        
        job = self.jobs[job_id]
        job.status = ConversionStatus.COMPLETED
        job.progress = 100.0
        job.message = "Conversion completed"
        job.completed_at = datetime.utcnow()
        job.output_path = output_path
    
    def fail_job(
        self,
        job_id: str,
        error: str
    ):
        """
        Mark job as failed
        
        Args:
            job_id: Job identifier
            error: Error message
        """
        if job_id not in self.jobs:
            return
        
        job = self.jobs[job_id]
        job.status = ConversionStatus.FAILED
        job.message = "Conversion failed"
        job.completed_at = datetime.utcnow()
        job.error = error
    
    def get_job(self, job_id: str) -> Optional[ConversionProgress]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> list[ConversionProgress]:
        """Get all jobs"""
        return list(self.jobs.values())
    
    def register_callback(
        self,
        job_id: str,
        callback: Callable
    ):
        """
        Register callback for job updates
        
        Args:
            job_id: Job identifier
            callback: Async callback function
        """
        if job_id not in self.callbacks:
            self.callbacks[job_id] = []
        
        self.callbacks[job_id].append(callback)
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """
        Remove old completed/failed jobs
        
        Args:
            max_age_hours: Maximum age in hours
        """
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        jobs_to_remove = []
        for job_id, job in self.jobs.items():
            if job.completed_at and job.completed_at < cutoff:
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
            if job_id in self.callbacks:
                del self.callbacks[job_id]
