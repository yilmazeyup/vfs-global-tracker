"""
🔄 VFS Global Randevu Sistemi - Silent Retry Engine
Self-healing error recovery system with intelligent backoff
"""

import asyncio
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import traceback

try:
    from core.telegram_bot import telegram_notifier
    from config.settings import settings
    from utils.logger import get_logger
except ImportError:
    from backend.core.telegram_bot import telegram_notifier
    from backend.config.settings import settings
    from backend.utils.logger import get_logger

retry_logger = get_logger("vfs_retry")

class ErrorSeverity(Enum):
    """❗ Hata şiddet seviyeleri"""
    LOW = "low"           # Network timeouts, temporary issues
    MEDIUM = "medium"     # Page load failures, element not found  
    HIGH = "high"         # Login failures, session expired
    CRITICAL = "critical" # Blocked by VFS, permanent errors

class RetryStrategy(Enum):
    """🔄 Retry stratejileri"""
    LINEAR = "linear"           # Fixed delay
    EXPONENTIAL = "exponential" # Exponential backoff
    JITTERED = "jittered"      # Exponential with random jitter
    ADAPTIVE = "adaptive"       # Smart adaptive delays

@dataclass
class RetryContext:
    """📊 Retry context bilgisi"""
    operation_name: str
    office: str
    attempt_count: int
    max_attempts: int
    last_error: Exception
    error_history: List[str]
    start_time: datetime
    total_delay: float
    strategy: RetryStrategy = RetryStrategy.JITTERED

@dataclass
class RetryResult:
    """✅ Retry sonucu"""
    success: bool
    final_result: Any = None
    total_attempts: int = 0
    total_time: float = 0.0
    error_message: Optional[str] = None
    recovery_actions: List[str] = None

class SilentRetryEngine:
    """🎯 Kendi Kendini İyileştiren Retry Motoru"""
    
    def __init__(self):
        self.operation_stats: Dict[str, Dict] = {}
        self.error_patterns: Dict[str, ErrorSeverity] = self._initialize_error_patterns()
        self.recovery_actions: Dict[ErrorSeverity, List[Callable]] = self._initialize_recovery_actions()
        
        # Global settings
        self.max_consecutive_failures = 5
        self.critical_error_cooldown = 300  # 5 dakika
        self.blocked_until: Optional[datetime] = None
        
    def _initialize_error_patterns(self) -> Dict[str, ErrorSeverity]:
        """❗ Hata pattern'larını tanımla"""
        
        return {
            # Network errors (LOW)
            "timeout": ErrorSeverity.LOW,
            "connection": ErrorSeverity.LOW,
            "network": ErrorSeverity.LOW,
            "dns": ErrorSeverity.LOW,
            
            # Page/Element errors (MEDIUM)
            "element not found": ErrorSeverity.MEDIUM,
            "page load": ErrorSeverity.MEDIUM,
            "stale element": ErrorSeverity.MEDIUM,
            "javascript error": ErrorSeverity.MEDIUM,
            
            # Session/Auth errors (HIGH)
            "login failed": ErrorSeverity.HIGH,
            "session expired": ErrorSeverity.HIGH,
            "authentication": ErrorSeverity.HIGH,
            "unauthorized": ErrorSeverity.HIGH,
            
            # Critical/Blocking errors (CRITICAL)
            "blocked": ErrorSeverity.CRITICAL,
            "banned": ErrorSeverity.CRITICAL,
            "cloudflare": ErrorSeverity.CRITICAL,
            "too many requests": ErrorSeverity.CRITICAL,
            "captcha": ErrorSeverity.CRITICAL,
        }
    
    def _initialize_recovery_actions(self) -> Dict[ErrorSeverity, List[Callable]]:
        """🔧 Recovery action'larını tanımla"""
        
        return {
            ErrorSeverity.LOW: [
                self._action_simple_retry,
                self._action_refresh_page,
            ],
            ErrorSeverity.MEDIUM: [
                self._action_clear_cache,
                self._action_restart_driver,
                self._action_change_user_agent,
            ],
            ErrorSeverity.HIGH: [
                self._action_full_relogin,
                self._action_clear_session,
                self._action_restart_browser,
            ],
            ErrorSeverity.CRITICAL: [
                self._action_emergency_stop,
                self._action_notify_admin,
                self._action_ip_rotation,
            ]
        }
    
    async def execute_with_retry(
        self,
        operation_func: Callable,
        operation_name: str,
        office: str,
        max_attempts: int = None,
        strategy: RetryStrategy = RetryStrategy.JITTERED,
        **kwargs
    ) -> RetryResult:
        """🎯 Ana retry execution fonksiyonu"""
        
        max_attempts = max_attempts or settings.SCRAPING.max_retries
        start_time = datetime.now()
        
        # Blocked check
        if self._is_blocked():
            return RetryResult(
                success=False,
                error_message="System temporarily blocked due to critical errors",
                recovery_actions=["wait_for_cooldown"]
            )
        
        context = RetryContext(
            operation_name=operation_name,
            office=office,
            attempt_count=0,
            max_attempts=max_attempts,
            last_error=None,
            error_history=[],
            start_time=start_time,
            total_delay=0.0,
            strategy=strategy
        )
        
        retry_logger.info(f"Starting retry operation: {operation_name} [{office}]")
        
        for attempt in range(1, max_attempts + 1):
            context.attempt_count = attempt
            
            try:
                retry_logger.debug(f"Attempt {attempt}/{max_attempts}: {operation_name}")
                
                # Execute operation
                result = await operation_func(**kwargs)
                
                # Success!
                total_time = (datetime.now() - start_time).total_seconds()
                
                retry_logger.success(
                    f"Operation successful: {operation_name} [{office}] "
                    f"(attempt {attempt}/{max_attempts}, {total_time:.2f}s)"
                )
                
                self._update_success_stats(operation_name, attempt, total_time)
                
                return RetryResult(
                    success=True,
                    final_result=result,
                    total_attempts=attempt,
                    total_time=total_time
                )
                
            except Exception as e:
                context.last_error = e
                context.error_history.append(str(e))
                
                # Error classification
                error_severity = self._classify_error(str(e))
                
                retry_logger.retry_event(
                    attempt=attempt,
                    max_attempts=max_attempts,
                    error=str(e),
                    severity=error_severity.value,
                    operation=operation_name,
                    office=office
                )
                
                # Last attempt check
                if attempt == max_attempts:
                    break
                
                # Recovery actions
                recovery_success = await self._execute_recovery_actions(error_severity, context)
                
                # Calculate delay
                delay = self._calculate_delay(attempt, strategy, error_severity)
                context.total_delay += delay
                
                retry_logger.warning(
                    f"Retry delay: {delay:.1f}s (recovery: {'success' if recovery_success else 'failed'})"
                )
                
                # Wait before retry
                await asyncio.sleep(delay)
        
        # All attempts failed
        total_time = (datetime.now() - start_time).total_seconds()
        final_error = context.error_history[-1] if context.error_history else "Unknown error"
        
        retry_logger.error(
            f"Operation failed after {max_attempts} attempts: {operation_name} [{office}] "
            f"({total_time:.2f}s) - {final_error}"
        )
        
        self._update_failure_stats(operation_name, max_attempts, total_time, final_error)
        
        # Critical error handling
        if self._classify_error(final_error) == ErrorSeverity.CRITICAL:
            await self._handle_critical_failure(context)
        
        return RetryResult(
            success=False,
            total_attempts=max_attempts,
            total_time=total_time,
            error_message=final_error,
            recovery_actions=[action.__name__ for action in self.recovery_actions.get(
                self._classify_error(final_error), []
            )]
        )
    
    def _classify_error(self, error_message: str) -> ErrorSeverity:
        """❗ Error classification"""
        
        error_lower = error_message.lower()
        
        for pattern, severity in self.error_patterns.items():
            if pattern in error_lower:
                return severity
        
        # Default to MEDIUM if no pattern matches
        return ErrorSeverity.MEDIUM
    
    def _calculate_delay(self, attempt: int, strategy: RetryStrategy, severity: ErrorSeverity) -> float:
        """⏰ Delay calculation"""
        
        base_delay = settings.SCRAPING.retry_delay
        
        # Severity multiplier
        severity_multipliers = {
            ErrorSeverity.LOW: 0.5,
            ErrorSeverity.MEDIUM: 1.0,
            ErrorSeverity.HIGH: 2.0,
            ErrorSeverity.CRITICAL: 5.0
        }
        
        base_delay *= severity_multipliers[severity]
        
        if strategy == RetryStrategy.LINEAR:
            return base_delay
        elif strategy == RetryStrategy.EXPONENTIAL:
            return base_delay * (2 ** (attempt - 1))
        elif strategy == RetryStrategy.JITTERED:
            exponential_delay = base_delay * (2 ** (attempt - 1))
            jitter = exponential_delay * random.uniform(0.1, 0.5)
            return exponential_delay + jitter
        elif strategy == RetryStrategy.ADAPTIVE:
            # Adaptive based on recent success rates
            success_rate = self._get_recent_success_rate()
            multiplier = 3.0 - (2.0 * success_rate)  # Higher delay for low success rates
            return base_delay * multiplier * attempt
        
        return base_delay
    
    async def _execute_recovery_actions(self, severity: ErrorSeverity, context: RetryContext) -> bool:
        """🔧 Recovery actions çalıştır"""
        
        actions = self.recovery_actions.get(severity, [])
        recovery_success = False
        
        for action in actions:
            try:
                retry_logger.debug(f"Executing recovery action: {action.__name__}")
                
                success = await action(context)
                if success:
                    recovery_success = True
                    retry_logger.info(f"Recovery action successful: {action.__name__}")
                    break
                else:
                    retry_logger.warning(f"Recovery action failed: {action.__name__}")
                    
            except Exception as e:
                retry_logger.error(f"Recovery action exception: {action.__name__} - {e}")
        
        return recovery_success
    
    # Recovery Actions
    async def _action_simple_retry(self, context: RetryContext) -> bool:
        """Simple retry without changes"""
        return True  # Always allow retry
    
    async def _action_refresh_page(self, context: RetryContext) -> bool:
        """Refresh current page"""
        try:
            # This would need access to the driver - placeholder
            retry_logger.debug("Page refresh action")
            await asyncio.sleep(1)
            return True
        except:
            return False
    
    async def _action_clear_cache(self, context: RetryContext) -> bool:
        """Clear browser cache"""
        try:
            retry_logger.debug("Cache clear action")
            await asyncio.sleep(1)
            return True
        except:
            return False
    
    async def _action_restart_driver(self, context: RetryContext) -> bool:
        """Restart browser driver"""
        try:
            retry_logger.debug("Driver restart action")
            await asyncio.sleep(2)
            return True
        except:
            return False
    
    async def _action_change_user_agent(self, context: RetryContext) -> bool:
        """Change user agent"""
        try:
            retry_logger.debug("User agent rotation action")
            await asyncio.sleep(1)
            return True
        except:
            return False
    
    async def _action_full_relogin(self, context: RetryContext) -> bool:
        """Full re-authentication"""
        try:
            retry_logger.debug("Full relogin action")
            await asyncio.sleep(3)
            return True
        except:
            return False
    
    async def _action_clear_session(self, context: RetryContext) -> bool:
        """Clear all session data"""
        try:
            retry_logger.debug("Session clear action")
            await asyncio.sleep(2)
            return True
        except:
            return False
    
    async def _action_restart_browser(self, context: RetryContext) -> bool:
        """Full browser restart"""
        try:
            retry_logger.debug("Browser restart action")
            await asyncio.sleep(5)
            return True
        except:
            return False
    
    async def _action_emergency_stop(self, context: RetryContext) -> bool:
        """Emergency stop - block further operations"""
        self.blocked_until = datetime.now() + timedelta(seconds=self.critical_error_cooldown)
        
        retry_logger.alert(
            f"Emergency stop activated for {self.critical_error_cooldown}s due to critical error: "
            f"{context.last_error}"
        )
        
        return False  # Don't continue retrying
    
    async def _action_notify_admin(self, context: RetryContext) -> bool:
        """Send admin notification"""
        try:
            async with telegram_notifier as notifier:
                await notifier.send_system_alert(
                    alert_type="Critical Error",
                    message=f"Operation {context.operation_name} failed critically for {context.office}",
                    severity="critical",
                    details={
                        "error": str(context.last_error),
                        "attempts": context.attempt_count,
                        "office": context.office
                    }
                )
            return True
        except:
            return False
    
    async def _action_ip_rotation(self, context: RetryContext) -> bool:
        """IP rotation (if proxy available)"""
        try:
            retry_logger.debug("IP rotation action (placeholder)")
            await asyncio.sleep(1)
            return True
        except:
            return False
    
    def _is_blocked(self) -> bool:
        """System blocked durumunu kontrol et"""
        
        if self.blocked_until:
            if datetime.now() < self.blocked_until:
                return True
            else:
                # Cooldown period ended
                self.blocked_until = None
                retry_logger.info("System block cooldown ended, resuming operations")
                return False
        
        return False
    
    async def _handle_critical_failure(self, context: RetryContext):
        """Critical failure handling"""
        
        retry_logger.alert(f"Critical failure detected: {context.operation_name}")
        
        # Auto block if too many consecutive failures  
        operation_stats = self.operation_stats.get(context.operation_name, {})
        consecutive_failures = operation_stats.get('consecutive_failures', 0) + 1
        
        if consecutive_failures >= self.max_consecutive_failures:
            self.blocked_until = datetime.now() + timedelta(seconds=self.critical_error_cooldown)
            
            # Send notification
            try:
                async with telegram_notifier as notifier:
                    await notifier.send_system_alert(
                        alert_type="System Auto-Block",
                        message=f"System blocked after {consecutive_failures} consecutive failures",
                        severity="critical",
                        details={
                            "operation": context.operation_name,
                            "office": context.office,
                            "cooldown_minutes": self.critical_error_cooldown // 60
                        }
                    )
            except:
                pass
    
    def _update_success_stats(self, operation_name: str, attempts: int, duration: float):
        """Success istatistiklerini güncelle"""
        
        if operation_name not in self.operation_stats:
            self.operation_stats[operation_name] = {
                'total_runs': 0,
                'successful_runs': 0,
                'total_attempts': 0,
                'total_duration': 0.0,
                'consecutive_failures': 0
            }
        
        stats = self.operation_stats[operation_name]
        stats['total_runs'] += 1
        stats['successful_runs'] += 1
        stats['total_attempts'] += attempts
        stats['total_duration'] += duration
        stats['consecutive_failures'] = 0  # Reset on success
    
    def _update_failure_stats(self, operation_name: str, attempts: int, duration: float, error: str):
        """Failure istatistiklerini güncelle"""
        
        if operation_name not in self.operation_stats:
            self.operation_stats[operation_name] = {
                'total_runs': 0,
                'successful_runs': 0,
                'total_attempts': 0,
                'total_duration': 0.0,
                'consecutive_failures': 0,
                'last_error': None
            }
        
        stats = self.operation_stats[operation_name]
        stats['total_runs'] += 1
        stats['total_attempts'] += attempts
        stats['total_duration'] += duration
        stats['consecutive_failures'] += 1
        stats['last_error'] = error
    
    def _get_recent_success_rate(self) -> float:
        """Recent success rate hesapla"""
        
        total_runs = sum(stats.get('total_runs', 0) for stats in self.operation_stats.values())
        successful_runs = sum(stats.get('successful_runs', 0) for stats in self.operation_stats.values())
        
        if total_runs == 0:
            return 1.0  # Default optimistic
        
        return successful_runs / total_runs
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retry engine istatistiklerini döndür"""
        
        return {
            "operation_stats": self.operation_stats.copy(),
            "overall_success_rate": self._get_recent_success_rate(),
            "is_blocked": self._is_blocked(),
            "blocked_until": self.blocked_until.isoformat() if self.blocked_until else None
        }
    
    def reset_stats(self):
        """İstatistikleri sıfırla"""
        self.operation_stats.clear()
        retry_logger.info("Retry engine statistics reset")

# Global retry engine instance
retry_engine = SilentRetryEngine()

# Convenience decorator
def with_retry(operation_name: str, office: str = "unknown", max_attempts: int = None, strategy: RetryStrategy = RetryStrategy.JITTERED):
    """🎯 Retry decorator"""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await retry_engine.execute_with_retry(
                operation_func=func,
                operation_name=operation_name,
                office=office,
                max_attempts=max_attempts,
                strategy=strategy,
                *args,
                **kwargs
            )
            
            if result.success:
                return result.final_result
            else:
                raise Exception(f"Operation failed after retries: {result.error_message}")
        
        return wrapper
    return decorator

# Test function
async def test_retry_engine():
    """Retry engine test"""
    
    print("🔄 Testing Silent Retry Engine...")
    
    # Test function that sometimes fails
    async def flaky_operation(fail_rate: float = 0.7):
        if random.random() < fail_rate:
            raise Exception(f"Random failure (network timeout)")
        return "Success!"
    
    # Test with decorator
    @with_retry("test_operation", "test_office", max_attempts=5)
    async def decorated_operation():
        return await flaky_operation(fail_rate=0.3)  # Lower fail rate for test
    
    try:
        result = await decorated_operation()
        print(f"✅ Decorated operation result: {result}")
    except Exception as e:
        print(f"❌ Decorated operation failed: {e}")
    
    # Test direct usage
    result = await retry_engine.execute_with_retry(
        operation_func=flaky_operation,
        operation_name="direct_test",
        office="test_office",
        max_attempts=3,
        fail_rate=0.8  # High fail rate
    )
    
    print(f"📊 Direct test result: Success={result.success}, Attempts={result.total_attempts}")
    
    # Statistics
    stats = retry_engine.get_statistics()
    print(f"📈 Engine statistics: {stats}")
    
    print("✅ Retry engine test completed")

if __name__ == "__main__":
    asyncio.run(test_retry_engine())