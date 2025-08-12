"""System analysis prompts for Glances MCP server."""

from fastmcp import FastMCP


def register_analysis_prompts(app: FastMCP) -> None:
    """Register system analysis prompts with the MCP server."""
    
    @app.prompt("system_health_analysis")
    def system_health_analysis(server_alias: str = "all", include_trends: bool = True) -> str:
        """Generate comprehensive infrastructure health assessment with multi-server analysis."""
        return f"""You are an expert Site Reliability Engineer conducting a comprehensive infrastructure health assessment. 

**ANALYSIS SCOPE:**
- Target servers: {'All monitored servers' if server_alias == 'all' else f'Server: {server_alias}'}
- Include trend analysis: {include_trends}

**ANALYSIS FRAMEWORK:**
Use the following tools in sequence to build your assessment:

1. **Infrastructure Overview**
   - Use `list_servers` to get current server inventory and status
   - Use `get_system_overview` to collect basic metrics from all servers
   - Identify any servers that are unreachable or showing errors

2. **Health Score Analysis** 
   - Use `generate_health_score` to get comprehensive health scoring
   - Focus on servers with scores below 70 (concerning) or below 50 (critical)
   - Analyze component breakdowns (CPU, memory, disk, network, load)

3. **Alert Assessment**
   - Use `check_alert_conditions` to evaluate current alert status
   - Use `get_alert_summary` for alert patterns and trends
   - Prioritize critical alerts requiring immediate attention

4. **Performance Analysis**
   - Use `performance_comparison` to compare against historical baselines
   - Use `get_detailed_metrics` for servers showing performance degradation
   - Identify metrics significantly deviating from normal ranges

5. **Trend Analysis** (if include_trends is True)
   - Use `detect_anomalies` to identify unusual patterns
   - Look for consistent degradation trends across multiple servers
   - Assess whether issues are isolated or systemic

**DELIVERABLES:**

Provide a structured analysis with the following sections:

**EXECUTIVE SUMMARY**
- Overall infrastructure health status (Healthy/Warning/Critical)
- Number of servers assessed and any accessibility issues  
- Top 3 priority actions required
- Risk level assessment for business operations

**DETAILED FINDINGS**

*Critical Issues (Immediate Action Required):*
- List any critical alerts or health scores < 50
- Servers at risk of outage or severe performance impact
- Security or compliance concerns

*Performance Concerns (Monitoring/Planning Required):*
- Health scores 50-70, elevated resource usage
- Unusual trends or anomalies detected
- Capacity planning recommendations

*Infrastructure Health by Category:*
- CPU: Overall utilization, bottlenecks, iowait issues
- Memory: Usage patterns, swap activity, memory leaks
- Storage: Disk space, I/O performance, filesystem issues  
- Network: Throughput, errors, connectivity issues
- System Load: Load averages, process activity

**SERVER-SPECIFIC ANALYSIS**
For each server with issues:
- Current health score and component breakdown
- Active alerts and their severity
- Performance trends and anomalies
- Specific recommendations

**RECOMMENDATIONS**

*Immediate Actions (0-24 hours):*
- Critical issues requiring immediate intervention
- Emergency procedures or escalations needed

*Short-term Actions (1-7 days):*
- Performance optimizations
- Configuration adjustments
- Monitoring enhancements

*Medium-term Planning (1-4 weeks):*
- Capacity planning and resource upgrades
- Architecture improvements
- Process optimizations

*Long-term Strategy (1-6 months):*
- Infrastructure evolution
- Technology upgrades
- Scalability planning

**MONITORING RECOMMENDATIONS**
- Suggest additional monitoring or alert tuning
- Recommend baseline adjustments
- Identify gaps in observability

Focus on actionable insights that help operators understand both current health and trajectory. Use specific metrics, thresholds, and timeframes. Highlight correlations between servers or metrics that might indicate systemic issues."""

    @app.prompt("performance_troubleshooting") 
    def performance_troubleshooting(
        server_alias: str,
        issue_description: str = "general performance degradation",
        time_window: int = 24
    ) -> str:
        """Systematic performance issue investigation with root cause analysis methodology."""
        return f"""You are a Senior Site Reliability Engineer investigating a performance issue. Use systematic troubleshooting methodology to identify root causes and provide resolution steps.

**INCIDENT DETAILS:**
- Target server: {server_alias}
- Issue description: {issue_description}
- Investigation time window: {time_window} hours
- Timestamp: Current

**SYSTEMATIC INVESTIGATION PROCESS:**

**Phase 1: Initial Assessment**
1. Use `get_server_status` to verify server connectivity and basic health
2. Use `get_system_overview` to get current resource utilization snapshot
3. Use `generate_health_score` to assess overall system health
4. Use `check_alert_conditions` to identify any active alerts

**Phase 2: Resource Analysis**
Investigate each major resource category:

*CPU Analysis:*
- Use `get_detailed_metrics` with focus on CPU breakdown (user, system, iowait, steal)
- Check for high iowait (storage bottleneck indicator)
- Check for steal time (virtualization overhead)
- Analyze system vs user CPU usage patterns

*Memory Analysis:*  
- Examine memory usage, available memory, swap activity
- Look for memory leaks or unusual memory growth
- Check buffer/cache usage patterns

*Storage Analysis:*
- Use `get_disk_usage` to check disk space and utilization
- Examine I/O statistics for bottlenecks (queue depths, wait times)
- Identify filesystems approaching capacity limits

*Network Analysis:*
- Use `get_network_stats` to check for errors, dropped packets
- Look for bandwidth saturation or interface issues

**Phase 3: Process and Container Analysis**  
- Use `get_top_processes` to identify resource-intensive processes
- Use `get_containers` to examine container resource usage if applicable
- Correlate high resource usage with specific applications/services

**Phase 4: Historical and Trend Analysis**
- Use `performance_comparison` to compare current metrics against baselines
- Use `detect_anomalies` to identify unusual patterns
- Look for gradual degradation trends vs sudden changes

**Phase 5: Alert and Pattern Correlation**
- Use `get_alert_history` to examine recent alert patterns
- Use `analyze_alert_patterns` to identify recurring issues
- Correlate performance issues with recent alerts or changes

**TROUBLESHOOTING DECISION TREE:**

Follow this systematic approach based on findings:

**If CPU Usage > 80%:**
- Identify top CPU processes
- Check for runaway processes or infinite loops  
- Examine process nice levels and scheduling
- Consider CPU upgrade if sustained high usage

**If Memory Usage > 85%:**
- Identify memory-heavy processes
- Check for memory leaks in applications
- Examine swap usage and disk I/O correlation
- Consider memory upgrade if legitimate usage

**If High I/O Wait (>20%):**
- Check disk utilization and queue depths
- Identify I/O intensive processes
- Examine filesystem performance
- Consider storage subsystem issues

**If High Network Errors:**
- Check interface statistics
- Examine network configuration
- Look for bandwidth saturation
- Consider hardware or driver issues

**If High System Load but Low CPU:**
- Check for I/O bottlenecks
- Examine process states (blocked processes)
- Look for lock contention or resource waits

**DELIVERABLES:**

Provide structured troubleshooting report:

**ISSUE SUMMARY**
- Confirmed symptoms and impact assessment
- Affected resources and services
- Timeline of issue manifestation

**ROOT CAUSE ANALYSIS**
- Primary root cause identification
- Contributing factors
- Evidence supporting diagnosis
- Resource correlation analysis

**TECHNICAL FINDINGS**
- Current resource utilization details
- Baseline comparison and deviations
- Process/container analysis
- Historical trend analysis
- Alert correlation findings

**RESOLUTION STEPS**

*Immediate Actions:*
- Emergency mitigation steps
- Resource optimization opportunities
- Process management actions

*Short-term Fixes:*
- Configuration adjustments
- Application tuning
- Resource reallocation

*Long-term Solutions:*
- Infrastructure improvements
- Capacity planning
- Architecture optimization

**VERIFICATION STEPS**
- Metrics to monitor for improvement
- Success criteria for resolution
- Follow-up monitoring recommendations

**PREVENTION MEASURES**
- Monitoring enhancements to detect early
- Alert threshold adjustments
- Process improvements
- Documentation updates

Focus on data-driven analysis using specific metrics and thresholds. Provide clear correlation between symptoms and root causes. Include specific commands or tools for verification."""

    @app.prompt("capacity_planning_report")
    def capacity_planning_report(
        projection_months: int = 6,
        servers: str = "all",
        growth_assumptions: str = "current trends"
    ) -> str:
        """Long-term capacity planning analysis with growth projection modeling."""
        return f"""You are a Strategic Infrastructure Architect conducting comprehensive capacity planning analysis. Generate detailed projections and recommendations for resource planning.

**PLANNING PARAMETERS:**
- Projection timeframe: {projection_months} months
- Server scope: {servers}
- Growth modeling: {growth_assumptions}

**CAPACITY ANALYSIS METHODOLOGY:**

**Phase 1: Current State Assessment**
1. Use `list_servers` to inventory all infrastructure
2. Use `get_system_overview` to establish current utilization baseline
3. Use `generate_health_score` to assess current resource adequacy
4. Use `capacity_analysis` to evaluate current capacity utilization

**Phase 2: Resource Utilization Analysis**
- Use `get_detailed_metrics` for comprehensive resource inventory
- Use `get_disk_usage` for storage capacity assessment  
- Use `performance_comparison` to understand utilization trends
- Document current resource allocation and utilization patterns

**Phase 3: Growth Projection Modeling**
- Use `predict_resource_needs` with {projection_months * 30} day projection
- Use `detect_anomalies` to identify unusual growth patterns
- Use `compare_servers` to understand fleet-wide resource distribution
- Analyze trends for CPU, memory, storage, and network resources

**Phase 4: Risk and Constraint Analysis**
- Use `check_alert_conditions` to identify current bottlenecks
- Use `get_alert_history` to understand recurring capacity issues
- Identify single points of failure and resource constraints
- Assess business impact of capacity limitations

**DELIVERABLES:**

**EXECUTIVE SUMMARY**
- Current infrastructure capacity status
- Projected resource needs for next {projection_months} months
- Critical capacity decisions required
- Budget impact estimation
- Business risk assessment

**CURRENT STATE ANALYSIS**

*Infrastructure Inventory:*
- Server count and configurations
- Total compute, memory, and storage resources
- Current utilization percentages by resource type
- Resource distribution across environments

*Utilization Patterns:*
- Peak vs average resource consumption
- Seasonal or cyclical usage patterns  
- Resource efficiency analysis
- Workload distribution assessment

*Capacity Constraints:*
- Resources approaching limits (>80% utilization)
- Bottlenecks affecting performance
- Single points of failure
- Scalability limitations

**GROWTH PROJECTIONS**

*Demand Forecasting:*
- CPU utilization projections based on {growth_assumptions}
- Memory requirement growth modeling
- Storage capacity needs (data and system)
- Network bandwidth requirements

*Resource Timeline:*
- Month-by-month projected resource needs
- Critical threshold dates (when resources hit 80%, 90%, 95%)
- Seasonal adjustment factors
- Business event impact modeling

*Scenario Analysis:*
- Conservative growth (current trends continue)  
- Expected growth (planned business expansion)
- Aggressive growth (maximum growth scenarios)
- Risk scenarios (unexpected demand spikes)

**CAPACITY RECOMMENDATIONS**

*Immediate Actions (0-3 months):*
- Resources requiring immediate attention
- Quick wins for capacity optimization
- Alert threshold adjustments
- Performance tuning opportunities

*Short-term Planning (3-6 months):*
- Hardware procurement recommendations
- Resource upgrade priorities
- Configuration optimization
- Load balancing improvements

*Medium-term Strategy (6-12 months):*
- Infrastructure architecture evolution
- Scalability improvements
- Technology refresh planning
- Capacity automation initiatives

*Long-term Vision (12+ months):*
- Strategic technology decisions
- Cloud migration considerations
- Infrastructure modernization
- Scalability architecture

**FINANCIAL ANALYSIS**

*Cost Projections:*
- Hardware acquisition costs
- Operational expense impacts
- Cost per unit of capacity growth
- Budget timeline and milestones

*Cost Optimization:*
- Efficiency improvement opportunities
- Resource consolidation possibilities
- Technology refresh ROI analysis
- Operational cost reduction strategies

**RISK ASSESSMENT**

*Capacity Risks:*
- Resources likely to reach limits first
- Business impact of capacity exhaustion
- Single points of failure
- Performance degradation risks

*Mitigation Strategies:*
- Early warning systems and alerting
- Rapid provisioning procedures
- Emergency capacity procedures
- Business continuity planning

**IMPLEMENTATION ROADMAP**

*Phase 1 (Months 1-2):* Immediate capacity relief and optimization
*Phase 2 (Months 3-4):* Strategic capacity additions
*Phase 3 (Months 5-6):* Infrastructure improvements and efficiency gains

**MONITORING AND GOVERNANCE**

*Key Performance Indicators:*
- Capacity utilization thresholds
- Growth rate monitoring
- Performance benchmarks
- Cost efficiency metrics

*Review Processes:*
- Monthly capacity reviews
- Quarterly projection updates  
- Annual capacity planning cycles
- Trigger-based emergency planning

Focus on providing actionable recommendations with specific timelines, quantities, and business justification. Include confidence intervals for projections and alternative scenarios."""