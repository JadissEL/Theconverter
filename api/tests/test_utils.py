"""
Unit tests for TheConverter API
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil

from utils.file_detector import FileDetector
from utils.validator import FileValidator
from utils.cache import ConversionCache
from utils.rate_limiter import RateLimiter, RateLimitConfig


class TestFileDetector:
    """Test file detection functionality"""
    
    @pytest.fixture
    def detector(self):
        return FileDetector()
    
    @pytest.mark.asyncio
    async def test_detect_by_magic_bytes(self, detector):
        """Test magic bytes detection"""
        # Create a test MP3 file with ID3 header
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
            f.write(b'ID3\x03\x00\x00\x00\x00\x00\x00')
            temp_path = Path(f.name)
        
        try:
            result = detector._detect_by_magic_bytes(temp_path)
            assert result == 'mp3'
        finally:
            temp_path.unlink()
    
    @pytest.mark.asyncio
    async def test_determine_media_type(self, detector):
        """Test media type determination"""
        assert detector._determine_media_type('mp3') == 'audio'
        assert detector._determine_media_type('mp4') == 'video'
        assert detector._determine_media_type('unknown') == 'unknown'


class TestFileValidator:
    """Test file validation"""
    
    @pytest.fixture
    def validator(self):
        return FileValidator()
    
    def test_validate_file_size_valid(self, validator):
        """Test file size validation - valid file"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test data' * 1000)
            temp_path = Path(f.name)
        
        try:
            valid, error = validator.validate_file_size(temp_path, 'audio')
            assert valid is True
            assert error is None
        finally:
            temp_path.unlink()
    
    def test_validate_file_size_too_large(self, validator):
        """Test file size validation - file too large"""
        # Mock a large file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            # Temporarily reduce max size for testing
            original_max = validator.MAX_SIZES['audio']
            validator.MAX_SIZES['audio'] = 100  # 100 bytes
            
            with open(temp_path, 'wb') as f:
                f.write(b'x' * 1000)
            
            valid, error = validator.validate_file_size(temp_path, 'audio')
            assert valid is False
            assert 'too large' in error.lower()
            
            # Restore original max size
            validator.MAX_SIZES['audio'] = original_max
        finally:
            temp_path.unlink()
    
    def test_scan_for_malicious_content(self, validator):
        """Test malicious content detection"""
        # Create file with suspicious content
        with tempfile.NamedTemporaryFile(delete=False, mode='wb') as f:
            f.write(b'<?php echo "malicious"; ?>')
            temp_path = Path(f.name)
        
        try:
            safe, error = validator.scan_for_malicious_content(temp_path)
            assert safe is False
            assert error is not None
        finally:
            temp_path.unlink()


class TestConversionCache:
    """Test caching functionality"""
    
    @pytest.fixture
    def cache(self):
        cache_dir = Path(tempfile.mkdtemp())
        cache = ConversionCache(cache_dir=str(cache_dir), max_cache_size_mb=10)
        yield cache
        shutil.rmtree(cache_dir)
    
    def test_generate_cache_key(self, cache):
        """Test cache key generation"""
        key1 = cache._generate_cache_key('hash1', 'mp3', 'high')
        key2 = cache._generate_cache_key('hash1', 'mp3', 'high')
        key3 = cache._generate_cache_key('hash2', 'mp3', 'high')
        
        assert key1 == key2  # Same inputs = same key
        assert key1 != key3  # Different inputs = different key
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, cache):
        """Test setting and getting from cache"""
        # Create test files
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
            f.write(b'test input')
            input_path = Path(f.name)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
            f.write(b'test output')
            output_path = Path(f.name)
        
        try:
            # Set cache
            await cache.set(
                input_path,
                output_path,
                'wav',
                'high',
                {'duration': 10}
            )
            
            # Recreate output file for testing get
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                f.write(b'test input')
                new_input_path = Path(f.name)
            
            # Get from cache
            cached = await cache.get(new_input_path, 'wav', 'high')
            
            assert cached is not None
            assert cached.exists()
            
            new_input_path.unlink()
            
        finally:
            if input_path.exists():
                input_path.unlink()


class TestRateLimiter:
    """Test rate limiting"""
    
    @pytest.fixture
    def limiter(self):
        return RateLimiter(RateLimitConfig(
            requests_per_minute=5,
            requests_per_hour=10,
            requests_per_day=20
        ))
    
    @pytest.mark.asyncio
    async def test_rate_limit_allows_requests(self, limiter):
        """Test that rate limiter allows valid requests"""
        for i in range(5):
            allowed, error = await limiter.check_rate_limit('test_client')
            assert allowed is True
            assert error is None
    
    @pytest.mark.asyncio
    async def test_rate_limit_blocks_excess(self, limiter):
        """Test that rate limiter blocks excess requests"""
        # Make 5 requests (at limit)
        for i in range(5):
            await limiter.check_rate_limit('test_client')
        
        # 6th request should be blocked
        allowed, error = await limiter.check_rate_limit('test_client')
        assert allowed is False
        assert error is not None
    
    def test_get_remaining(self, limiter):
        """Test getting remaining requests"""
        remaining = limiter.get_remaining('new_client')
        
        assert remaining['minute'] == 5
        assert remaining['hour'] == 10
        assert remaining['day'] == 20
    
    def test_reset(self, limiter):
        """Test resetting limits for a client"""
        limiter.minute_requests['test_client'] = [1, 2, 3]
        limiter.reset('test_client')
        
        assert len(limiter.minute_requests['test_client']) == 0


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
