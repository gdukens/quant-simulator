"""
Health Check and Readiness Probes for Production Deployment

Provides comprehensive health monitoring endpoints.
"""

import time
import psutil
import requests
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path


class HealthChecker:
    """Comprehensive health checking system."""
    
    def __init__(self):
        """Initialize health checker."""
        self.start_time = time.time()
        self.last_check_time = None
        self.check_history: List[Dict[str, Any]] = []
    
    def check_health(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.
        
        Returns:
            Health status dictionary
        """
        self.last_check_time = datetime.now()
        
        health_checks = {
            'status': 'healthy',
            'timestamp': self.last_check_time.isoformat(),
            'uptime_seconds': int(time.time() - self.start_time),
            'checks': {}
        }
        
        # System resource checks
        health_checks['checks']['system'] = self._check_system_resources()
        
        # Application checks
        health_checks['checks']['application'] = self._check_application()
        
        # Dependencies checks
        health_checks['checks']['dependencies'] = self._check_dependencies()
        
        # Data checks
        health_checks['checks']['data'] = self._check_data_directories()
        
        # Determine overall status
        failed_checks = [
            check_name for check_name, check_result in health_checks['checks'].items()
            if check_result.get('status') != 'healthy'
        ]
        
        if failed_checks:
            health_checks['status'] = 'unhealthy'
            health_checks['failed_checks'] = failed_checks
        
        # Store in history (keep last 100)
        self.check_history.append(health_checks)
        if len(self.check_history) > 100:
            self.check_history.pop(0)
        
        return health_checks
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resources."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Thresholds
            cpu_critical = 90
            memory_critical = 90
            disk_critical = 90
            
            status = 'healthy'
            warnings = []
            
            if cpu_percent > cpu_critical:
                status = 'unhealthy'
                warnings.append(f"CPU usage critical: {cpu_percent:.1f}%")
            elif cpu_percent > 75:
                warnings.append(f"CPU usage high: {cpu_percent:.1f}%")
            
            if memory.percent > memory_critical:
                status = 'unhealthy'
                warnings.append(f"Memory usage critical: {memory.percent:.1f}%")
            elif memory.percent > 75:
                warnings.append(f"Memory usage high: {memory.percent:.1f}%")
            
            if disk.percent > disk_critical:
                status = 'unhealthy'
                warnings.append(f"Disk usage critical: {disk.percent:.1f}%")
            elif disk.percent > 80:
                warnings.append(f"Disk usage high: {disk.percent:.1f}%")
            
            return {
                'status': status,
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'warnings': warnings,
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def _check_application(self) -> Dict[str, Any]:
        """Check application health."""
        try:
            # Check if critical modules can be imported
            import quantlib_pro
            from quantlib_pro.portfolio import PortfolioOptimizer
            from quantlib_pro.risk import RiskCalculator
            
            return {
                'status': 'healthy',
                'modules_loaded': True,
            }
        except ImportError as e:
            return {
                'status': 'unhealthy',
                'error': f"Module import failed: {str(e)}"
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Check external dependencies."""
        dependencies_status = {
            'status': 'healthy',
            'checks': {}
        }
        
        # Check Redis (if configured)
        try:
            import os
            redis_host = os.getenv('REDIS_HOST')
            if redis_host:
                import redis
                r = redis.Redis(host=redis_host, port=6379, socket_connect_timeout=2)
                r.ping()
                dependencies_status['checks']['redis'] = 'connected'
        except Exception as e:
            dependencies_status['checks']['redis'] = f'error: {str(e)}'
            # Redis is optional, don't fail health check
        
        # Check internet connectivity (for market data)
        try:
            response = requests.get('https://www.google.com', timeout=5)
            dependencies_status['checks']['internet'] = 'connected'
        except Exception as e:
            dependencies_status['checks']['internet'] = f'error: {str(e)}'
            dependencies_status['status'] = 'degraded'
        
        return dependencies_status
    
    def _check_data_directories(self) -> Dict[str, Any]:
        """Check data directories."""
        try:
            required_dirs = ['data', 'data/cache', 'data/logs']
            missing_dirs = []
            
            for dir_path in required_dirs:
                if not Path(dir_path).exists():
                    missing_dirs.append(dir_path)
            
            if missing_dirs:
                return {
                    'status': 'unhealthy',
                    'missing_directories': missing_dirs
                }
            
            # Check write permissions
            test_file = Path('data/cache/.health_check_test')
            try:
                test_file.write_text('test')
                test_file.unlink()
                writeable = True
            except Exception:
                writeable = False
            
            return {
                'status': 'healthy' if writeable else 'unhealthy',
                'writeable': writeable,
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_readiness(self) -> Dict[str, Any]:
        """
        Check if application is ready to serve traffic.
        
        Returns:
            Readiness status
        """
        # Application is ready if:
        # 1. System resources are not critical
        # 2. Application modules loaded
        # 3. Required directories exist
        
        health = self.check_health()
        
        ready = (
            health['status'] == 'healthy' and
            health['checks']['application']['status'] == 'healthy'
        )
        
        return {
            'ready': ready,
            'status': 'ready' if ready else 'not_ready',
            'timestamp': datetime.now().isoformat(),
        }
    
    def check_liveness(self) -> Dict[str, Any]:
        """
        Check if application is alive (simpler than health check).
        
        Returns:
            Liveness status
        """
        # Application is alive if it can respond
        return {
            'alive': True,
            'status': 'alive',
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': int(time.time() - self.start_time),
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get health metrics for monitoring.
        
        Returns:
            Metrics dictionary
        """
        if not self.check_history:
            return {}
        
        # Calculate success rate
        total_checks = len(self.check_history)
        healthy_checks = sum(
            1 for check in self.check_history
            if check['status'] == 'healthy'
        )
        success_rate = (healthy_checks / total_checks * 100) if total_checks > 0 else 0
        
        # Get latest resource usage
        latest = self.check_history[-1]
        system_check = latest['checks'].get('system', {})
        
        return {
            'total_checks': total_checks,
            'success_rate': success_rate,
            'uptime_seconds': int(time.time() - self.start_time),
            'last_check': self.last_check_time.isoformat() if self.last_check_time else None,
            'current_cpu_percent': system_check.get('cpu_percent'),
            'current_memory_percent': system_check.get('memory_percent'),
            'current_disk_percent': system_check.get('disk_percent'),
        }


# Global health checker instance
_health_checker = HealthChecker()


def get_health_checker() -> HealthChecker:
    """Get global health checker instance."""
    return _health_checker


# Flask endpoints (if using REST API)
def create_health_endpoints(app):
    """
    Create health check endpoints for Flask app.
    
    Args:
        app: Flask application
    """
    @app.route('/health')
    def health():
        """Full health check endpoint."""
        result = _health_checker.check_health()
        status_code = 200 if result['status'] == 'healthy' else 503
        return result, status_code
    
    @app.route('/health/ready')
    def ready():
        """Readiness probe endpoint."""
        result = _health_checker.check_readiness()
        status_code = 200 if result['ready'] else 503
        return result, status_code
    
    @app.route('/health/live')
    def live():
        """Liveness probe endpoint."""
        result = _health_checker.check_liveness()
        return result, 200
    
    @app.route('/metrics')
    def metrics():
        """Metrics endpoint for Prometheus."""
        metrics_data = _health_checker.get_metrics()
        
        # Convert to Prometheus format
        lines = [
            '# HELP quantlib_health_checks_total Total number of health checks',
            '# TYPE quantlib_health_checks_total counter',
            f'quantlib_health_checks_total {metrics_data.get("total_checks", 0)}',
            '',
            '# HELP quantlib_health_success_rate Health check success rate',
            '# TYPE quantlib_health_success_rate gauge',
            f'quantlib_health_success_rate {metrics_data.get("success_rate", 0)}',
            '',
            '# HELP quantlib_uptime_seconds Application uptime in seconds',
            '# TYPE quantlib_uptime_seconds counter',
            f'quantlib_uptime_seconds {metrics_data.get("uptime_seconds", 0)}',
            '',
            '# HELP quantlib_cpu_percent CPU usage percentage',
            '# TYPE quantlib_cpu_percent gauge',
            f'quantlib_cpu_percent {metrics_data.get("current_cpu_percent", 0)}',
            '',
            '# HELP quantlib_memory_percent Memory usage percentage',
            '# TYPE quantlib_memory_percent gauge',
            f'quantlib_memory_percent {metrics_data.get("current_memory_percent", 0)}',
            '',
            '# HELP quantlib_disk_percent Disk usage percentage',
            '# TYPE quantlib_disk_percent gauge',
            f'quantlib_disk_percent {metrics_data.get("current_disk_percent", 0)}',
        ]
        
        return '\n'.join(lines), 200, {'Content-Type': 'text/plain; charset=utf-8'}


# Streamlit health check (simpler version)
def streamlit_health_check() -> bool:
    """
    Simple health check for Streamlit.
    
    Returns:
        True if healthy, False otherwise
    """
    try:
        checker = get_health_checker()
        result = checker.check_health()
        return result['status'] == 'healthy'
    except Exception:
        return False
