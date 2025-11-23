"""
File validation and security checks
"""

import magic
import hashlib
from pathlib import Path
from typing import Optional, List, Tuple
import mimetypes


class FileValidator:
    """
    Security-focused file validation
    Prevents malicious file uploads and validates file integrity
    """
    
    # Maximum file sizes by type (in bytes)
    MAX_SIZES = {
        'audio': 500 * 1024 * 1024,  # 500MB
        'video': 2 * 1024 * 1024 * 1024,  # 2GB
    }
    
    # Allowed MIME types
    ALLOWED_AUDIO_MIMES = {
        'audio/mpeg',
        'audio/mp3',
        'audio/wav',
        'audio/x-wav',
        'audio/wave',
        'audio/flac',
        'audio/x-flac',
        'audio/ogg',
        'audio/aac',
        'audio/mp4',
        'audio/m4a',
        'audio/x-m4a',
    }
    
    ALLOWED_VIDEO_MIMES = {
        'video/mp4',
        'video/x-msvideo',
        'video/avi',
        'video/quicktime',
        'video/x-matroska',
        'video/webm',
        'video/x-flv',
        'video/mpeg',
        'image/gif',
    }
    
    # Dangerous patterns in files
    DANGEROUS_PATTERNS = [
        b'<?php',
        b'<script',
        b'eval(',
        b'exec(',
        b'system(',
        b'shell_exec',
    ]
    
    def __init__(self):
        """Initialize validator"""
        try:
            self.magic = magic.Magic(mime=True)
            self.magic_available = True
        except:
            self.magic = None
            self.magic_available = False
    
    def validate_file_size(self, file_path: Path, media_type: str = 'video') -> Tuple[bool, Optional[str]]:
        """
        Validate file size
        
        Args:
            file_path: Path to file
            media_type: Type of media (audio/video)
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        file_size = file_path.stat().st_size
        max_size = self.MAX_SIZES.get(media_type, self.MAX_SIZES['video'])
        
        if file_size > max_size:
            return False, f"File too large: {file_size / 1024 / 1024:.2f}MB (max: {max_size / 1024 / 1024:.2f}MB)"
        
        if file_size == 0:
            return False, "File is empty"
        
        return True, None
    
    def validate_mime_type(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate MIME type using magic bytes
        
        Args:
            file_path: Path to file
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.magic_available:
            # Fallback to extension-based validation
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                return False, "Could not determine file type"
        else:
            mime_type = self.magic.from_file(str(file_path))
        
        # Check if MIME type is allowed
        allowed_mimes = self.ALLOWED_AUDIO_MIMES | self.ALLOWED_VIDEO_MIMES
        
        # Handle MIME type variations
        base_mime = mime_type.split(';')[0].strip()
        
        if base_mime not in allowed_mimes:
            # Check for wildcards
            mime_category = base_mime.split('/')[0]
            if mime_category not in ['audio', 'video', 'image']:
                return False, f"Unsupported file type: {base_mime}"
        
        return True, None
    
    def scan_for_malicious_content(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Scan file for potentially malicious content
        
        Args:
            file_path: Path to file
        
        Returns:
            Tuple of (is_safe, error_message)
        """
        try:
            # Read first 8KB for pattern matching
            with open(file_path, 'rb') as f:
                header = f.read(8192)
            
            # Check for dangerous patterns
            for pattern in self.DANGEROUS_PATTERNS:
                if pattern in header:
                    return False, f"Suspicious content detected"
            
            return True, None
            
        except Exception as e:
            return False, f"Error scanning file: {str(e)}"
    
    def validate_file_integrity(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate file can be read and is not corrupted
        
        Args:
            file_path: Path to file
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Try to read the entire file
            with open(file_path, 'rb') as f:
                chunk_size = 1024 * 1024  # 1MB chunks
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
            
            return True, None
            
        except Exception as e:
            return False, f"File integrity check failed: {str(e)}"
    
    def compute_checksum(self, file_path: Path) -> str:
        """
        Compute SHA256 checksum of file
        
        Args:
            file_path: Path to file
        
        Returns:
            Hex digest of SHA256 hash
        """
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(65536)
                if not data:
                    break
                sha256.update(data)
        
        return sha256.hexdigest()
    
    def full_validation(self, file_path: Path, media_type: str = 'video') -> Tuple[bool, List[str]]:
        """
        Perform full validation suite
        
        Args:
            file_path: Path to file
            media_type: Type of media
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # 1. File size validation
        valid, error = self.validate_file_size(file_path, media_type)
        if not valid:
            errors.append(error)
        
        # 2. MIME type validation
        valid, error = self.validate_mime_type(file_path)
        if not valid:
            errors.append(error)
        
        # 3. Malicious content scan
        valid, error = self.scan_for_malicious_content(file_path)
        if not valid:
            errors.append(error)
        
        # 4. File integrity check
        valid, error = self.validate_file_integrity(file_path)
        if not valid:
            errors.append(error)
        
        return len(errors) == 0, errors
