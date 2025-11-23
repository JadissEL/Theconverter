"""
Configuration management for TheConverter API
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from functools import lru_cache


class CacheConfig(BaseModel):
    """Cache configuration"""
    enabled: bool = Field(default=True, description="Enable caching")
    size_mb: int = Field(default=1000, description="Maximum cache size in MB")
    max_age_hours: int = Field(default=24, description="Maximum cache age in hours")


class RateLimitConfig(BaseModel):
    """Rate limit configuration"""
    enabled: bool = Field(default=True, description="Enable rate limiting")
    requests_per_minute: int = Field(default=10, description="Requests per minute")
    requests_per_hour: int = Field(default=100, description="Requests per hour")
    requests_per_day: int = Field(default=1000, description="Requests per day")


class ConversionConfig(BaseModel):
    """Conversion configuration"""
    max_file_size_mb: int = Field(default=500, description="Maximum file size in MB")
    temp_dir: str = Field(default="/tmp/theconverter", description="Temporary directory")
    enable_hardware_acceleration: bool = Field(default=True, description="Enable GPU acceleration")
    max_concurrent_conversions: int = Field(default=3, description="Maximum concurrent conversions")


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = Field(default="INFO", description="Log level")
    log_file: str = Field(default="api/logs/app.log", description="Log file path")
    max_log_size_mb: int = Field(default=10, description="Maximum log file size")
    backup_count: int = Field(default=5, description="Number of backup log files")


class SecurityConfig(BaseModel):
    """Security configuration"""
    allowed_origins: list[str] = Field(default=["*"], description="Allowed CORS origins")
    enable_file_validation: bool = Field(default=True, description="Enable file validation")
    enable_malware_scan: bool = Field(default=True, description="Enable malware scanning")


class Settings(BaseModel):
    """Application settings"""
    # General
    app_name: str = Field(default="TheConverter API", description="Application name")
    version: str = Field(default="2.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment")
    
    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # Components
    cache: CacheConfig = Field(default_factory=CacheConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    conversion: ConversionConfig = Field(default_factory=ConversionConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    class Config:
        env_prefix = "THECONVERTER_"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings (cached)
    Load from environment variables with THECONVERTER_ prefix
    """
    return Settings(
        environment=os.getenv("ENVIRONMENT", "development"),
        port=int(os.getenv("PORT", "8000")),
        cache=CacheConfig(
            enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            size_mb=int(os.getenv("CACHE_SIZE_MB", "1000")),
            max_age_hours=int(os.getenv("CACHE_AGE_HOURS", "24"))
        ),
        rate_limit=RateLimitConfig(
            enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "10")),
            requests_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "100")),
            requests_per_day=int(os.getenv("RATE_LIMIT_PER_DAY", "1000"))
        ),
        conversion=ConversionConfig(
            max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "500")),
            temp_dir=os.getenv("TEMP_DIR", "/tmp/theconverter"),
            enable_hardware_acceleration=os.getenv("ENABLE_HW_ACCEL", "true").lower() == "true",
            max_concurrent_conversions=int(os.getenv("MAX_CONCURRENT", "3"))
        ),
        logging=LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "api/logs/app.log")
        ),
        security=SecurityConfig(
            allowed_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
            enable_file_validation=os.getenv("ENABLE_VALIDATION", "true").lower() == "true",
            enable_malware_scan=os.getenv("ENABLE_MALWARE_SCAN", "true").lower() == "true"
        )
    )
