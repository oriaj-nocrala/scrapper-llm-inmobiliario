"""
Performance Monitor for tracking scraping metrics and system health.
"""
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


@dataclass
class ScrapingMetrics:
    """Metrics for scraping operations."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_properties_scraped: int = 0
    average_response_time: float = 0.0
    error_rate: float = 0.0
    throughput: float = 0.0  # properties per minute
    start_time: datetime = field(default_factory=datetime.now)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def elapsed_time(self) -> timedelta:
        """Get elapsed time since start."""
        return datetime.now() - self.start_time


@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    disk_usage_percent: float = 0.0
    network_sent_mb: float = 0.0
    network_received_mb: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class PerformanceMonitor:
    """Monitor scraping performance and system resources."""
    
    def __init__(self, monitoring_interval: int = 5):
        """Initialize the performance monitor.
        
        Args:
            monitoring_interval: Interval in seconds for system monitoring
        """
        self.monitoring_interval = monitoring_interval
        self.scraping_metrics = ScrapingMetrics()
        self.system_metrics_history: deque = deque(maxlen=100)  # Keep last 100 measurements
        self.error_history: deque = deque(maxlen=50)  # Keep last 50 errors
        self.response_times: deque = deque(maxlen=100)  # Keep last 100 response times
        self.property_timestamps: List[datetime] = []
        self.error_counts: Dict[str, int] = defaultdict(int)
        
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
    def start_monitoring(self) -> None:
        """Start background system monitoring."""
        if not self._monitoring:
            self._monitoring = True
            self._monitor_thread = threading.Thread(target=self._monitor_system, daemon=True)
            self._monitor_thread.start()
            logger.info("Performance monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)
        logger.info("Performance monitoring stopped")
    
    def _monitor_system(self) -> None:
        """Background thread function for monitoring system resources."""
        while self._monitoring:
            try:
                metrics = self._collect_system_metrics()
                with self._lock:
                    self.system_metrics_history.append(metrics)
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                time.sleep(self.monitoring_interval)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # Network usage
            network = psutil.net_io_counters()
            network_sent_mb = network.bytes_sent / (1024 * 1024)
            network_received_mb = network.bytes_recv / (1024 * 1024)
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                disk_usage_percent=disk_usage_percent,
                network_sent_mb=network_sent_mb,
                network_received_mb=network_received_mb
            )
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
            return SystemMetrics()
    
    def record_request_start(self) -> str:
        """Record the start of a request.
        
        Returns:
            Request ID for tracking
        """
        request_id = f"req_{int(time.time() * 1000)}"
        with self._lock:
            self.scraping_metrics.total_requests += 1
        return request_id
    
    def record_request_success(self, request_id: str, response_time: float) -> None:
        """Record a successful request.
        
        Args:
            request_id: Request identifier
            response_time: Response time in seconds
        """
        with self._lock:
            self.scraping_metrics.successful_requests += 1
            self.response_times.append(response_time)
            self._update_average_response_time()
            self._update_error_rate()
    
    def record_request_failure(self, request_id: str, error_type: str, error_message: str) -> None:
        """Record a failed request.
        
        Args:
            request_id: Request identifier
            error_type: Type of error
            error_message: Error message
        """
        with self._lock:
            self.scraping_metrics.failed_requests += 1
            self.error_counts[error_type] += 1
            
            # Record error details
            error_record = {
                'timestamp': datetime.now(),
                'request_id': request_id,
                'error_type': error_type,
                'error_message': error_message
            }
            self.error_history.append(error_record)
            
            self._update_error_rate()
    
    def record_property_scraped(self) -> None:
        """Record that a property was successfully scraped."""
        with self._lock:
            self.scraping_metrics.total_properties_scraped += 1
            self.property_timestamps.append(datetime.now())
            self._update_throughput()
    
    def _update_average_response_time(self) -> None:
        """Update average response time."""
        if self.response_times:
            self.scraping_metrics.average_response_time = sum(self.response_times) / len(self.response_times)
    
    def _update_error_rate(self) -> None:
        """Update error rate."""
        if self.scraping_metrics.total_requests > 0:
            self.scraping_metrics.error_rate = (
                self.scraping_metrics.failed_requests / self.scraping_metrics.total_requests
            ) * 100
    
    def _update_throughput(self) -> None:
        """Update throughput (properties per minute)."""
        if not self.property_timestamps:
            return
        
        # Calculate throughput based on last 10 minutes
        cutoff_time = datetime.now() - timedelta(minutes=10)
        recent_properties = [ts for ts in self.property_timestamps if ts > cutoff_time]
        
        if len(recent_properties) > 1:
            time_span = (recent_properties[-1] - recent_properties[0]).total_seconds() / 60
            if time_span > 0:
                self.scraping_metrics.throughput = len(recent_properties) / time_span
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a comprehensive performance summary.
        
        Returns:
            Dictionary with performance metrics
        """
        with self._lock:
            current_system_metrics = self._collect_system_metrics()
            
            # Get recent error breakdown
            recent_errors = defaultdict(int)
            cutoff_time = datetime.now() - timedelta(minutes=30)
            for error in self.error_history:
                if error['timestamp'] > cutoff_time:
                    recent_errors[error['error_type']] += 1
            
            return {
                'scraping_metrics': {
                    'total_requests': self.scraping_metrics.total_requests,
                    'successful_requests': self.scraping_metrics.successful_requests,
                    'failed_requests': self.scraping_metrics.failed_requests,
                    'success_rate': round(self.scraping_metrics.success_rate, 2),
                    'error_rate': round(self.scraping_metrics.error_rate, 2),
                    'total_properties_scraped': self.scraping_metrics.total_properties_scraped,
                    'average_response_time': round(self.scraping_metrics.average_response_time, 3),
                    'throughput_per_minute': round(self.scraping_metrics.throughput, 2),
                    'elapsed_time': str(self.scraping_metrics.elapsed_time).split('.')[0]
                },
                'system_metrics': {
                    'cpu_percent': round(current_system_metrics.cpu_percent, 1),
                    'memory_percent': round(current_system_metrics.memory_percent, 1),
                    'memory_used_mb': round(current_system_metrics.memory_used_mb, 1),
                    'disk_usage_percent': round(current_system_metrics.disk_usage_percent, 1)
                },
                'error_breakdown': dict(recent_errors),
                'health_status': self._get_health_status()
            }
    
    def _get_health_status(self) -> str:
        """Determine overall health status.
        
        Returns:
            Health status string
        """
        # Check error rate
        if self.scraping_metrics.error_rate > 50:
            return "CRITICAL"
        elif self.scraping_metrics.error_rate > 25:
            return "WARNING"
        
        # Check system resources
        if self.system_metrics_history:
            latest_system = self.system_metrics_history[-1]
            if latest_system.memory_percent > 90 or latest_system.cpu_percent > 90:
                return "WARNING"
        
        # Check throughput
        if self.scraping_metrics.throughput < 1 and self.scraping_metrics.total_requests > 10:
            return "WARNING"
        
        return "HEALTHY"
    
    def get_error_analysis(self) -> Dict[str, Any]:
        """Get detailed error analysis.
        
        Returns:
            Error analysis data
        """
        with self._lock:
            total_errors = sum(self.error_counts.values())
            
            if total_errors == 0:
                return {'total_errors': 0, 'error_breakdown': {}, 'recent_errors': []}
            
            # Error breakdown by percentage
            error_breakdown = {
                error_type: {
                    'count': count,
                    'percentage': round((count / total_errors) * 100, 2)
                }
                for error_type, count in self.error_counts.items()
            }
            
            # Recent errors (last 10)
            recent_errors = list(self.error_history)[-10:]
            
            return {
                'total_errors': total_errors,
                'error_breakdown': error_breakdown,
                'recent_errors': [
                    {
                        'timestamp': error['timestamp'].isoformat(),
                        'error_type': error['error_type'],
                        'error_message': error['error_message'][:100]  # Truncate long messages
                    }
                    for error in recent_errors
                ]
            }
    
    def log_performance_summary(self) -> None:
        """Log a performance summary."""
        summary = self.get_performance_summary()
        
        logger.info(
            f"Performance Summary - "
            f"Properties: {summary['scraping_metrics']['total_properties_scraped']}, "
            f"Success Rate: {summary['scraping_metrics']['success_rate']}%, "
            f"Throughput: {summary['scraping_metrics']['throughput_per_minute']}/min, "
            f"Avg Response: {summary['scraping_metrics']['average_response_time']}s, "
            f"Health: {summary['health_status']}"
        )
    
    def is_performance_degraded(self) -> bool:
        """Check if performance is significantly degraded.
        
        Returns:
            True if performance is degraded
        """
        # Check error rate
        if self.scraping_metrics.error_rate > 30:
            return True
        
        # Check response time
        if self.scraping_metrics.average_response_time > 10:
            return True
        
        # Check throughput
        if (self.scraping_metrics.throughput < 2 and 
            self.scraping_metrics.total_requests > 20):
            return True
        
        return False
    
    def reset_metrics(self) -> None:
        """Reset all metrics to start fresh."""
        with self._lock:
            self.scraping_metrics = ScrapingMetrics()
            self.system_metrics_history.clear()
            self.error_history.clear()
            self.response_times.clear()
            self.property_timestamps.clear()
            self.error_counts.clear()
        
        logger.info("Performance metrics reset")
    
class PerformanceAlerts:
    """Performance alerting system."""
    
    def __init__(self, monitor: PerformanceMonitor):
        """Initialize alerting system.
        
        Args:
            monitor: PerformanceMonitor instance
        """
        self.monitor = monitor
        self.alert_history = []
        
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for performance alerts.
        
        Returns:
            List of active alerts
        """
        alerts = []
        summary = self.monitor.get_performance_summary()
        
        # High error rate alert
        if summary['scraping_metrics']['error_rate'] > 25:
            alerts.append({
                'type': 'HIGH_ERROR_RATE',
                'severity': 'WARNING' if summary['scraping_metrics']['error_rate'] < 50 else 'CRITICAL',
                'message': f"Error rate is {summary['scraping_metrics']['error_rate']}%",
                'timestamp': datetime.now()
            })
        
        # Low throughput alert
        if (summary['scraping_metrics']['throughput_per_minute'] < 1 and 
            summary['scraping_metrics']['total_requests'] > 10):
            alerts.append({
                'type': 'LOW_THROUGHPUT',
                'severity': 'WARNING',
                'message': f"Throughput is {summary['scraping_metrics']['throughput_per_minute']} properties/min",
                'timestamp': datetime.now()
            })
        
        # High resource usage alert
        if summary['system_metrics']['memory_percent'] > 85:
            alerts.append({
                'type': 'HIGH_MEMORY_USAGE',
                'severity': 'WARNING' if summary['system_metrics']['memory_percent'] < 95 else 'CRITICAL',
                'message': f"Memory usage is {summary['system_metrics']['memory_percent']}%",
                'timestamp': datetime.now()
            })
        
        # Slow response time alert
        if summary['scraping_metrics']['average_response_time'] > 5:
            alerts.append({
                'type': 'SLOW_RESPONSE_TIME',
                'severity': 'WARNING',
                'message': f"Average response time is {summary['scraping_metrics']['average_response_time']}s",
                'timestamp': datetime.now()
            })
        
        return alerts