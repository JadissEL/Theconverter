"""
Batch processing support for multiple file conversions
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import uuid


@dataclass
class BatchJob:
    """Batch conversion job"""
    batch_id: str
    total_files: int
    completed_files: int
    failed_files: int
    status: str
    files: List[Dict[str, Any]]


class BatchProcessor:
    """
    Process multiple file conversions in parallel
    Optimized for throughput with concurrency limits
    """
    
    def __init__(self, max_concurrent: int = 3):
        """
        Initialize batch processor
        
        Args:
            max_concurrent: Maximum concurrent conversions
        """
        self.max_concurrent = max_concurrent
        self.batches: Dict[str, BatchJob] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_batch(
        self,
        files: List[Path],
        output_format: str,
        quality: str,
        converter_func: callable
    ) -> str:
        """
        Process a batch of files
        
        Args:
            files: List of input files
            output_format: Target format
            quality: Quality preset
            converter_func: Async conversion function
        
        Returns:
            Batch ID
        """
        batch_id = str(uuid.uuid4())
        
        # Create batch job
        batch = BatchJob(
            batch_id=batch_id,
            total_files=len(files),
            completed_files=0,
            failed_files=0,
            status="processing",
            files=[
                {
                    "filename": f.name,
                    "status": "pending",
                    "output_path": None,
                    "error": None
                }
                for f in files
            ]
        )
        
        self.batches[batch_id] = batch
        
        # Process files concurrently
        tasks = [
            self._process_single_file(
                batch_id,
                idx,
                file_path,
                output_format,
                quality,
                converter_func
            )
            for idx, file_path in enumerate(files)
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Mark batch as completed
        batch.status = "completed"
        
        return batch_id
    
    async def _process_single_file(
        self,
        batch_id: str,
        file_idx: int,
        file_path: Path,
        output_format: str,
        quality: str,
        converter_func: callable
    ):
        """Process a single file in the batch"""
        batch = self.batches[batch_id]
        
        async with self.semaphore:
            try:
                # Update status
                batch.files[file_idx]["status"] = "converting"
                
                # Perform conversion
                output_path = await converter_func(
                    file_path,
                    output_format,
                    quality
                )
                
                # Mark as completed
                batch.files[file_idx]["status"] = "completed"
                batch.files[file_idx]["output_path"] = str(output_path)
                batch.completed_files += 1
                
            except Exception as e:
                # Mark as failed
                batch.files[file_idx]["status"] = "failed"
                batch.files[file_idx]["error"] = str(e)
                batch.failed_files += 1
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a batch job"""
        batch = self.batches.get(batch_id)
        if not batch:
            return None
        
        return {
            "batch_id": batch.batch_id,
            "total_files": batch.total_files,
            "completed_files": batch.completed_files,
            "failed_files": batch.failed_files,
            "pending_files": batch.total_files - batch.completed_files - batch.failed_files,
            "status": batch.status,
            "progress": (batch.completed_files + batch.failed_files) / batch.total_files * 100,
            "files": batch.files
        }
    
    def cleanup_batch(self, batch_id: str):
        """Remove batch from memory"""
        if batch_id in self.batches:
            del self.batches[batch_id]
