"""
Business Analytics Prompt Templates for Voice-Synchronized Visualizations
"""

SALES_PERFORMANCE_PROMPT = """
Analyze the sales performance data and create voice-synchronized visualizations. 

Data Context: {context}
Time Period: {time_period}
Key Metrics: {metrics}

Requirements:
1. Create a compelling narrative about sales trends
2. Highlight peak and low performance periods
3. Use appropriate highlight actions (pulse for peaks, focus for problems)
4. Include growth/decline percentages in your speech
5. Provide actionable insights and recommendations

Remember to:
- Mention specific time periods with precise timing for highlights
- Use color psychology (green for growth, red for decline)
- Create smooth speech flow with natural transitions
- Time highlights to align with speech mentions

Response format: JSON with speechText, speechMarkers, visualizations array
"""

FINANCIAL_DASHBOARD_PROMPT = """
Create a comprehensive financial dashboard with multiple synchronized visualizations.

Financial Data: {financial_data}
Key KPIs: {kpis}
Comparison Period: {comparison_period}

Create multiple visualizations:
1. Key metrics cards (revenue, profit, expenses)
2. Trend chart showing financial performance over time
3. Breakdown pie chart of expense categories

Speech requirements:
- Start with overall financial health summary
- Highlight specific metrics with appropriate timing
- Explain trends and patterns clearly
- Provide context for any unusual variations
- End with outlook and recommendations

Use presentation mode for executive-level reporting.
"""

MARKET_ANALYSIS_PROMPT = """
Perform market analysis with competitive insights and voice-synchronized charts.

Market Data: {market_data}
Competitors: {competitors}
Market Segments: {segments}

Visualization requirements:
1. Market share pie chart with competitor breakdown
2. Growth trends line chart over time
3. Segment performance bar chart
4. Key opportunity metrics

Speech strategy:
- Begin with market overview and size
- Highlight our position vs competitors (use zoom for emphasis)
- Discuss growth opportunities (use reveal for emerging segments)
- Focus on competitive advantages
- Conclude with strategic recommendations

Colors: Use brand colors where possible, competitive colors for market share
"""

CUSTOMER_INSIGHTS_PROMPT = """
Analyze customer behavior and satisfaction with interactive visualizations.

Customer Data: {customer_data}
Satisfaction Scores: {satisfaction_scores}
Behavioral Metrics: {behavioral_metrics}

Create visualizations for:
1. Customer satisfaction trends (line chart)
2. Demographics breakdown (pie chart)
3. Engagement metrics (bar chart)
4. Retention rates table

Speech approach:
- Start with overall customer health score
- Highlight positive trends and improvements
- Address any concerning patterns (use pulse for attention)
- Explain demographic insights
- Provide customer success recommendations

Timing: Allow extra time for metric explanations, use focus action for key insights
"""

OPERATIONAL_EFFICIENCY_PROMPT = """
Present operational metrics with efficiency-focused visualizations.

Operations Data: {operations_data}
Efficiency Metrics: {efficiency_metrics}
Cost Analysis: {cost_analysis}

Visualization strategy:
1. Efficiency trend charts showing improvement over time
2. Cost breakdown with variance analysis
3. Performance metrics dashboard
4. Bottleneck identification charts

Speech requirements:
- Begin with operational overview
- Highlight efficiency gains (use green colors and zoom action)
- Address cost concerns (use orange/red with focus action)
- Explain process improvements
- Recommend next optimization steps

Use data-driven storytelling to show operational journey
"""

PRODUCT_PERFORMANCE_PROMPT = """
Analyze product performance across different dimensions with synchronized visuals.

Product Data: {product_data}
Sales by Product: {sales_data}
Customer Feedback: {feedback_data}

Create comprehensive product analysis:
1. Product sales comparison (bar chart)
2. Performance trends over time (line chart)
3. Customer satisfaction by product (metrics)
4. Market position analysis (scatter plot)

Speech narrative:
- Start with portfolio overview
- Highlight top performers (use pulse action)
- Address underperforming products (use focus to draw attention)
- Explain customer feedback correlation
- Provide product strategy recommendations

Colors: Use distinct colors for each product line, maintain consistency
"""

GEOGRAPHIC_ANALYSIS_PROMPT = """
Present geographic performance data with location-based insights.

Geographic Data: {geographic_data}
Regional Performance: {regional_performance}
Market Penetration: {market_penetration}

Visualization approach:
1. Regional performance bar chart
2. Geographic trends over time
3. Market penetration metrics
4. Opportunity mapping table

Speech structure:
- Begin with geographic footprint overview
- Highlight strongest regions (use green highlights)
- Address expansion opportunities (use reveal action)
- Discuss regional challenges
- Recommend geographic strategy

Include regional comparisons and growth potential analysis
"""

def generate_prompt(template_type: str, **kwargs) -> str:
    """
    Generate a specific prompt based on template type and provided data.
    
    Args:
        template_type: Type of analysis prompt to generate
        **kwargs: Data context for the specific analysis
    
    Returns:
        Formatted prompt string ready for LLM
    """
    
    templates = {
        'sales_performance': SALES_PERFORMANCE_PROMPT,
        'financial_dashboard': FINANCIAL_DASHBOARD_PROMPT,
        'market_analysis': MARKET_ANALYSIS_PROMPT,
        'customer_insights': CUSTOMER_INSIGHTS_PROMPT,
        'operational_efficiency': OPERATIONAL_EFFICIENCY_PROMPT,
        'product_performance': PRODUCT_PERFORMANCE_PROMPT,
        'geographic_analysis': GEOGRAPHIC_ANALYSIS_PROMPT
    }
    
    if template_type not in templates:
        raise ValueError(f"Unknown template type: {template_type}")
    
    return templates[template_type].format(**kwargs)

# Example usage templates
EXAMPLE_CONTEXTS = {
    'sales_performance': {
        'context': 'Q1-Q4 2024 sales data across all product lines',
        'time_period': 'January 2024 - December 2024',
        'metrics': 'Total revenue, units sold, average order value, conversion rate'
    },
    
    'financial_dashboard': {
        'financial_data': 'Monthly P&L statements, cash flow, balance sheet items',
        'kpis': 'Revenue growth, profit margin, EBITDA, burn rate',
        'comparison_period': 'Year-over-year and quarter-over-quarter'
    },
    
    'market_analysis': {
        'market_data': 'Industry reports, competitor analysis, market sizing',
        'competitors': 'Top 5 direct competitors in the market',
        'segments': 'Enterprise, SMB, Consumer segments'
    }
}

def get_example_context(template_type: str) -> dict:
    """Get example context for a template type."""
    return EXAMPLE_CONTEXTS.get(template_type, {})