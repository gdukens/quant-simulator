"""
UAT Bug Tracking System

Specialized bug tracking with detailed lifecycle management.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import json
from .feedback import Feedback, FeedbackType, Severity, FeedbackStatus


class BugPriority(Enum):
    """Bug priority levels."""
    P0 = "p0"  # Critical, system down
    P1 = "p1"  # High, major functionality broken
    P2 = "p2"  # Medium, some functionality affected
    P3 = "p3"  # Low, minor issue
    P4 = "p4"  # Trivial, cosmetic


class BugCategory(Enum):
    """Bug categories."""
    CRASH = "crash"
    DATA_CORRUPTION = "data_corruption"
    CALCULATION_ERROR = "calculation_error"
    UI_BUG = "ui_bug"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"
    SECURITY = "security"
    USABILITY = "usability"


@dataclass
class Bug:
    """Bug tracking record."""
    bug_id: str
    title: str
    description: str
    category: BugCategory
    priority: BugPriority
    severity: Severity
    status: FeedbackStatus
    reporter: str
    reported_date: datetime
    
    # Bug details
    steps_to_reproduce: List[str]
    expected_behavior: str
    actual_behavior: str
    page: str
    browser: str
    environment: str = "UAT"
    
    # Tracking
    assignee: Optional[str] = None
    assigned_date: Optional[datetime] = None
    resolution_date: Optional[datetime] = None
    resolution: str = ""
    root_cause: str = ""
    fix_description: str = ""
    
    # Related
    related_bugs: List[str] = field(default_factory=list)
    duplicate_of: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def time_to_assign_hours(self) -> Optional[float]:
        """Time from report to assignment in hours."""
        if self.assigned_date:
            delta = self.assigned_date - self.reported_date
            return delta.total_seconds() / 3600
        return None
    
    @property
    def time_to_resolve_hours(self) -> Optional[float]:
        """Time from report to resolution in hours."""
        if self.resolution_date:
            delta = self.resolution_date - self.reported_date
            return delta.total_seconds() / 3600
        return None
    
    @property
    def is_open(self) -> bool:
        """Check if bug is still open."""
        return self.status not in [FeedbackStatus.RESOLVED, FeedbackStatus.WONT_FIX]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'bug_id': self.bug_id,
            'title': self.title,
            'description': self.description,
            'category': self.category.value,
            'priority': self.priority.value,
            'severity': self.severity.value,
            'status': self.status.value,
            'reporter': self.reporter,
            'reported_date': self.reported_date.isoformat(),
            'steps_to_reproduce': self.steps_to_reproduce,
            'expected_behavior': self.expected_behavior,
            'actual_behavior': self.actual_behavior,
            'page': self.page,
            'browser': self.browser,
            'environment': self.environment,
            'assignee': self.assignee,
            'assigned_date': self.assigned_date.isoformat() if self.assigned_date else None,
            'resolution_date': self.resolution_date.isoformat() if self.resolution_date else None,
            'resolution': self.resolution,
            'root_cause': self.root_cause,
            'fix_description': self.fix_description,
            'related_bugs': self.related_bugs,
            'duplicate_of': self.duplicate_of,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'time_to_assign_hours': self.time_to_assign_hours,
            'time_to_resolve_hours': self.time_to_resolve_hours,
        }
    
    @classmethod
    def from_feedback(cls, feedback: Feedback) -> 'Bug':
        """Create bug from feedback item."""
        # Infer category from description/tags
        category = BugCategory.UI_BUG  # Default
        
        if any(word in feedback.description.lower() for word in ['crash', 'error', 'exception']):
            category = BugCategory.CRASH
        elif any(word in feedback.description.lower() for word in ['wrong', 'incorrect', 'calculation']):
            category = BugCategory.CALCULATION_ERROR
        elif any(word in feedback.description.lower() for word in ['slow', 'performance', 'timeout']):
            category = BugCategory.PERFORMANCE
        
        # Map severity to priority
        priority_map = {
            Severity.CRITICAL: BugPriority.P0,
            Severity.HIGH: BugPriority.P1,
            Severity.MEDIUM: BugPriority.P2,
            Severity.LOW: BugPriority.P3,
        }
        
        return cls(
            bug_id=f"BUG-{feedback.feedback_id}",
            title=feedback.title,
            description=feedback.description,
            category=category,
            priority=priority_map.get(feedback.severity, BugPriority.P2),
            severity=feedback.severity,
            status=feedback.status,
            reporter=feedback.user_name,
            reported_date=feedback.timestamp,
            steps_to_reproduce=feedback.steps_to_reproduce,
            expected_behavior=feedback.expected_behavior,
            actual_behavior=feedback.actual_behavior,
            page=feedback.page,
            browser=feedback.browser,
            assignee=feedback.assignee,
            resolution=feedback.resolution,
            tags=feedback.tags,
        )


class BugTracker:
    """Track and manage bugs."""
    
    def __init__(self, storage_path: str = "data/uat/bugs.json"):
        """Initialize bug tracker."""
        self.storage_path = storage_path
        self.bugs: List[Bug] = []
        self._load_bugs()
    
    def _load_bugs(self) -> None:
        """Load bugs from storage."""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                # Would deserialize here
        except FileNotFoundError:
            self.bugs = []
    
    def _save_bugs(self) -> None:
        """Save bugs to storage."""
        with open(self.storage_path, 'w') as f:
            json.dump({
                'bugs': [bug.to_dict() for bug in self.bugs],
                'last_updated': datetime.now().isoformat(),
            }, f, indent=2)
    
    def create_bug(self, **kwargs) -> Bug:
        """Create new bug."""
        bug_id = f"BUG-{len(self.bugs) + 1:04d}"
        bug = Bug(bug_id=bug_id, **kwargs)
        self.bugs.append(bug)
        self._save_bugs()
        return bug
    
    def assign_bug(self, bug_id: str, assignee: str) -> Optional[Bug]:
        """Assign bug to developer."""
        for bug in self.bugs:
            if bug.bug_id == bug_id:
                bug.assignee = assignee
                bug.assigned_date = datetime.now()
                bug.status = FeedbackStatus.IN_PROGRESS
                bug.updated_at = datetime.now()
                self._save_bugs()
                return bug
        return None
    
    def resolve_bug(
        self,
        bug_id: str,
        resolution: str,
        root_cause: str = "",
        fix_description: str = ""
    ) -> Optional[Bug]:
        """Mark bug as resolved."""
        for bug in self.bugs:
            if bug.bug_id == bug_id:
                bug.status = FeedbackStatus.RESOLVED
                bug.resolution_date = datetime.now()
                bug.resolution = resolution
                bug.root_cause = root_cause
                bug.fix_description = fix_description
                bug.updated_at = datetime.now()
                self._save_bugs()
                return bug
        return None
    
    def mark_duplicate(self, bug_id: str, duplicate_of: str) -> Optional[Bug]:
        """Mark bug as duplicate."""
        for bug in self.bugs:
            if bug.bug_id == bug_id:
                bug.status = FeedbackStatus.DUPLICATE
                bug.duplicate_of = duplicate_of
                bug.updated_at = datetime.now()
                self._save_bugs()
                
                # Link to original
                for original in self.bugs:
                    if original.bug_id == duplicate_of:
                        if bug_id not in original.related_bugs:
                            original.related_bugs.append(bug_id)
                
                return bug
        return None
    
    def get_open_bugs(self, priority: Optional[BugPriority] = None) -> List[Bug]:
        """Get open bugs."""
        open_bugs = [bug for bug in self.bugs if bug.is_open]
        
        if priority:
            open_bugs = [bug for bug in open_bugs if bug.priority == priority]
        
        return sorted(open_bugs, key=lambda b: (
            list(BugPriority).index(b.priority),
            b.reported_date
        ))
    
    def get_bug_metrics(self) -> Dict[str, Any]:
        """Get bug tracking metrics."""
        total = len(self.bugs)
        
        if total == 0:
            return {
                'total': 0,
                'open': 0,
                'resolved': 0,
                'by_priority': {},
                'by_category': {},
                'avg_resolution_time_hours': 0,
            }
        
        open_bugs = [b for b in self.bugs if b.is_open]
        resolved_bugs = [b for b in self.bugs if b.status == FeedbackStatus.RESOLVED]
        
        # By priority
        by_priority = {}
        for priority in BugPriority:
            count = sum(1 for b in self.bugs if b.priority == priority)
            open_count = sum(1 for b in open_bugs if b.priority == priority)
            if count > 0:
                by_priority[priority.value] = {
                    'total': count,
                    'open': open_count,
                    'resolved': count - open_count,
                }
        
        # By category
        by_category = {}
        for category in BugCategory:
            count = sum(1 for b in self.bugs if b.category == category)
            if count > 0:
                by_category[category.value] = count
        
        # Resolution times
        resolution_times = [
            b.time_to_resolve_hours for b in resolved_bugs
            if b.time_to_resolve_hours is not None
        ]
        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
        
        # Assignment times
        assignment_times = [
            b.time_to_assign_hours for b in self.bugs
            if b.time_to_assign_hours is not None
        ]
        avg_assignment_time = sum(assignment_times) / len(assignment_times) if assignment_times else 0
        
        return {
            'total': total,
            'open': len(open_bugs),
            'resolved': len(resolved_bugs),
            'by_priority': by_priority,
            'by_category': by_category,
            'avg_resolution_time_hours': avg_resolution_time,
            'avg_assignment_time_hours': avg_assignment_time,
            'resolution_rate': len(resolved_bugs) / total * 100 if total > 0 else 0,
        }
    
    def get_critical_bugs(self) -> List[Bug]:
        """Get critical open bugs (P0/P1)."""
        return [
            bug for bug in self.bugs
            if bug.is_open and bug.priority in [BugPriority.P0, BugPriority.P1]
        ]
    
    def get_stale_bugs(self, days: int = 7) -> List[Bug]:
        """Get bugs open for more than N days."""
        cutoff = datetime.now()
        cutoff = cutoff.replace(day=cutoff.day - days) if cutoff.day > days else cutoff
        
        return [
            bug for bug in self.bugs
            if bug.is_open and bug.reported_date < cutoff
        ]
    
    def generate_burn_down_data(self) -> Dict[str, List[int]]:
        """
        Generate bug burn-down chart data.
        
        Returns:
            Dict with dates and bug counts
        """
        if not self.bugs:
            return {'dates': [], 'open': [], 'resolved': []}
        
        # Group by date
        from collections import defaultdict
        daily_data = defaultdict(lambda: {'opened': 0, 'resolved': 0})
        
        for bug in self.bugs:
            report_date = bug.reported_date.date()
            daily_data[report_date]['opened'] += 1
            
            if bug.resolution_date:
                resolve_date = bug.resolution_date.date()
                daily_data[resolve_date]['resolved'] += 1
        
        # Calculate cumulative
        dates = sorted(daily_data.keys())
        open_count = []
        cumulative_open = 0
        
        for date in dates:
            cumulative_open += daily_data[date]['opened'] - daily_data[date]['resolved']
            open_count.append(cumulative_open)
        
        return {
            'dates': [str(d) for d in dates],
            'open': open_count,
        }
    
    def export_bug_report(self, filepath: str) -> None:
        """Export comprehensive bug report."""
        metrics = self.get_bug_metrics()
        critical = self.get_critical_bugs()
        stale = self.get_stale_bugs()
        burn_down = self.generate_burn_down_data()
        
        report = {
            'summary': metrics,
            'critical_bugs': [b.to_dict() for b in critical],
            'stale_bugs': [b.to_dict() for b in stale],
            'burn_down': burn_down,
            'all_bugs': [b.to_dict() for b in self.bugs],
            'generated_at': datetime.now().isoformat(),
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
