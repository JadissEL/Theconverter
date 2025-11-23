"""
Performance monitoring and profiling utilities
"""

import time
import psutil
import functools
from typing import Callable, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for an operation"""
    operation: str
    duration_ms: float
    cpu_percent: float
    memory_mb: float
    timestamp: datetime


class PerformanceMonitor:
    """
    Monitor performance of operations
    Track CPU, memory, and timing metrics
    """
    
    def __init__(self):
        """Initialize performance monitor"""
        self.metrics: list[PerformanceMetrics] = []
        self.process = psutil.Process()
    
    def record_metric(
        self,
        operation: str,
        duration_ms: float,
        cpu_percent: float,
        memory_mb: float
    ):
        """Record a performance metric"""
        metric = PerformanceMetrics(
            operation=operation,
            duration_ms=duration_ms,
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            timestamp=datetime.utcnow()
        )
        
        self.metrics.append(metric)
        
        # Keep only last 1000 metrics
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]
    
    def get_stats(self) -> dict:
        """Get performance statistics"""
        if not self.metrics:
            return {}
        
        durations = [m.duration_ms for m in self.metrics]
        cpu_usage = [m.cpu_percent for m in self.metrics]
        memory_usage = [m.memory_mb for m in self.metrics]
        
        return {
            'total_operations': len(self.metrics),
            'avg_duration_ms': sum(durations) / len(durations),
            'max_duration_ms': max(durations),
            'min_duration_ms': min(durations),
            'avg_cpu_percent': sum(cpu_usage) / len(cpu_usage),
            'avg_memory_mb': sum(memory_usage) / len(memory_usage),
            'max_memory_mb': max(memory_usage)
        }
    
    def clear(self):
        """Clear all metrics"""
        self.metrics.clear()


def profile_performance(operation_name: str):
    """
    Decorator to profile function performance
    
    Usage:
        @profile_performance("conversion")
        async def convert_file(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            process = psutil.Process()
            
            # Before
            start_time = time.time()
            start_cpu = process.cpu_percent()
            start_memory = process.memory_info().rss / 1024 / 1024
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                # After
                end_time = time.time()
                end_cpu = process.cpu_percent()
                end_memory = process.memory_info().rss / 1024 / 1024
                
                duration_ms = (end_time - start_time) * 1000
                cpu_delta = end_cpu - start_cpu
                memory_delta = end_memory - start_memory
                
                logger.info(
                    f"Performance [{operation_name}]: "
                    f"duration={duration_ms:.2f}ms, "
                    f"cpu_delta={cpu_delta:.2f}%, "
                    f"memory_delta={memory_delta:.2f}MB"
                )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            process = psutil.Process()
            
            # Before
            start_time = time.time()
            start_cpu = process.cpu_percent()
            start_memory = process.memory_info().rss / 1024 / 1024
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # After
                end_time = time.time()
                end_cpu = process.cpu_percent()
                end_memory = process.memory_info().rss / 1024 / 1024
                
                duration_ms = (end_time - start_time) * 1000
                cpu_delta = end_cpu - start_cpu
                memory_delta = end_memory - start_memory
                
                logger.info(
                    f"Performance [{operation_name}]: "
                    f"duration={duration_ms:.2f}ms, "
                    f"cpu_delta={cpu_delta:.2f}%, "
                    f"memory_delta={memory_delta:.2f}MB"
                )
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class ResourceMonitor:
    """Monitor system resources"""
    
    @staticmethod
    def get_system_info() -> dict:
        """Get current system resource information"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu': {
                'percent': cpu_percent,
                'count': psutil.cpu_count(),
            },
            'memory': {
                'total_mb': memory.total / 1024 / 1024,
                'available_mb': memory.available / 1024 / 1024,
                'used_mb': memory.used / 1024 / 1024,
                'percent': memory.percent,
            },
            'disk': {
                'total_gb': disk.total / 1024 / 1024 / 1024,
                'used_gb': disk.used / 1024 / 1024 / 1024,
                'free_gb': disk.free / 1024 / 1024 / 1024,
                'percent': disk.percent,
            }
        }
    
    @staticmethod
    def check_resource_availability(
        min_memory_mb: int = 500,
        min_disk_gb: int = 1
    ) -> tuple[bool, str]:
        """
        Check if sufficient resources are available
        
        Returns:
            Tuple of (is_available, message)
        """
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        available_memory_mb = memory.available / 1024 / 1024
        available_disk_gb = disk.free / 1024 / 1024 / 1024
        
        if available_memory_mb < min_memory_mb:
            return False, f"Insufficient memory: {available_memory_mb:.0f}MB available, {min_memory_mb}MB required"
        
        if available_disk_gb < min_disk_gb:
            return False, f"Insufficient disk space: {available_disk_gb:.1f}GB available, {min_disk_gb}GB required"
        
        return True, "Resources available"
