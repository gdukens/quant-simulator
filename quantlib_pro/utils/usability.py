"""
Usability Helper Module

Provides contextual help, tooltips, and user guidance across the application.
"""

from typing import Dict, List, Optional
import streamlit as st


class HelpContent:
    """Centralized help content for all features."""
    
    PORTFOLIO_OPTIMIZATION = {
        'title': 'Portfolio Optimization Help',
        'sections': [
            {
                'heading': 'Getting Started',
                'content': '''
                1. Select 5-10 stocks from different sectors for diversification
                2. Choose a date range of at least 1 year for reliable statistics  
                3. Click "Fetch Data" to download historical prices
                4. Select an optimization method (MaxSharpe recommended for beginners)
                5. Click "Optimize" to calculate optimal weights
                '''
            },
            {
                'heading': 'Optimization Methods',
                'content': '''
                **Maximum Sharpe Ratio**: Best risk-adjusted returns (recommended)
                **Minimum Volatility**: Lowest risk portfolio  
                **Efficient Frontier**: Explore all optimal portfolios
                **Target Return**: Specify desired return level
                '''
            },
            {
                'heading': 'Understanding Results',
                'content': '''
                **Weights**: Percentage to invest in each stock
                **Expected Return**: Annualized return estimate
                **Volatility**: Annual standard deviation (risk measure)
                **Sharpe Ratio**: Return per unit of risk (higher is better)
                '''
            },
            {
                'heading': 'Common Issues',
                'content': '''
                 **"Optimization failed"**: Try reducing number of stocks or changing date range
                 **Negative Sharpe ratio**: Consider different stocks or time period
                 **All weight in one stock**: Add constraints (max 25% per position)
                '''
            },
        ]
    }
    
    RISK_ANALYSIS = {
        'title': 'Risk Analysis Help',
        'sections': [
            {
                'heading': 'Value at Risk (VaR)',
                'content': '''
                VaR estimates the maximum loss over a time period at a confidence level.
                
                **Example**: VaR of $50K at 95% confidence means:
                - 95% of days, losses will be less than $50K
                - 5% of days, losses could exceed $50K
                
                **Which method to use?**
                - **Parametric**: Fast, assumes normal distribution
                - **Historical**: Based on actual past returns
                - **Monte Carlo**: Most flexible, slower
                '''
            },
            {
                'heading': 'CVaR (Expected Shortfall)',
                'content': '''
                CVaR is the average loss when VaR is exceeded.  
                It answers: "When things go bad, how bad on average?"
                
                CVaR is always more negative (worse) than VaR.
                '''
            },
            {
                'heading': 'Stress Testing',
                'content': '''
                Test portfolio performance under extreme scenarios:
                
                **Historical**: COVID-19 crash, 2008 crisis, dot-com bubble
                **Hypothetical**: Define custom shocks (-30% tech, rates +2%, etc.)
                **Monte Carlo**: Random severe scenarios
                '''
            },
        ]
    }
    
    OPTIONS_PRICING = {
        'title': 'Options Pricing Help',
        'sections': [
            {
                'heading': 'Black-Scholes Inputs',
                'content': '''
                **S (Stock Price)**: Current market price
                **K (Strike Price)**: Exercise price of option
                **T (Time)**: Years until expiration (0.25 = 3 months)
                **r (Risk-Free Rate)**: Treasury yield (e.g., 0.05 = 5%)  
                **σ (Volatility)**: Annual volatility (0.25 = 25%)
                '''
            },
            {
                'heading': 'The Greeks',
                'content': '''
                **Delta**: Price change for $1 move in stock (0-1 for calls)
                **Gamma**: Delta change for $1 move in stock
                **Vega**: Price change for 1% vol increase
                **Theta**: Daily time decay  
                **Rho**: Price change for 1% rate increase
                '''
            },
            {
                'heading': 'Typical Values',
                'content': '''
                At-the-money (S=K) call:
                - Delta ≈ 0.5
                - Gamma maximized
                - Theta most negative
                
                Deep in-the-money call:
                - Delta approaches 1.0
                - Low Gamma
                - Behaves like stock
                '''
            },
        ]
    }
    
    BACKTESTING = {
        'title': 'Backtesting Help',
        'sections': [
            {
                'heading': 'Creating a Strategy',
                'content': '''
                1. Define entry signals (e.g., MA crossover)
                2. Define exit signals  
                3. Set position sizing
                4. Include transaction costs (0.1% typical)
                5. Test on out-of-sample data
                '''
            },
            {
                'heading': 'Key Metrics',
                'content': '''
                **Sharpe Ratio**: Risk-adjusted return (>1.0 good, >2.0 excellent)
                **Max Drawdown**: Largest peak-to-trough decline
                **Win Rate**: % of profitable trades (>50% good)
                **Profit Factor**: Gross profit / gross loss (>1.5 good)
                '''
            },
            {
                'heading': 'Avoiding Pitfalls',
                'content': '''
                 **Overfitting**: Don't optimize too many parameters
                 **Look-ahead bias**: Only use data available at decision time
                 **Survivorship bias**: Include delisted stocks
                 **Transaction costs**: Always include realistic costs
                '''
            },
        ]
    }
    
    REGIME_DETECTION = {
        'title': 'Market Regime Detection Help',
        'sections': [
            {
                'heading': 'What are Market Regimes?',
                'content': '''
                Markets cycle through different behavioral states:
                
                **Bull Market**: Rising prices, low volatility
                **Bear Market**: Falling prices, higher volatility  
                **Sideways**: Range-bound, low trend
                **Crisis**: High volatility, correlations → 1
                '''
            },
            {
                'heading': 'Hidden Markov Model (HMM)',
                'content': '''
                HMM automatically identifies regimes from return data.
                
                **Number of Regimes**: Start with 2-3
                - 2 regimes: Bull/Bear
                - 3 regimes: Bull/Bear/Sideways
                - 4+ regimes: More granularity
                '''
            },
            {
                'heading': 'Using Regime Information',
                'content': '''
                - **Regime-aware allocation**: Reduce risk in bear regime
                - **Transition monitoring**: Watch for regime shifts
                - **Strategy selection**: Different strategies per regime
                '''
            },
        ]
    }


def show_help_modal(content_key: str) -> None:
    """
    Display help modal for a specific feature.
    
    Args:
        content_key: Key from HelpContent attributes
    """
    content = getattr(HelpContent, content_key, None)
    
    if not content:
        st.error(f"Help content not found for: {content_key}")
        return
    
    # Create modal using expander
    with st.expander(" " + content['title'], expanded=False):
        for section in content['sections']:
            st.markdown(f"### {section['heading']}")
            st.markdown(section['content'])
            st.markdown("---")


def show_tooltip(text: str, help_text: str) -> None:
    """
    Display text with hover tooltip.
    
    Args:
        text: Main text to display
        help_text: Tooltip content
    """
    st.markdown(f"{text} ", help=help_text)


def show_info_box(title: str, content: str, type: str = "info") -> None:
    """
    Display informational box.
    
    Args:
        title: Box title
        content: Box content
        type: Box type (info, warning, success, error)
    """
    if type == "info":
        st.info(f"**{title}**\n\n{content}")
    elif type == "warning":
        st.warning(f"**{title}**\n\n{content}")
    elif type == "success":
        st.success(f"**{title}**\n\n{content}")
    elif type == "error":
        st.error(f"**{title}**\n\n{content}")


def show_quick_tips(tips: List[str]) -> None:
    """
    Display quick tips section.
    
    Args:
        tips: List of tip strings
    """
    with st.expander(" Quick Tips", expanded=False):
        for tip in tips:
            st.markdown(f"- {tip}")


def validate_input_with_feedback(
    value: float,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    recommended_range: Optional[tuple] = None,
    field_name: str = "Input"
) -> tuple[bool, str]:
    """
    Validate input and provide user feedback.
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        recommended_range: (min, max) recommended range
        field_name: Name of field for error messages
        
    Returns:
        (is_valid, message) tuple
    """
    # Check hard limits
    if min_val is not None and value < min_val:
        return False, f" {field_name} must be >= {min_val}"
    
    if max_val is not None and value > max_val:
        return False, f" {field_name} must be <= {max_val}"
    
    # Check recommended range
    if recommended_range:
        rec_min, rec_max = recommended_range
        if value < rec_min or value > rec_max:
            return True, f" {field_name} is outside recommended range ({rec_min}-{rec_max})"
    
    return True, f" {field_name} looks good"


def show_example_workflow(steps: List[dict]) -> None:
    """
    Display example workflow with steps.
    
    Args:
        steps: List of dicts with 'step', 'action', 'result' keys
    """
    with st.expander(" Example Workflow", expanded=False):
        for i, step_info in enumerate(steps, 1):
            st.markdown(f"**Step {i}: {step_info['step']}**")
            st.markdown(f" {step_info['action']}")
            if 'result' in step_info:
                st.markdown(f" {step_info['result']}")
            st.markdown("")


def show_progress_checklist(items: List[dict]) -> None:
    """
    Display progress checklist.
    
    Args:
        items: List of dicts with 'item', 'completed' keys
    """
    st.markdown("### Progress Checklist")
    
    for item in items:
        icon = "" if item.get('completed', False) else "⬜"
        st.markdown(f"{icon} {item['item']}")


class UserGuidance:
    """Contextual user guidance system."""
    
    @staticmethod
    def show_first_time_user_guide() -> None:
        """Show guide for first-time users."""
        if 'first_visit' not in st.session_state:
            st.session_state.first_visit = True
            
            st.info("""
             **Welcome to QuantLib Pro!**
            
            This appears to be your first visit. Here are some quick tips:
            
            1. **Start with Portfolio Optimization** to build optimal portfolios
            2. **Use Risk Analytics** to measure portfolio risk (VaR, stress tests)
            3. **Try Options Pricing** to value derivatives and calculate Greeks
            4. **Explore Advanced Analytics** for regime detection and correlation analysis
            
            Click the  icon on any page for detailed help.
            """)
    
    @staticmethod
    def show_feature_tour(feature: str, steps: List[str]) -> None:
        """Show interactive feature tour."""
        tour_key = f"tour_{feature}"
        
        if tour_key not in st.session_state:
            st.session_state[tour_key] = 0
        
        with st.expander(f" {feature} Tour", expanded=True):
            step = st.session_state[tour_key]
            
            if step < len(steps):
                st.markdown(f"**Step {step + 1}/{len(steps)}**")
                st.markdown(steps[step])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Previous", disabled=(step == 0)):
                        st.session_state[tour_key] -= 1
                        st.rerun()
                
                with col2:
                    if st.button("Next", disabled=(step == len(steps) - 1)):
                        st.session_state[tour_key] += 1
                        st.rerun()
            else:
                st.success(" Tour completed!")
                if st.button("Restart Tour"):
                    st.session_state[tour_key] = 0
                    st.rerun()
    
    @staticmethod
    def show_input_validation_help(field: str, current_value: any) -> None:
        """Show real-time input validation help."""
        validation_rules = {
            'volatility': {
                'range': (0.05, 1.0),
                'recommended': (0.15, 0.40),
                'help': 'Annual volatility. Most stocks: 15-40%. Tech stocks typically higher.'
            },
            'risk_free_rate': {
                'range': (0.0, 0.20),
                'recommended': (0.02, 0.06),
                'help': 'Risk-free rate. Use current T-Bill rate (typically 2-6%).'
            },
            'confidence_level': {
                'range': (0.80, 0.99),
                'recommended': (0.90, 0.99),
                'help': 'VaR confidence level. 95% is standard, 99% for conservative estimates.'
            },
        }
        
        if field in validation_rules:
            rules = validation_rules[field]
            
            if isinstance(current_value, (int, float)):
                rec_min, rec_max = rules['recommended']
                
                if current_value < rec_min:
                    st.warning(f" {current_value} is below typical range. {rules['help']}")
                elif current_value > rec_max:
                    st.warning(f" {current_value} is above typical range. {rules['help']}")
                else:
                    st.success(f" {current_value} is within typical range.")
