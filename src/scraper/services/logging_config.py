"""
Structured logging configuration for the scraper system.
"""
import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def __init__(self, service_name: str = "scraper"):
        """Initialize structured formatter.
        
        Args:
            service_name: Name of the service for logging context
        """
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON formatted log string
        """
        # Base log structure
        log_obj = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_obj["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add extra fields from the log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
                'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage'
            }:
                extra_fields[key] = value
        
        if extra_fields:
            log_obj["extra"] = extra_fields
        
        return json.dumps(log_obj, ensure_ascii=False)


class ScraperLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds scraper-specific context."""
    
    def __init__(self, logger: logging.Logger, extra: Optional[Dict[str, Any]] = None):
        """Initialize adapter.
        
        Args:
            logger: Base logger
            extra: Extra context to add to all log messages
        """
        super().__init__(logger, extra or {})
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process log message and add context.
        
        Args:
            msg: Log message
            kwargs: Keyword arguments
            
        Returns:
            Processed message and kwargs
        """
        # Merge extra context
        extra = kwargs.get('extra', {})
        extra.update(self.extra)
        kwargs['extra'] = extra
        
        return msg, kwargs
    
    def scraping_start(self, url: str, max_properties: int = None) -> None:
        """Log scraping operation start.
        
        Args:
            url: URL being scraped
            max_properties: Maximum properties to scrape
        """
        self.info(
            "Scraping operation started",
            extra={
                "event_type": "scraping_start",
                "url": url,
                "max_properties": max_properties
            }
        )
    
    def scraping_end(self, url: str, properties_count: int, duration: float, success: bool = True) -> None:
        """Log scraping operation end.
        
        Args:
            url: URL that was scraped
            properties_count: Number of properties scraped
            duration: Duration in seconds
            success: Whether operation was successful
        """
        self.info(
            f"Scraping operation {'completed' if success else 'failed'}",
            extra={
                "event_type": "scraping_end",
                "url": url,
                "properties_count": properties_count,
                "duration_seconds": duration,
                "success": success
            }
        )
    
    def property_extracted(self, property_url: str, extraction_time: float, success: bool = True) -> None:
        """Log property extraction event.
        
        Args:
            property_url: URL of extracted property
            extraction_time: Time taken to extract
            success: Whether extraction was successful
        """
        level = logging.DEBUG if success else logging.WARNING
        message = f"Property {'extracted' if success else 'extraction failed'}"
        
        self.log(
            level,
            message,
            extra={
                "event_type": "property_extraction",
                "property_url": property_url,
                "extraction_time_ms": extraction_time * 1000,
                "success": success
            }
        )
    
    def validation_result(self, total_properties: int, valid_properties: int, errors: list) -> None:
        """Log validation results.
        
        Args:
            total_properties: Total properties validated
            valid_properties: Number of valid properties
            errors: List of validation errors
        """
        self.info(
            "Property validation completed",
            extra={
                "event_type": "validation_result",
                "total_properties": total_properties,
                "valid_properties": valid_properties,
                "error_count": len(errors),
                "validation_errors": errors[:5]  # Log first 5 errors
            }
        )
    
    def performance_metrics(self, metrics: Dict[str, Any]) -> None:
        """Log performance metrics.
        
        Args:
            metrics: Performance metrics dictionary
        """
        self.info(
            "Performance metrics",
            extra={
                "event_type": "performance_metrics",
                **metrics
            }
        )
    
    def error_with_context(self, message: str, error: Exception, context: Dict[str, Any] = None) -> None:
        """Log error with additional context.
        
        Args:
            message: Error message
            error: Exception object
            context: Additional context
        """
        extra = {
            "event_type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
        
        if context:
            extra.update(context)
        
        self.error(message, exc_info=error, extra=extra)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    service_name: str = "scraper",
    enable_console: bool = True,
    enable_structured: bool = True
) -> ScraperLoggerAdapter:
    """Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (optional)
        service_name: Service name for logging context
        enable_console: Whether to enable console logging
        enable_structured: Whether to use structured JSON logging
        
    Returns:
        Configured logger adapter
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set up formatters
    if enable_structured:
        formatter = StructuredFormatter(service_name)
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler (max 10MB per file, keep 5 files)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Create service-specific logger
    service_logger = logging.getLogger(service_name)
    
    # Create and return adapter
    adapter = ScraperLoggerAdapter(service_logger, {"service": service_name})
    
    return adapter


def setup_selenium_logging(log_level: str = "WARNING") -> None:
    """Configure Selenium logging to reduce noise.
    
    Args:
        log_level: Log level for Selenium components
    """
    selenium_loggers = [
        'selenium.webdriver.remote.remote_connection',
        'selenium.webdriver.common.service',
        'urllib3.connectionpool',
        'requests.packages.urllib3.connectionpool'
    ]
    
    for logger_name in selenium_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, log_level.upper()))


def setup_performance_logging() -> ScraperLoggerAdapter:
    """Set up performance-focused logging configuration.
    
    Returns:
        Performance logger adapter
    """
    return setup_logging(
        log_level="INFO",
        log_file="logs/scraper_performance.log",
        service_name="scraper_performance",
        enable_console=False,
        enable_structured=True
    )


def setup_error_logging() -> ScraperLoggerAdapter:
    """Set up error-focused logging configuration.
    
    Returns:
        Error logger adapter
    """
    return setup_logging(
        log_level="ERROR",
        log_file="logs/scraper_errors.log",
        service_name="scraper_errors",
        enable_console=True,
        enable_structured=True
    )


class LoggingContext:
    """Context manager for adding logging context."""
    
    def __init__(self, logger: ScraperLoggerAdapter, **context):
        """Initialize logging context.
        
        Args:
            logger: Logger adapter to modify
            **context: Context fields to add
        """
        self.logger = logger
        self.context = context
        self.original_extra = None
    
class LoggingMixin:
    """Mixin class for adding logging capabilities."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = None
    
    @property
    def logger(self) -> ScraperLoggerAdapter:
        """Get logger for this class."""
        if self._logger is None:
            class_name = self.__class__.__name__
            base_logger = logging.getLogger(f"scraper.{class_name}")
            self._logger = ScraperLoggerAdapter(
                base_logger, 
                {"component": class_name}
            )
        return self._logger


# Global logger instance
_global_logger: Optional[ScraperLoggerAdapter] = None


def get_logger() -> ScraperLoggerAdapter:
    """Get global logger instance.
    
    Returns:
        Global logger adapter
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = setup_logging()
        setup_selenium_logging()
    return _global_logger