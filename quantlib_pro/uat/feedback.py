"""
UAT Feedback Collection System

Structured feedback capture, categorization, and analysis.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import json
from pathlib import Path


class FeedbackType(Enum):
    """Feedback types."""
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    USABILITY = "usability"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    GENERAL = "general"


class Severity(Enum):
    """Issue severity levels."""
    CRITICAL = "critical"  # System unusable, data corruption
    HIGH = "high"  # Major feature broken
    MEDIUM = "medium"  # Minor feature issue
    LOW = "low"  # Cosmetic, enhancement
    

class FeedbackStatus(Enum):
    """Feedback processing status."""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    WONT_FIX = "wont_fix"
    DUPLICATE = "duplicate"


@dataclass
class Feedback:
    """User feedback item."""
    feedback_id: str
    timestamp: datetime
    user_name: str
    user_role: str
    feedback_type: FeedbackType
    severity: Severity
    title: str
    description: str
    steps_to_reproduce: List[str] = field(default_factory=list)
    expected_behavior: str = ""
    actual_behavior: str = ""
    page: str = ""
    browser: str = ""
    screenshot_path: Optional[str] = None
    status: FeedbackStatus = FeedbackStatus.NEW
    assignee: Optional[str] = None
    resolution: str = ""
    tags: List[str] = field(default_factory=list)
    related_issues: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'feedback_id': self.feedback_id,
            'timestamp': self.timestamp.isoformat(),
            'user_name': self.user_name,
            'user_role': self.user_role,
            'feedback_type': self.feedback_type.value,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'steps_to_reproduce': self.steps_to_reproduce,
            'expected_behavior': self.expected_behavior,
            'actual_behavior': self.actual_behavior,
            'page': self.page,
            'browser': self.browser,
            'screenshot_path': self.screenshot_path,
            'status': self.status.value,
            'assignee': self.assignee,
            'resolution': self.resolution,
            'tags': self.tags,
            'related_issues': self.related_issues,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Feedback':
        """Create from dictionary."""
        return cls(
            feedback_id=data['feedback_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            user_name=data['user_name'],
            user_role=data['user_role'],
            feedback_type=FeedbackType(data['feedback_type']),
            severity=Severity(data['severity']),
            title=data['title'],
            description=data['description'],
            steps_to_reproduce=data.get('steps_to_reproduce', []),
            expected_behavior=data.get('expected_behavior', ''),
            actual_behavior=data.get('actual_behavior', ''),
            page=data.get('page', ''),
            browser=data.get('browser', ''),
            screenshot_path=data.get('screenshot_path'),
            status=FeedbackStatus(data.get('status', 'new')),
            assignee=data.get('assignee'),
            resolution=data.get('resolution', ''),
            tags=data.get('tags', []),
            related_issues=data.get('related_issues', []),
            created_at=datetime.fromisoformat(data.get('created_at', data['timestamp'])),
            updated_at=datetime.fromisoformat(data.get('updated_at', data['timestamp'])),
        )


class FeedbackCollector:
    """Collect and manage user feedback."""
    
    def __init__(self, storage_path: str = "data/uat/feedback.json"):
        """
        Initialize feedback collector.
        
        Args:
            storage_path: Path to feedback storage file
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.feedback_items: List[Feedback] = []
        self._load_feedback()
    
    def _load_feedback(self) -> None:
        """Load feedback from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.feedback_items = [
                        Feedback.from_dict(item) for item in data.get('feedback', [])
                    ]
            except Exception as e:
                print(f"Error loading feedback: {e}")
                self.feedback_items = []
    
    def _save_feedback(self) -> None:
        """Save feedback to storage."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'feedback': [item.to_dict() for item in self.feedback_items],
                    'last_updated': datetime.now().isoformat(),
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving feedback: {e}")
    
    def submit_feedback(
        self,
        user_name: str,
        user_role: str,
        feedback_type: FeedbackType,
        severity: Severity,
        title: str,
        description: str,
        **kwargs
    ) -> Feedback:
        """
        Submit new feedback.
        
        Args:
            user_name: Name of user submitting feedback
            user_role: Role of user
            feedback_type: Type of feedback
            severity: Severity level
            title: Brief title
            description: Detailed description
            **kwargs: Additional fields
            
        Returns:
            Created feedback item
        """
        feedback_id = f"FB-{len(self.feedback_items) + 1:04d}"
        
        feedback = Feedback(
            feedback_id=feedback_id,
            timestamp=datetime.now(),
            user_name=user_name,
            user_role=user_role,
            feedback_type=feedback_type,
            severity=severity,
            title=title,
            description=description,
            **{k: v for k, v in kwargs.items() if hasattr(Feedback, k)}
        )
        
        self.feedback_items.append(feedback)
        self._save_feedback()
        
        return feedback
    
    def update_status(
        self,
        feedback_id: str,
        status: FeedbackStatus,
        assignee: Optional[str] = None,
        resolution: str = ""
    ) -> Optional[Feedback]:
        """
        Update feedback status.
        
        Args:
            feedback_id: Feedback ID
            status: New status
            assignee: Assigned developer
            resolution: Resolution notes
            
        Returns:
            Updated feedback or None if not found
        """
        for feedback in self.feedback_items:
            if feedback.feedback_id == feedback_id:
                feedback.status = status
                feedback.updated_at = datetime.now()
                if assignee:
                    feedback.assignee = assignee
                if resolution:
                    feedback.resolution = resolution
                self._save_feedback()
                return feedback
        return None
    
    def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """Get feedback by ID."""
        for feedback in self.feedback_items:
            if feedback.feedback_id == feedback_id:
                return feedback
        return None
    
    def filter_feedback(
        self,
        feedback_type: Optional[FeedbackType] = None,
        severity: Optional[Severity] = None,
        status: Optional[FeedbackStatus] = None,
        user_role: Optional[str] = None,
        page: Optional[str] = None,
    ) -> List[Feedback]:
        """
        Filter feedback by criteria.
        
        Args:
            feedback_type: Filter by type
            severity: Filter by severity
            status: Filter by status
            user_role: Filter by user role
            page: Filter by page
            
        Returns:
            Filtered feedback list
        """
        filtered = self.feedback_items
        
        if feedback_type:
            filtered = [f for f in filtered if f.feedback_type == feedback_type]
        if severity:
            filtered = [f for f in filtered if f.severity == severity]
        if status:
            filtered = [f for f in filtered if f.status == status]
        if user_role:
            filtered = [f for f in filtered if f.user_role == user_role]
        if page:
            filtered = [f for f in filtered if f.page == page]
        
        return filtered
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get feedback statistics.
        
        Returns:
            Statistics dictionary
        """
        total = len(self.feedback_items)
        
        if total == 0:
            return {
                'total': 0,
                'by_type': {},
                'by_severity': {},
                'by_status': {},
                'by_page': {},
                'resolution_rate': 0,
            }
        
        # By type
        by_type = {}
        for feedback_type in FeedbackType:
            count = sum(1 for f in self.feedback_items if f.feedback_type == feedback_type)
            if count > 0:
                by_type[feedback_type.value] = count
        
        # By severity
        by_severity = {}
        for severity in Severity:
            count = sum(1 for f in self.feedback_items if f.severity == severity)
            if count > 0:
                by_severity[severity.value] = count
        
        # By status
        by_status = {}
        for status in FeedbackStatus:
            count = sum(1 for f in self.feedback_items if f.status == status)
            if count > 0:
                by_status[status.value] = count
        
        # By page
        by_page = {}
        for feedback in self.feedback_items:
            if feedback.page:
                by_page[feedback.page] = by_page.get(feedback.page, 0) + 1
        
        # Resolution rate
        resolved = sum(1 for f in self.feedback_items if f.status in [FeedbackStatus.RESOLVED, FeedbackStatus.WONT_FIX])
        resolution_rate = (resolved / total * 100) if total > 0 else 0
        
        # Open critical/high issues
        open_critical = sum(
            1 for f in self.feedback_items
            if f.severity == Severity.CRITICAL and f.status not in [FeedbackStatus.RESOLVED, FeedbackStatus.WONT_FIX]
        )
        open_high = sum(
            1 for f in self.feedback_items
            if f.severity == Severity.HIGH and f.status not in [FeedbackStatus.RESOLVED, FeedbackStatus.WONT_FIX]
        )
        
        return {
            'total': total,
            'by_type': by_type,
            'by_severity': by_severity,
            'by_status': by_status,
            'by_page': by_page,
            'resolution_rate': resolution_rate,
            'open_critical': open_critical,
            'open_high': open_high,
        }
    
    def get_trending_issues(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get trending issues (most common problems).
        
        Args:
            limit: Maximum number of issues to return
            
        Returns:
            List of trending issues with counts
        """
        # Group by title similarity (simple version)
        issue_counts = {}
        for feedback in self.feedback_items:
            if feedback.feedback_type == FeedbackType.BUG:
                # Normalize title
                key = feedback.title.lower().strip()
                if key not in issue_counts:
                    issue_counts[key] = {
                        'title': feedback.title,
                        'count': 0,
                        'severity': feedback.severity.value,
                        'example_id': feedback.feedback_id,
                    }
                issue_counts[key]['count'] += 1
        
        # Sort by count
        trending = sorted(issue_counts.values(), key=lambda x: x['count'], reverse=True)
        return trending[:limit]
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive feedback report.
        
        Returns:
            Report dictionary
        """
        stats = self.get_statistics()
        trending = self.get_trending_issues()
        
        # Recent feedback (last 7 days)
        recent_cutoff = datetime.now()
        recent_cutoff = recent_cutoff.replace(day=recent_cutoff.day - 7)
        recent = [f for f in self.feedback_items if f.timestamp >= recent_cutoff]
        
        # Critical open issues
        critical_open = self.filter_feedback(
            severity=Severity.CRITICAL,
            status=FeedbackStatus.NEW
        )
        
        return {
            'statistics': stats,
            'trending_issues': trending,
            'recent_count': len(recent),
            'critical_open_count': len(critical_open),
            'critical_open': [f.to_dict() for f in critical_open],
            'generated_at': datetime.now().isoformat(),
        }
    
    def export_csv(self, filepath: str) -> None:
        """Export feedback to CSV."""
        import csv
        
        with open(filepath, 'w', newline='') as f:
            if not self.feedback_items:
                return
            
            fieldnames = [
                'feedback_id', 'timestamp', 'user_name', 'user_role',
                'feedback_type', 'severity', 'status', 'title',
                'description', 'page', 'assignee', 'resolution'
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for feedback in self.feedback_items:
                row = {
                    'feedback_id': feedback.feedback_id,
                    'timestamp': feedback.timestamp.isoformat(),
                    'user_name': feedback.user_name,
                    'user_role': feedback.user_role,
                    'feedback_type': feedback.feedback_type.value,
                    'severity': feedback.severity.value,
                    'status': feedback.status.value,
                    'title': feedback.title,
                    'description': feedback.description,
                    'page': feedback.page,
                    'assignee': feedback.assignee or '',
                    'resolution': feedback.resolution,
                }
                writer.writerow(row)


class FeedbackAnalyzer:
    """Analyze feedback patterns and insights."""
    
    def __init__(self, feedback_collector: FeedbackCollector):
        """Initialize analyzer."""
        self.collector = feedback_collector
    
    def analyze_usability_issues(self) -> Dict[str, Any]:
        """Analyze usability feedback."""
        usability = self.collector.filter_feedback(feedback_type=FeedbackType.USABILITY)
        
        if not usability:
            return {'total': 0, 'insights': []}
        
        # Common themes
        themes = {}
        for feedback in usability:
            for tag in feedback.tags:
                themes[tag] = themes.get(tag, 0) + 1
        
        # Pages with most issues
        page_issues = {}
        for feedback in usability:
            if feedback.page:
                page_issues[feedback.page] = page_issues.get(feedback.page, 0) + 1
        
        return {
            'total': len(usability),
            'themes': themes,
            'problematic_pages': sorted(page_issues.items(), key=lambda x: x[1], reverse=True),
            'avg_severity': sum(
                ['critical', 'high', 'medium', 'low'].index(f.severity.value)
                for f in usability
            ) / len(usability) if usability else 0,
        }
    
    def analyze_performance_feedback(self) -> Dict[str, Any]:
        """Analyze performance-related feedback."""
        performance = self.collector.filter_feedback(feedback_type=FeedbackType.PERFORMANCE)
        
        if not performance:
            return {'total': 0, 'slow_features': []}
        
        # Extract slow features
        slow_features = {}
        for feedback in performance:
            if feedback.page:
                slow_features[feedback.page] = slow_features.get(feedback.page, 0) + 1
        
        return {
            'total': len(performance),
            'slow_features': sorted(slow_features.items(), key=lambda x: x[1], reverse=True),
        }
    
    def get_quick_wins(self) -> List[Feedback]:
        """
        Identify quick win improvements.
        
        Returns:
            Low-effort, high-impact feedback items
        """
        # Low severity, high frequency issues
        quick_wins = []
        
        for feedback in self.collector.feedback_items:
            if (feedback.severity == Severity.LOW and
                feedback.status == FeedbackStatus.NEW and
                feedback.feedback_type in [FeedbackType.USABILITY, FeedbackType.DOCUMENTATION]):
                quick_wins.append(feedback)
        
        return quick_wins[:10]  # Top 10
