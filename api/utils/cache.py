"""
Advanced caching system for conversion optimization
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
import asyncio
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    file_hash: str
    output_format: str
    quality: str
    file_path: str
    created_at: float
    size: int
    metadata: Dict[str, Any]


class ConversionCache:
    """
    Smart caching system for converted files
    Avoids re-converting identical files with same settings
    """
    
    def __init__(
        self,
        cache_dir: str = "/tmp/theconverter_cache",
        max_cache_size_mb: int = 1000,
        max_age_hours: int = 24
    ):
        """
        Initialize cache system
        
        Args:
            cache_dir: Directory for cached files
            max_cache_size_mb: Maximum cache size in MB
            max_age_hours: Maximum age of cache entries in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_cache_size = max_cache_size_mb * 1024 * 1024
        self.max_age = timedelta(hours=max_age_hours)
        
        self.index_file = self.cache_dir / "cache_index.json"
        self.index: Dict[str, CacheEntry] = {}
        
        self._load_index()
    
    def _load_index(self):
        """Load cache index from disk"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    data = json.load(f)
                    self.index = {
                        k: CacheEntry(**v) for k, v in data.items()
                    }
            except Exception:
                self.index = {}
    
    def _save_index(self):
        """Save cache index to disk"""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(
                    {k: asdict(v) for k, v in self.index.items()},
                    f,
                    indent=2
                )
        except Exception as e:
            print(f"Failed to save cache index: {e}")
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file"""
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(65536)  # 64KB chunks
                if not data:
                    break
                sha256.update(data)
        
        return sha256.hexdigest()
    
    def _generate_cache_key(
        self,
        file_hash: str,
        output_format: str,
        quality: str
    ) -> str:
        """Generate unique cache key"""
        key_data = f"{file_hash}_{output_format}_{quality}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(
        self,
        input_file: Path,
        output_format: str,
        quality: str
    ) -> Optional[Path]:
        """
        Get cached conversion if available
        
        Args:
            input_file: Original input file
            output_format: Desired output format
            quality: Quality preset
        
        Returns:
            Path to cached file or None if not found
        """
        # Compute file hash
        file_hash = await asyncio.to_thread(
            self._compute_file_hash,
            input_file
        )
        
        # Generate cache key
        cache_key = self._generate_cache_key(file_hash, output_format, quality)
        
        # Check if entry exists
        if cache_key not in self.index:
            return None
        
        entry = self.index[cache_key]
        cached_file = Path(entry.file_path)
        
        # Verify file exists
        if not cached_file.exists():
            del self.index[cache_key]
            self._save_index()
            return None
        
        # Check age
        age = datetime.now() - datetime.fromtimestamp(entry.created_at)
        if age > self.max_age:
            cached_file.unlink()
            del self.index[cache_key]
            self._save_index()
            return None
        
        return cached_file
    
    async def set(
        self,
        input_file: Path,
        output_file: Path,
        output_format: str,
        quality: str,
        metadata: Dict[str, Any]
    ):
        """
        Store converted file in cache
        
        Args:
            input_file: Original input file
            output_file: Converted output file
            output_format: Output format
            quality: Quality preset
            metadata: Additional metadata
        """
        # Compute file hash
        file_hash = await asyncio.to_thread(
            self._compute_file_hash,
            input_file
        )
        
        # Generate cache key
        cache_key = self._generate_cache_key(file_hash, output_format, quality)
        
        # Create cache filename
        cache_filename = f"{cache_key}.{output_format}"
        cached_file = self.cache_dir / cache_filename
        
        # Copy file to cache
        await asyncio.to_thread(
            output_file.rename,
            cached_file
        )
        
        # Create cache entry
        entry = CacheEntry(
            key=cache_key,
            file_hash=file_hash,
            output_format=output_format,
            quality=quality,
            file_path=str(cached_file),
            created_at=time.time(),
            size=cached_file.stat().st_size,
            metadata=metadata
        )
        
        # Add to index
        self.index[cache_key] = entry
        self._save_index()
        
        # Cleanup if needed
        await self._cleanup_if_needed()
    
    async def _cleanup_if_needed(self):
        """Remove old entries if cache is too large"""
        total_size = sum(entry.size for entry in self.index.values())
        
        if total_size > self.max_cache_size:
            # Sort by age (oldest first)
            entries = sorted(
                self.index.items(),
                key=lambda x: x[1].created_at
            )
            
            # Remove oldest until under limit
            for key, entry in entries:
                if total_size <= self.max_cache_size * 0.8:
                    break
                
                file_path = Path(entry.file_path)
                if file_path.exists():
                    file_path.unlink()
                    total_size -= entry.size
                
                del self.index[key]
            
            self._save_index()
    
    def clear(self):
        """Clear all cache entries"""
        for entry in self.index.values():
            file_path = Path(entry.file_path)
            if file_path.exists():
                file_path.unlink()
        
        self.index.clear()
        self._save_index()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_size = sum(entry.size for entry in self.index.values())
        
        return {
            'total_entries': len(self.index),
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'max_size_mb': self.max_cache_size / 1024 / 1024,
            'utilization': round(total_size / self.max_cache_size * 100, 2),
            'oldest_entry': min(
                (e.created_at for e in self.index.values()),
                default=None
            ),
            'newest_entry': max(
                (e.created_at for e in self.index.values()),
                default=None
            )
        }
