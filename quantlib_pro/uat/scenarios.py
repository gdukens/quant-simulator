"""
User Acceptance Testing (UAT) Scenarios

Comprehensive test scenarios for different user roles and workflows.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime
import json


class UserRole(Enum):
    """User role types."""
    QUANTITATIVE_ANALYST = "quantitative_analyst"
    RISK_MANAGER = "risk_manager"
    OPTIONS_TRADER = "options_trader"
    PORTFOLIO_MANAGER = "portfolio_manager"
    ALGORITHMIC_TRADER = "algorithmic_trader"
    COMPLIANCE_OFFICER = "compliance_officer"


class TestStatus(Enum):
    """UAT test status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


class Priority(Enum):
    """Test priority."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TestStep:
    """Individual test step."""
    step_number: int
    description: str
    expected_result: str
    actual_result: Optional[str] = None
    passed: Optional[bool] = None
    notes: str = ""
    
    def execute(self, context: Dict[str, Any]) -> bool:
        """
        Execute test step.
        
        Args:
            context: Test execution context
            
        Returns:
            Whether step passed
        """
        # Placeholder for actual execution
        return True


@dataclass
class UATScenario:
    """User acceptance test scenario."""
    scenario_id: str
    title: str
    description: str
    user_role: UserRole
    priority: Priority
    prerequisites: List[str]
    steps: List[TestStep]
    status: TestStatus = TestStatus.NOT_STARTED
    tester: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    pass_criteria: str = ""
    notes: str = ""
    issues: List[str] = field(default_factory=list)
    
    @property
    def duration_minutes(self) -> Optional[float]:
        """Test execution duration in minutes."""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() / 60
        return None
    
    @property
    def passed_steps(self) -> int:
        """Number of passed steps."""
        return sum(1 for step in self.steps if step.passed is True)
    
    @property
    def failed_steps(self) -> int:
        """Number of failed steps."""
        return sum(1 for step in self.steps if step.passed is False)
    
    @property
    def completion_percentage(self) -> float:
        """Test completion percentage."""
        total = len(self.steps)
        if total == 0:
            return 0.0
        completed = sum(1 for step in self.steps if step.passed is not None)
        return (completed / total) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'scenario_id': self.scenario_id,
            'title': self.title,
            'description': self.description,
            'user_role': self.user_role.value,
            'priority': self.priority.value,
            'status': self.status.value,
            'tester': self.tester,
            'duration_minutes': self.duration_minutes,
            'passed_steps': self.passed_steps,
            'failed_steps': self.failed_steps,
            'completion_percentage': self.completion_percentage,
            'issues': self.issues,
        }


class UATScenarioLibrary:
    """Library of predefined UAT scenarios."""
    
    @staticmethod
    def get_all_scenarios() -> List[UATScenario]:
        """Get all UAT scenarios."""
        scenarios = []
        
        # Portfolio Manager scenarios
        scenarios.extend([
            UATScenarioLibrary.portfolio_optimization_basic(),
            UATScenarioLibrary.portfolio_rebalancing(),
            UATScenarioLibrary.efficient_frontier_analysis(),
        ])
        
        # Risk Manager scenarios
        scenarios.extend([
            UATScenarioLibrary.var_calculation(),
            UATScenarioLibrary.stress_testing(),
            UATScenarioLibrary.tail_risk_analysis(),
        ])
        
        # Options Trader scenarios
        scenarios.extend([
            UATScenarioLibrary.options_pricing(),
            UATScenarioLibrary.greeks_calculation(),
            UATScenarioLibrary.monte_carlo_pricing(),
        ])
        
        # Quant Analyst scenarios
        scenarios.extend([
            UATScenarioLibrary.regime_detection(),
            UATScenarioLibrary.correlation_analysis(),
            UATScenarioLibrary.backtesting(),
        ])
        
        # Compliance Officer scenarios
        scenarios.extend([
            UATScenarioLibrary.audit_trail_verification(),
            UATScenarioLibrary.policy_enforcement(),
        ])
        
        return scenarios
    
    @staticmethod
    def portfolio_optimization_basic() -> UATScenario:
        """Basic portfolio optimization scenario."""
        return UATScenario(
            scenario_id="PM-001",
            title="Basic Portfolio Optimization",
            description="Create and optimize a multi-asset portfolio using MPT",
            user_role=UserRole.PORTFOLIO_MANAGER,
            priority=Priority.CRITICAL,
            prerequisites=[
                "Access to Portfolio Optimizer page",
                "Sample market data available",
            ],
            steps=[
                TestStep(1, "Navigate to Portfolio Optimizer page", "Page loads successfully"),
                TestStep(2, "Select 5-10 tickers (e.g., AAPL, MSFT, GOOGL, JPM, JNJ)", "Tickers displayed in selection"),
                TestStep(3, "Set date range (1 year historical)", "Date range accepted"),
                TestStep(4, "Click 'Fetch Data'", "Historical data loaded, no errors"),
                TestStep(5, "Select 'Maximum Sharpe Ratio' optimization", "Option selected"),
                TestStep(6, "Click 'Optimize'", "Optimization completes within 5 seconds"),
                TestStep(7, "Review optimal weights", "Weights sum to 100%, all non-negative"),
                TestStep(8, "Check Sharpe ratio", "Sharpe ratio > 0 and displayed correctly"),
                TestStep(9, "View efficient frontier chart", "Chart displays with frontier curve"),
                TestStep(10, "Export results to CSV", "CSV downloads successfully"),
            ],
            pass_criteria="All steps complete without errors, optimization completes <5s, results are mathematically valid"
        )
    
    @staticmethod
    def portfolio_rebalancing() -> UATScenario:
        """Portfolio rebalancing scenario."""
        return UATScenario(
            scenario_id="PM-002",
            title="Portfolio Rebalancing",
            description="Rebalance existing portfolio to target weights",
            user_role=UserRole.PORTFOLIO_MANAGER,
            priority=Priority.HIGH,
            prerequisites=[
                "Existing portfolio with current weights",
                "Target weights from optimization",
            ],
            steps=[
                TestStep(1, "Input current portfolio holdings", "Holdings accepted"),
                TestStep(2, "Input target weights", "Weights accepted, sum validates to 100%"),
                TestStep(3, "Set transaction cost (0.1%)", "Cost parameter accepted"),
                TestStep(4, "Calculate rebalancing trades", "Trades calculated successfully"),
                TestStep(5, "Review buy/sell recommendations", "Recommendations displayed with quantities"),
                TestStep(6, "Check total transaction cost", "Cost displayed and reasonable"),
                TestStep(7, "Verify post-rebalance weights", "Matches target within tolerance"),
            ],
            pass_criteria="Rebalancing calculation accurate, transaction costs properly included"
        )
    
    @staticmethod
    def efficient_frontier_analysis() -> UATScenario:
        """Efficient frontier analysis scenario."""
        return UATScenario(
            scenario_id="PM-003",
            title="Efficient Frontier Analysis",
            description="Generate and analyze efficient frontier",
            user_role=UserRole.PORTFOLIO_MANAGER,
            priority=Priority.MEDIUM,
            prerequisites=[
                "Portfolio data loaded",
            ],
            steps=[
                TestStep(1, "Generate efficient frontier (50 points)", "Calculation completes"),
                TestStep(2, "Identify minimum volatility portfolio", "Point marked on chart"),
                TestStep(3, "Identify maximum Sharpe portfolio", "Point marked on chart"),
                TestStep(4, "Select target return level", "Frontier point highlighted"),
                TestStep(5, "View corresponding weights", "Weights displayed for selected point"),
                TestStep(6, "Compare multiple portfolios", "Multiple points can be selected"),
            ],
            pass_criteria="Frontier displays correctly, all points are optimal"
        )
    
    @staticmethod
    def var_calculation() -> UATScenario:
        """VaR calculation scenario."""
        return UATScenario(
            scenario_id="RM-001",
            title="Value at Risk Calculation",
            description="Calculate VaR using multiple methodologies",
            user_role=UserRole.RISK_MANAGER,
            priority=Priority.CRITICAL,
            prerequisites=[
                "Portfolio returns data available",
                "Portfolio value defined ($1M)",
            ],
            steps=[
                TestStep(1, "Navigate to Risk Analytics page", "Page loads"),
                TestStep(2, "Set confidence level (95%)", "Confidence level accepted"),
                TestStep(3, "Calculate parametric VaR", "Result displayed within 1 second"),
                TestStep(4, "Calculate historical VaR", "Result displayed within 1 second"),
                TestStep(5, "Calculate Monte Carlo VaR (10K sims)", "Result displayed within 10 seconds"),
                TestStep(6, "Compare all three methods", "Results are within reasonable range"),
                TestStep(7, "Calculate CVaR", "CVaR ≥ VaR (more negative)"),
                TestStep(8, "View VaR confidence interval", "Confidence interval displayed"),
            ],
            pass_criteria="All VaR methods produce valid results, CVaR > VaR, performance acceptable"
        )
    
    @staticmethod
    def stress_testing() -> UATScenario:
        """Stress testing scenario."""
        return UATScenario(
            scenario_id="RM-002",
            title="Portfolio Stress Testing",
            description="Perform historical and hypothetical stress tests",
            user_role=UserRole.RISK_MANAGER,
            priority=Priority.HIGH,
            prerequisites=[
                "Portfolio defined with positions",
            ],
            steps=[
                TestStep(1, "Select historical scenario (COVID-19 crash)", "Scenario loaded"),
                TestStep(2, "Run historical stress test", "Impact calculated"),
                TestStep(3, "Review portfolio loss", "Loss displayed as percentage and $"),
                TestStep(4, "Switch to hypothetical scenario", "Tab changes"),
                TestStep(5, "Define shock: -30% tech stocks", "Shock parameters accepted"),
                TestStep(6, "Run hypothetical test", "Impact calculated"),
                TestStep(7, "Compare scenarios", "Multiple scenarios can be compared"),
                TestStep(8, "Export stress test report", "PDF/CSV export successful"),
            ],
            pass_criteria="Stress tests produce realistic impacts, export works"
        )
    
    @staticmethod
    def tail_risk_analysis() -> UATScenario:
        """Tail risk analysis scenario."""
        return UATScenario(
            scenario_id="RM-003",
            title="Tail Risk Analysis",
            description="Analyze extreme risk using EVT",
            user_role=UserRole.RISK_MANAGER,
            priority=Priority.MEDIUM,
            prerequisites=[
                "Long return history (3+ years)",
            ],
            steps=[
                TestStep(1, "Navigate to Advanced Analytics > Tail Risk", "Tab loads"),
                TestStep(2, "Fit GPD distribution to tail", "Distribution fitted"),
                TestStep(3, "Review Hill estimator plot", "Plot displayed"),
                TestStep(4, "Calculate extreme VaR (99.9%)", "Result displayed"),
                TestStep(5, "View tail index", "Tail index estimated"),
                TestStep(6, "Compare to normal distribution", "Comparison shown"),
            ],
            pass_criteria="EVT analysis completes, tail index reasonable"
        )
    
    @staticmethod
    def options_pricing() -> UATScenario:
        """Options pricing scenario."""
        return UATScenario(
            scenario_id="OT-001",
            title="Black-Scholes Options Pricing",
            description="Price European call and put options",
            user_role=UserRole.OPTIONS_TRADER,
            priority=Priority.CRITICAL,
            prerequisites=[
                "Access to Options Pricing page",
            ],
            steps=[
                TestStep(1, "Navigate to Options Pricing page", "Page loads"),
                TestStep(2, "Input: S=100, K=100, T=0.25, r=0.05, σ=0.25", "Inputs accepted"),
                TestStep(3, "Calculate call price", "Price displayed instantly"),
                TestStep(4, "Calculate put price", "Price displayed instantly"),
                TestStep(5, "Verify put-call parity", "Parity check passes"),
                TestStep(6, "Change strike to 105 (OTM)", "Call price decreases"),
                TestStep(7, "Increase volatility to 0.30", "Both prices increase"),
                TestStep(8, "View Greeks (all)", "Delta, Gamma, Vega, Theta, Rho displayed"),
            ],
            pass_criteria="Pricing is accurate (<1% error vs. known values), Greeks correct"
        )
    
    @staticmethod
    def greeks_calculation() -> UATScenario:
        """Greeks calculation scenario."""
        return UATScenario(
            scenario_id="OT-002",
            title="Options Greeks Calculation",
            description="Calculate and interpret option Greeks",
            user_role=UserRole.OPTIONS_TRADER,
            priority=Priority.HIGH,
            prerequisites=[
                "Option priced with Black-Scholes",
            ],
            steps=[
                TestStep(1, "Price ATM call option", "Price displayed"),
                TestStep(2, "View Delta", "Delta ≈ 0.5 for ATM call"),
                TestStep(3, "View Gamma", "Gamma > 0, max at ATM"),
                TestStep(4, "View Vega", "Vega > 0"),
                TestStep(5, "View Theta", "Theta < 0 (time decay)"),
                TestStep(6, "Create Greeks visualization", "Chart shows all Greeks"),
                TestStep(7, "Change to deep ITM", "Delta approaches 1.0"),
                TestStep(8, "Change to deep OTM", "Delta approaches 0.0"),
            ],
            pass_criteria="All Greeks calculated correctly, visualizations accurate"
        )
    
    @staticmethod
    def monte_carlo_pricing() -> UATScenario:
        """Monte Carlo options pricing scenario."""
        return UATScenario(
            scenario_id="OT-003",
            title="Monte Carlo Options Pricing",
            description="Price options using Monte Carlo simulation",
            user_role=UserRole.OPTIONS_TRADER,
            priority=Priority.MEDIUM,
            prerequisites=[
                "Access to Monte Carlo page",
            ],
            steps=[
                TestStep(1, "Navigate to Monte Carlo page", "Page loads"),
                TestStep(2, "Set simulation parameters (100K paths)", "Parameters accepted"),
                TestStep(3, "Price European call", "Price calculated"),
                TestStep(4, "Compare to Black-Scholes", "Prices within 2%"),
                TestStep(5, "Price Asian call", "Price calculated (lower than European)"),
                TestStep(6, "Price barrier option (knock-out)", "Price calculated"),
                TestStep(7, "View convergence plot", "Shows convergence with # of sims"),
                TestStep(8, "View price distribution", "Histogram displayed"),
            ],
            pass_criteria="MC prices converge to analytical values for European, exotic options price correctly"
        )
    
    @staticmethod
    def regime_detection() -> UATScenario:
        """Market regime detection scenario."""
        return UATScenario(
            scenario_id="QA-001",
            title="Market Regime Detection",
            description="Detect market regimes using HMM",
            user_role=UserRole.QUANTITATIVE_ANALYST,
            priority=Priority.HIGH,
            prerequisites=[
                "Market returns data (3+ years)",
            ],
            steps=[
                TestStep(1, "Navigate to Regime Detection page", "Page loads"),
                TestStep(2, "Load market data", "Data loaded successfully"),
                TestStep(3, "Set number of regimes (3)", "Parameter accepted"),
                TestStep(4, "Fit HMM model", "Model fitted within 30 seconds"),
                TestStep(5, "View regime classification", "Regimes displayed on chart"),
                TestStep(6, "Review transition matrix", "Matrix displayed"),
                TestStep(7, "Analyze regime characteristics", "Mean/volatility per regime shown"),
                TestStep(8, "Identify current regime", "Current regime highlighted"),
            ],
            pass_criteria="Regimes detected, characteristics make sense (bull/bear/sideways)"
        )
    
    @staticmethod
    def correlation_analysis() -> UATScenario:
        """Correlation analysis scenario."""
        return UATScenario(
            scenario_id="QA-002",
            title="Correlation Regime Analysis",
            description="Analyze correlation regimes and breakdowns",
            user_role=UserRole.QUANTITATIVE_ANALYST,
            priority=Priority.MEDIUM,
            prerequisites=[
                "Multi-asset returns data",
            ],
            steps=[
                TestStep(1, "Navigate to Advanced Analytics > Correlation", "Tab loads"),
                TestStep(2, "Calculate rolling correlations (90-day)", "Correlations calculated"),
                TestStep(3, "View correlation heatmap", "Heatmap displayed"),
                TestStep(4, "Identify correlation regimes", "Regimes detected and labeled"),
                TestStep(5, "Detect correlation breakdowns", "Breakdown periods highlighted"),
                TestStep(6, "Analyze crisis periods", "Correlations approached 1 during crisis"),
            ],
            pass_criteria="Correlation regimes identified, crisis correlations elevated"
        )
    
    @staticmethod
    def backtesting() -> UATScenario:
        """Strategy backtesting scenario."""
        return UATScenario(
            scenario_id="QA-003",
            title="Strategy Backtesting",
            description="Backtest trading strategy on historical data",
            user_role=UserRole.ALGORITHMIC_TRADER,
            priority=Priority.HIGH,
            prerequisites=[
                "Trading strategy defined",
                "Historical data available",
            ],
            steps=[
                TestStep(1, "Navigate to Backtesting page", "Page loads"),
                TestStep(2, "Select strategy (MA Crossover)", "Strategy selected"),
                TestStep(3, "Set parameters (50/200 day)", "Parameters accepted"),
                TestStep(4, "Set initial capital ($100K)", "Capital accepted"),
                TestStep(5, "Run backtest", "Backtest completes within 10 seconds"),
                TestStep(6, "Review equity curve", "Curve displayed"),
                TestStep(7, "Check Sharpe ratio", "Sharpe ratio calculated"),
                TestStep(8, "Review max drawdown", "Drawdown displayed"),
                TestStep(9, "Analyze trade list", "All trades listed with P&L"),
                TestStep(10, "Export results", "Results exported successfully"),
            ],
            pass_criteria="Backtest runs successfully, metrics calculated correctly"
        )
    
    @staticmethod
    def audit_trail_verification() -> UATScenario:
        """Audit trail verification scenario."""
        return UATScenario(
            scenario_id="CO-001",
            title="Audit Trail Verification",
            description="Verify audit trail captures all calculations",
            user_role=UserRole.COMPLIANCE_OFFICER,
            priority=Priority.CRITICAL,
            prerequisites=[
                "Access to governance dashboard",
            ],
            steps=[
                TestStep(1, "Perform portfolio optimization", "Optimization completes"),
                TestStep(2, "Navigate to Audit Trail", "Audit page loads"),
                TestStep(3, "Find optimization record", "Record exists with timestamp"),
                TestStep(4, "Verify inputs recorded", "All inputs captured"),
                TestStep(5, "Verify outputs recorded", "All outputs captured"),
                TestStep(6, "Check calculation hash", "Hash present and verifiable"),
                TestStep(7, "Export audit log", "CSV export successful"),
            ],
            pass_criteria="All calculations audited, trail is immutable and complete"
        )
    
    @staticmethod
    def policy_enforcement() -> UATScenario:
        """Policy enforcement scenario."""
        return UATScenario(
            scenario_id="CO-002",
            title="Risk Policy Enforcement",
            description="Verify risk policies are enforced",
            user_role=UserRole.COMPLIANCE_OFFICER,
            priority=Priority.HIGH,
            prerequisites=[
                "Risk policies configured",
            ],
            steps=[
                TestStep(1, "Configure position limit (10% max)", "Policy saved"),
                TestStep(2, "Try to create portfolio with 15% position", "Violation flagged"),
                TestStep(3, "System blocks non-compliant portfolio", "Portfolio rejected"),
                TestStep(4, "View policy violation log", "Violation recorded"),
                TestStep(5, "Configure max leverage (1.5x)", "Policy saved"),
                TestStep(6, "Try to exceed leverage", "Violation flagged"),
                TestStep(7, "Review compliance report", "All violations listed"),
            ],
            pass_criteria="Policies enforced, violations blocked and logged"
        )


class UATExecutor:
    """Execute UAT scenarios and track results."""
    
    def __init__(self):
        """Initialize UAT executor."""
        self.scenarios: List[UATScenario] = []
        self.results: List[Dict[str, Any]] = []
    
    def load_scenarios(self, scenarios: List[UATScenario]) -> None:
        """Load UAT scenarios."""
        self.scenarios = scenarios
    
    def execute_scenario(self, scenario: UATScenario, tester: str) -> Dict[str, Any]:
        """
        Execute UAT scenario.
        
        Args:
            scenario: Scenario to execute
            tester: Name of tester
            
        Returns:
            Execution result
        """
        scenario.tester = tester
        scenario.start_time = datetime.now()
        scenario.status = TestStatus.IN_PROGRESS
        
        try:
            # Execute each step
            for step in scenario.steps:
                # In real UAT, tester would manually execute
                # For now, mark as placeholder
                step.passed = None  # Awaiting manual testing
            
            scenario.end_time = datetime.now()
            
            # Determine overall status
            if scenario.failed_steps > 0:
                scenario.status = TestStatus.FAILED
            elif scenario.passed_steps == len(scenario.steps):
                scenario.status = TestStatus.PASSED
            else:
                scenario.status = TestStatus.IN_PROGRESS
            
            result = scenario.to_dict()
            self.results.append(result)
            
            return result
            
        except Exception as e:
            scenario.status = TestStatus.FAILED
            scenario.notes = f"Execution error: {str(e)}"
            return scenario.to_dict()
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get UAT execution summary.
        
        Returns:
            Summary statistics
        """
        if not self.scenarios:
            return {}
        
        total = len(self.scenarios)
        passed = sum(1 for s in self.scenarios if s.status == TestStatus.PASSED)
        failed = sum(1 for s in self.scenarios if s.status == TestStatus.FAILED)
        in_progress = sum(1 for s in self.scenarios if s.status == TestStatus.IN_PROGRESS)
        not_started = sum(1 for s in self.scenarios if s.status == TestStatus.NOT_STARTED)
        
        # By role
        by_role = {}
        for role in UserRole:
            role_scenarios = [s for s in self.scenarios if s.user_role == role]
            if role_scenarios:
                by_role[role.value] = {
                    'total': len(role_scenarios),
                    'passed': sum(1 for s in role_scenarios if s.status == TestStatus.PASSED),
                    'failed': sum(1 for s in role_scenarios if s.status == TestStatus.FAILED),
                }
        
        # By priority
        by_priority = {}
        for priority in Priority:
            priority_scenarios = [s for s in self.scenarios if s.priority == priority]
            if priority_scenarios:
                by_priority[priority.value] = {
                    'total': len(priority_scenarios),
                    'passed': sum(1 for s in priority_scenarios if s.status == TestStatus.PASSED),
                    'failed': sum(1 for s in priority_scenarios if s.status == TestStatus.FAILED),
                }
        
        return {
            'total_scenarios': total,
            'passed': passed,
            'failed': failed,
            'in_progress': in_progress,
            'not_started': not_started,
            'pass_rate': (passed / total * 100) if total > 0 else 0,
            'by_role': by_role,
            'by_priority': by_priority,
        }
    
    def export_results(self, filepath: str) -> None:
        """Export UAT results to JSON."""
        with open(filepath, 'w') as f:
            json.dump({
                'summary': self.get_summary(),
                'scenarios': [s.to_dict() for s in self.scenarios],
                'export_time': datetime.now().isoformat(),
            }, f, indent=2)
