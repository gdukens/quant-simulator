"""
User Acceptance Testing (UAT) Module

Infrastructure for UAT including scenarios, feedback, bug tracking, and performance validation.
"""

from .scenarios import (
    UATScenario,
    UATScenarioLibrary,
    UATExecutor,
    UserRole,
    TestStatus,
    Priority,
    TestStep,
)

from .feedback import (
    Feedback,
    FeedbackCollector,
    FeedbackAnalyzer,
    FeedbackType,
    Severity,
    FeedbackStatus,
)

from .bug_tracker import (
    Bug,
    BugTracker,
    BugPriority,
    BugCategory,
)

from .performance_validation import (
    PerformanceValidator,
    PerformanceBenchmark,
    PerformanceResult,
    PerformanceStatus,
)

__all__ = [
    # Scenarios
    'UATScenario',
    'UATScenarioLibrary',
    'UATExecutor',
    'UserRole',
    'TestStatus',
    'Priority',
    'TestStep',
    
    # Feedback
    'Feedback',
    'FeedbackCollector',
    'FeedbackAnalyzer',
    'FeedbackType',
    'Severity',
    'FeedbackStatus',
    
    # Bug Tracking
    'Bug',
    'BugTracker',
    'BugPriority',
    'BugCategory',
    
    # Performance
    'PerformanceValidator',
    'PerformanceBenchmark',
    'PerformanceResult',
    'PerformanceStatus',
]
