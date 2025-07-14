"""
Professional Scraper Manager that orchestrates all scraping operations.
"""
import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from ...utils.config import settings
from ..domain.assetplan_extractor_v2 import AssetPlanExtractorV2
from ..domain.data_validator import (PropertyCollectionValidator,
                                     PropertyDataValidator)
from ..domain.retry_manager import (CommonCircuitConfigs, CommonRetryConfigs,
                                    RetryManager)
from ..infrastructure.human_behavior import (BehaviorConfig,
                                             HumanBehaviorSimulator)
from ..infrastructure.performance_monitor import (PerformanceAlerts,
                                                  PerformanceMonitor)
from ..infrastructure.webdriver_factory import DriverManager
from ..models import PropertyCollection
from .logging_config import LoggingContext, ScraperLoggerAdapter, get_logger


@dataclass
class ScrapingConfig:
    """Configuration for scraping operations."""
    max_properties: int = 50
    max_typologies: Optional[int] = None  # New: limit number of typologies/buildings to scrape
    max_links_per_page: int = 100
    enable_detail_page_extraction: bool = False
    behavior_mode: str = "extreme"  # extreme (default), fast, normal, slow, very_slow
    retry_strategy: str = "fast"  # fast (default), standard, aggressive, patient
    circuit_breaker_mode: str = "tolerant"  # tolerant (default), standard, sensitive
    enable_validation: bool = False  # Disabled by default for speed
    enable_performance_monitoring: bool = False  # Disabled by default for speed
    save_raw_data: bool = True
    output_file: Optional[str] = None
    debug_mode: bool = False  # Enable visual debugging with browser
    human_like_behavior: bool = False  # Enable human-like behavior simulation (optional)


class ScraperManager:
    """Professional scraper manager with full orchestration capabilities."""
    
    def __init__(self, 
                 config: Optional[ScrapingConfig] = None,
                 logger: Optional[ScraperLoggerAdapter] = None):
        """Initialize the scraper manager.
        
        Args:
            config: Scraping configuration
            logger: Logger instance
        """
        self.config = config or ScrapingConfig()
        self.logger = logger or get_logger()
        
        # Initialize components
        self._setup_components()
        
        # State tracking
        self.is_running = False
        self.current_operation: Optional[str] = None
        self.start_time: Optional[datetime] = None

    def __enter__(self):
        """Enter context: return self."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context: stop scraper and clean up."""
        self.stop()
        
    def _setup_components(self) -> None:
        """Set up all scraper components."""
        # Driver management
        debug_mode = getattr(self.config, 'debug_mode', False)
        extreme_mode = (self.config.behavior_mode == "extreme")
        
        self.driver_manager = DriverManager(
            driver_type="chrome",
            headless=settings.headless_browser and not debug_mode,  # Force visible in debug mode (even in extreme)
            stealth_mode=not debug_mode and not extreme_mode,  # Disable stealth in debug/extreme mode
            performance_optimized=not debug_mode and not extreme_mode,  # Disable optimizations in debug/extreme mode
            debug_mode=debug_mode
        )
        
        # Performance monitoring
        if self.config.enable_performance_monitoring:
            self.performance_monitor = PerformanceMonitor()
            self.performance_alerts = PerformanceAlerts(self.performance_monitor)
        else:
            self.performance_monitor = None
            self.performance_alerts = None
        
        # Retry management
        retry_configs = {
            "fast": CommonRetryConfigs.FAST,
            "standard": CommonRetryConfigs.STANDARD,
            "aggressive": CommonRetryConfigs.AGGRESSIVE,
            "patient": CommonRetryConfigs.PATIENT
        }
        
        circuit_configs = {
            "sensitive": CommonCircuitConfigs.SENSITIVE,
            "standard": CommonCircuitConfigs.STANDARD,
            "tolerant": CommonCircuitConfigs.TOLERANT
        }
        
        self.retry_manager = RetryManager(
            retry_config=retry_configs.get(self.config.retry_strategy, CommonRetryConfigs.STANDARD),
            circuit_config=circuit_configs.get(self.config.circuit_breaker_mode, CommonCircuitConfigs.STANDARD)
        )
        
        # Validators
        if self.config.enable_validation:
            self.property_validator = PropertyDataValidator()
            self.collection_validator = PropertyCollectionValidator()
        else:
            self.property_validator = None
            self.collection_validator = None
    
    def scrape_properties(self, 
                         base_url: str = "https://www.assetplan.cl/propiedades",
                         progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> PropertyCollection:
        """Main method to scrape properties with full orchestration.
        
        Args:
            base_url: Base URL to start scraping from
            progress_callback: Optional callback for progress updates
            
        Returns:
            PropertyCollection with scraped and validated properties
        """
        self.is_running = True
        self.start_time = datetime.now()
        self.current_operation = "initializing"
        
        try:
            # Start monitoring
            if self.performance_monitor:
                self.performance_monitor.start_monitoring()
            
            with LoggingContext(self.logger, operation="scrape_properties", base_url=base_url):
                self.logger.scraping_start(base_url, self.config.max_properties)
                
                # Execute scraping with retry logic
                collection = self.retry_manager.execute_with_retry(
                    self._execute_scraping_workflow,
                    base_url,
                    progress_callback,
                    retry_on=[Exception],
                    no_retry_on=[KeyboardInterrupt]
                )
                
                self.logger.scraping_end(
                    base_url, 
                    collection.total_count, 
                    self._get_elapsed_time(),
                    success=True
                )
                
                return collection
                
        except Exception as e:
            self.logger.error_with_context(
                "Scraping operation failed",
                e,
                {"operation": self.current_operation, "elapsed_time": self._get_elapsed_time()}
            )
            
            # Return empty collection with error info
            return PropertyCollection(
                properties=[],
                total_count=0,
                scraped_at=datetime.now().isoformat(),
                source_url=base_url
            )
        
        finally:
            self.is_running = False
            self.current_operation = None
            
            # Stop monitoring and generate reports
            if self.performance_monitor:
                self.performance_monitor.stop_monitoring()
                self._log_final_performance_report()
    
    def _execute_scraping_workflow(self, 
                                  base_url: str,
                                  progress_callback: Optional[Callable[[Dict[str, Any]], None]]) -> PropertyCollection:
        """Execute the complete scraping workflow.
        
        Args:
            base_url: Base URL to scrape
            progress_callback: Progress callback function
            
        Returns:
            Scraped and processed property collection
        """
        # Phase 1: Setup and Navigation
        self.current_operation = "setup"
        self._report_progress("Setting up scraper components", 0, progress_callback)
        
        driver = self.driver_manager.get_driver()
        behavior_config = BehaviorConfig.get_config(self.config.behavior_mode)
        behavior = HumanBehaviorSimulator(
            driver, 
            speed_factor=behavior_config.get("speed_factor", 1.0)
        )
        # Use the updated extractor that follows the guide specifications
        extractor_v2 = AssetPlanExtractorV2(driver, base_url="https://www.assetplan.cl")
        
        # Configure extractor modes
        if self.config.debug_mode:
            extractor_v2.enable_debug_mode(True)
        
        # Configure human-like behavior and extreme mode
        extractor_v2.configure_behavior_mode(
            human_like=self.config.human_like_behavior,
            behavior_mode=self.config.behavior_mode
        )
        
        # Phase 2: Extract Properties using V2 Extractor (follows guide flow)
        self.current_operation = "extraction"
        self._report_progress("Extracting properties using guide methodology", 20, progress_callback)
        
        request_id = self.performance_monitor.record_request_start() if self.performance_monitor else None
        start_time = time.time()
        
        try:
            # Use the new V2 extractor that follows the complete guide flow
            collection = extractor_v2.start_scraping(
                max_properties=self.config.max_properties,
                max_typologies=self.config.max_typologies
            )
            
            if self.performance_monitor:
                self.performance_monitor.record_request_success(request_id, time.time() - start_time)
                for _ in collection.properties:
                    self.performance_monitor.record_property_scraped()
            
            self.logger.info(
                f"Successfully extracted {collection.total_count} properties using V2 extractor",
                extra={"properties_count": collection.total_count, "extractor_version": "v2", "typologies_count": len(collection.typologies)}
            )
            
        except Exception as e:
            if self.performance_monitor:
                self.performance_monitor.record_request_failure(request_id, type(e).__name__, str(e))
            
            self.logger.error_with_context("V2 extractor failed", e)
            collection = PropertyCollection(
                properties=[],
                total_count=0,
                scraped_at=datetime.now().isoformat(),
                source_url=base_url
            )
        
        # Phase 5: Validation and Cleaning
        if self.config.enable_validation and collection.properties:
            self.current_operation = "validation"
            self._report_progress("Validating and cleaning data", 85, progress_callback)
            
            validated_properties, validation_summary = self.collection_validator.validate_collection(collection.properties)
            
            # Update collection with validated properties
            collection.properties = validated_properties
            collection.total_count = len(validated_properties)
            
            self.logger.validation_result(
                total_properties=len(collection.properties),
                valid_properties=len(validated_properties),
                errors=validation_summary.get('error_details', [])
            )
        
        # Phase 6: Finalize Collection
        self.current_operation = "finalization"
        self._report_progress("Finalizing collection", 95, progress_callback)
        
        # Phase 7: Save Results
        if self.config.save_raw_data:
            self._save_collection(collection)
        
        self._report_progress("Scraping completed", 100, progress_callback)
        
        return collection
    
    
    def _save_collection(self, collection: PropertyCollection) -> None:
        """Save property collection to file.
        
        Args:
            collection: Collection to save
        """
        try:
            output_file = self.config.output_file or settings.properties_json_path
            
            # Ensure output directory exists
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(collection.model_dump(mode='json'), f, ensure_ascii=False, indent=2)
            
            self.logger.info(
                f"Properties saved to {output_file}",
                extra={"output_file": output_file, "properties_count": collection.total_count}
            )
            
        except Exception as e:
            self.logger.error_with_context("Failed to save properties", e)
    
    def _report_progress(self, 
                        message: str, 
                        percentage: float, 
                        callback: Optional[Callable[[Dict[str, Any]], None]]) -> None:
        """Report progress to callback and logs.
        
        Args:
            message: Progress message
            percentage: Completion percentage (0-100)
            callback: Optional progress callback
        """
        progress_data = {
            "message": message,
            "percentage": percentage,
            "elapsed_time": self._get_elapsed_time(),
            "operation": self.current_operation
        }
        
        self.logger.debug(f"Progress: {message} ({percentage:.1f}%)", extra=progress_data)
        
        if callback:
            try:
                callback(progress_data)
            except Exception as e:
                self.logger.warning(f"Progress callback failed: {e}")
    
    def _get_elapsed_time(self) -> float:
        """Get elapsed time since operation start.
        
        Returns:
            Elapsed time in seconds
        """
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0.0
    
    def _log_final_performance_report(self) -> None:
        """Log final performance and monitoring reports."""
        if not self.performance_monitor:
            return
        
        try:
            # Performance summary
            summary = self.performance_monitor.get_performance_summary()
            self.logger.performance_metrics(summary)
            
            # Check for alerts
            alerts = self.performance_alerts.check_alerts()
            for alert in alerts:
                self.logger.warning(
                    f"Performance alert: {alert['message']}",
                    extra={
                        "alert_type": alert['type'],
                        "severity": alert['severity'],
                        "alert_data": alert
                    }
                )
            
            # Retry statistics
            retry_stats = self.retry_manager.get_retry_statistics()
            if retry_stats['total_operations'] > 0:
                self.logger.info(
                    "Retry statistics",
                    extra={
                        "event_type": "retry_statistics",
                        **retry_stats
                    }
                )
            
            # Data quality report
            if hasattr(self, 'collection_validator') and self.collection_validator:
                # This would be populated during validation
                pass
            
        except Exception as e:
            self.logger.error_with_context("Failed to generate performance report", e)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scraper status.
        
        Returns:
            Status dictionary
        """
        status = {
            "is_running": self.is_running,
            "current_operation": self.current_operation,
            "elapsed_time": self._get_elapsed_time(),
            "config": {
                "max_properties": self.config.max_properties,
                "behavior_mode": self.config.behavior_mode,
                "retry_strategy": self.config.retry_strategy,
                "enable_validation": self.config.enable_validation
            }
        }
        
        if self.performance_monitor:
            status["performance"] = self.performance_monitor.get_performance_summary()
        
        if self.retry_manager:
            status["retry_stats"] = self.retry_manager.get_retry_statistics()
        
        return status
    
    def stop(self) -> None:
        """Stop the scraper gracefully."""
        self.logger.info("Stopping scraper...")
        self.is_running = False
        
        if self.performance_monitor:
            self.performance_monitor.stop_monitoring()
        
        self.driver_manager.close()
    
def scrape_properties_quick(max_properties: int = 10, max_typologies: Optional[int] = None) -> PropertyCollection:
    """Quick scraping with default extreme mode.
    
    Args:
        max_properties: Maximum properties to scrape
        max_typologies: Maximum number of typologies/buildings to scrape from
        
    Returns:
        PropertyCollection
    """
    config = ScrapingConfig(
        max_properties=max_properties,
        max_typologies=max_typologies,
        # Uses defaults: behavior_mode="extreme", no human_like_behavior
        enable_detail_page_extraction=False
    )
    
    with ScraperManager(config) as manager:
        return manager.scrape_properties(base_url="https://www.assetplan.cl/arriendo/departamento")


def scrape_properties_comprehensive(max_properties: int = 50) -> PropertyCollection:
    """Comprehensive scraping with human-like behavior, validation and monitoring.
    
    Args:
        max_properties: Maximum properties to scrape
        
    Returns:
        PropertyCollection
    """
    config = ScrapingConfig(
        max_properties=max_properties,
        behavior_mode="normal",  # Slower, more conservative
        retry_strategy="standard",
        circuit_breaker_mode="standard",
        enable_detail_page_extraction=True,
        enable_validation=True,
        enable_performance_monitoring=True,
        human_like_behavior=True  # Enable human simulation
    )
    
    with ScraperManager(config) as manager:
        return manager.scrape_properties(base_url="https://www.assetplan.cl/arriendo/departamento")


# scrape_properties_extreme removed - extreme mode is now the default


def scrape_with_progress(max_properties: int = 25, 
                        progress_callback: Optional[Callable] = None) -> PropertyCollection:
    """Scrape with progress reporting.
    
    Args:
        max_properties: Maximum properties to scrape
        progress_callback: Function to call with progress updates
        
    Returns:
        PropertyCollection
    """
    config = ScrapingConfig(
        max_properties=max_properties,
        behavior_mode="normal",
        enable_performance_monitoring=True
    )
    
    if progress_callback is None:
        def default_progress(data):
            print(f"Progress: {data['message']} ({data['percentage']:.1f}%)")
        progress_callback = default_progress
    
    with ScraperManager(config) as manager:
        return manager.scrape_properties(progress_callback=progress_callback)