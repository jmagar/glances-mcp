"""Reporting prompts for Glances MCP server."""

from fastmcp import FastMCP


def register_reporting_prompts(app: FastMCP) -> None:
    """Register reporting prompts with the MCP server."""
    
    @app.prompt("executive_dashboard")
    def executive_dashboard(
        time_period: str = "last_30_days",
        focus_areas: str = "availability_performance_costs",
        executive_level: str = "CTO"
    ) -> str:
        """High-level infrastructure overview with KPI tracking and business impact analysis."""
        return f"""You are creating an executive infrastructure dashboard for {executive_level} level consumption. Focus on business impact, strategic insights, and key performance indicators rather than technical details.

**REPORTING PARAMETERS:**
- Time Period: {time_period}
- Focus Areas: {focus_areas}
- Executive Audience: {executive_level}
- Report Type: Strategic Infrastructure Overview

**EXECUTIVE DASHBOARD FRAMEWORK:**

**Section 1: INFRASTRUCTURE HEALTH OVERVIEW**

*Key Performance Indicators:*
1. Use `list_servers` and `generate_health_score` to calculate fleet health percentage
2. Use `get_alert_summary` to determine system reliability metrics
3. Use `capacity_analysis` to assess resource adequacy
4. Use `performance_comparison` to establish performance trends

*Business-Critical Metrics:*
- **System Availability**: Overall uptime percentage and availability trends
- **Performance Index**: Composite performance score across all systems  
- **Capacity Utilization**: Resource utilization efficiency and planning status
- **Alert Health**: Ratio of resolved vs active critical issues

*Executive Summary Format:*
- Green/Yellow/Red status indicators for each area
- Percentage improvements or degradations vs previous period
- Key performance trends (improving, stable, declining)
- Business impact assessment (low, medium, high)

**Section 2: BUSINESS IMPACT ANALYSIS**

*Service Availability Impact:*
- Critical service uptime statistics
- User-impacting incident frequency and duration  
- Revenue impact from infrastructure issues
- SLA compliance metrics and trending

*Performance Impact on Business Operations:*
- Response time impacts on user experience
- Transaction processing capacity and trends
- Peak load handling effectiveness
- Business continuity readiness

*Cost Efficiency Metrics:*
- Infrastructure cost per business transaction
- Resource utilization efficiency trends
- Capacity planning cost avoidance
- Operational efficiency improvements

**Section 3: STRATEGIC INSIGHTS**

*Infrastructure Maturity Assessment:*
1. Use `compare_servers` to assess infrastructure standardization
2. Use `analyze_alert_patterns` to identify recurring issues
3. Use `predict_resource_needs` for strategic planning insights

*Key Strategic Observations:*
- Infrastructure scalability readiness
- Technology debt and modernization needs
- Automation and efficiency opportunities  
- Risk management effectiveness

*Future State Readiness:*
- Capacity to support business growth
- Technology architecture sustainability
- Operational scalability assessment
- Innovation enablement capability

**Section 4: RISK AND COMPLIANCE STATUS**

*Infrastructure Risk Assessment:*
- Critical single points of failure
- Disaster recovery readiness
- Security posture indicators
- Compliance status overview

*Business Continuity Metrics:*
- Recovery time objectives (RTO) compliance
- Recovery point objectives (RPO) compliance  
- Backup success rates and testing
- Incident response effectiveness

**Section 5: RESOURCE AND CAPACITY PLANNING**

*Current Resource Status:*
- Infrastructure utilization at-a-glance
- Capacity runway (time until expansion needed)
- Resource efficiency trends
- Cost optimization opportunities

*Strategic Capacity Planning:*
- 6-month and 12-month capacity projections
- Infrastructure investment timeline
- Cost implications of growth scenarios
- Technology refresh planning

**EXECUTIVE DELIVERABLES:**

**DASHBOARD OVERVIEW (1 PAGE)**

*Infrastructure Health Scorecard:*
```
System Availability:     ██████████ 99.8% ↗️
Performance Index:       ██████████ 94.2% ↗️  
Capacity Utilization:    ███████░░░ 72.1% →
Alert Resolution:        █████████░ 89.5% ↗️
```

*Key Performance Indicators:*
- **Uptime**: 99.8% (Target: 99.9%) - Meeting SLA requirements
- **Mean Time to Recovery**: 12 minutes (Target: <15 min) - Excellent
- **Capacity Runway**: 8 months at current growth - Planning required  
- **Cost Efficiency**: $0.34/transaction (Previous: $0.41) - Improved 17%

*Business Impact Summary:*
- Zero revenue-impacting incidents this period
- 15% improvement in application response times
- Prevented 2 capacity-related service impacts through proactive scaling
- Achieved $2.1M cost avoidance through optimization initiatives

**STRATEGIC RECOMMENDATIONS (Executive Actions)**

*Immediate Priorities (Next 90 Days):*
1. **Capacity Planning**: Initiate procurement for infrastructure expansion to support Q3 growth projections
2. **Risk Mitigation**: Address identified single points of failure in payment processing infrastructure  
3. **Cost Optimization**: Implement automated scaling to achieve additional 12% cost reduction

*Strategic Initiatives (Next 6-12 Months):*
1. **Infrastructure Modernization**: Plan cloud migration strategy for 40% cost reduction and improved agility
2. **Automation Enhancement**: Invest in infrastructure automation to reduce operational overhead by 30%
3. **Disaster Recovery**: Upgrade DR capabilities to achieve <5 minute RTO for critical systems

**FINANCIAL IMPACT ANALYSIS**

*Cost Performance:*
- Infrastructure costs vs budget: 94% of allocated budget utilized
- Cost per user trend: Decreased 8% while supporting 23% user growth
- Avoided costs through optimization: $2.1M this period
- Projected savings from planned initiatives: $4.2M annually

*Investment Requirements:*
- Q3 capacity expansion: $850K (already budgeted)
- Infrastructure modernization: $2.1M over 18 months
- Automation tooling: $450K initial investment, $1.2M annual savings

**RISK ASSESSMENT FOR EXECUTIVES**

*Critical Risk Areas:*
- **Capacity Risk**: Medium - 8 month runway requires action planning
- **Technology Risk**: Low - Current architecture scaling appropriately
- **Security Risk**: Low - All security controls operating effectively
- **Compliance Risk**: Low - Meeting all regulatory requirements

*Business Continuity Status:*
- Disaster recovery tested and verified monthly
- Backup systems achieving 100% success rate
- Incident response team trained and ready
- Business continuity plans updated and tested

**COMPARATIVE ANALYSIS**

*Industry Benchmarking:*
- Availability performance: Top 10% of industry peers
- Cost efficiency: 15% better than industry average
- Incident response: 40% faster than industry benchmark
- Capacity utilization: Optimal range (65-75% target achieved)

*Year-over-Year Improvements:*
- 24% reduction in critical incidents
- 18% improvement in system performance
- 12% reduction in infrastructure costs per transaction
- 35% improvement in incident resolution time

**ACTION ITEMS FOR EXECUTIVE TEAM**

*Decisions Required:*
1. **Budget Approval**: Q4 infrastructure expansion ($850K)
2. **Strategic Direction**: Cloud migration timeline and approach
3. **Investment Priority**: Automation vs manual process optimization
4. **Risk Tolerance**: Acceptable capacity runway before expansion

*Success Metrics to Track:*
- System availability trending toward 99.95%
- Mean time to recovery <10 minutes  
- Infrastructure cost per transaction <$0.30
- Capacity runway maintained at 6+ months

**NEXT PERIOD FOCUS AREAS**

*Key Monitoring Priorities:*
- Q3 peak season capacity readiness
- Infrastructure modernization project progress
- Cost optimization initiative results
- Security posture maintenance during growth

*Strategic Planning Items:*
- Multi-year infrastructure roadmap development
- Technology refresh planning and budgeting
- Disaster recovery capability enhancement
- Operational excellence program expansion

Present all data with clear business context, avoid technical jargon, focus on outcomes and business value. Use visual indicators (progress bars, trend arrows) and specific metrics that executives can use for decision-making."""

    @app.prompt("technical_deep_dive")
    def technical_deep_dive(
        analysis_focus: str = "performance_optimization",
        technical_domain: str = "infrastructure_engineering", 
        depth_level: str = "comprehensive"
    ) -> str:
        """Detailed technical analysis with performance optimization and architecture improvement suggestions."""
        return f"""You are a Principal Site Reliability Engineer conducting a comprehensive technical deep-dive analysis. Provide detailed technical insights, optimization opportunities, and architecture recommendations.

**ANALYSIS PARAMETERS:**
- Focus Area: {analysis_focus}
- Technical Domain: {technical_domain}
- Analysis Depth: {depth_level}
- Target Audience: Senior Technical Staff, Architecture Teams

**TECHNICAL ANALYSIS FRAMEWORK:**

**Section 1: COMPREHENSIVE SYSTEM ANALYSIS**

*Infrastructure Architecture Assessment:*
1. Use `list_servers` to map current infrastructure topology
2. Use `compare_servers` to analyze architectural consistency and patterns
3. Use `get_system_overview` and `get_detailed_metrics` for comprehensive resource profiling
4. Use `generate_health_score` for component-level health analysis

*Performance Characterization:*
- CPU utilization patterns and efficiency analysis
- Memory allocation, usage patterns, and optimization opportunities
- Storage I/O performance, bottlenecks, and optimization potential
- Network utilization, latency characteristics, and capacity planning

*Resource Utilization Deep Dive:*
- Per-core CPU utilization and scheduling analysis
- Memory hierarchy utilization (L1/L2/L3 cache implications)
- Storage subsystem analysis (IOPS, throughput, queue depths)
- Network interface utilization and protocol efficiency

**Section 2: PERFORMANCE OPTIMIZATION ANALYSIS**

*Current Performance Baseline:*
1. Use `performance_comparison` to establish performance baselines and trends
2. Use `detect_anomalies` to identify performance outliers and patterns
3. Use `get_top_processes` to analyze workload characteristics and resource consumption
4. Use `get_containers` to assess containerized workload efficiency

*Bottleneck Identification and Analysis:*

**CPU Performance Analysis:**
- Instruction mix and CPU efficiency metrics
- Context switching overhead and scheduling efficiency  
- NUMA topology utilization and memory locality
- CPU frequency scaling and power management impacts

**Memory Subsystem Analysis:**
- Memory bandwidth utilization and saturation points
- Page fault analysis and memory pressure indicators
- Buffer/cache effectiveness and tuning opportunities
- Memory fragmentation and allocation patterns

**Storage Performance Analysis:**
- Filesystem performance characteristics and optimization
- Block device queue depth and scheduler analysis
- Storage protocol efficiency (NVMe, SATA, network storage)
- I/O pattern analysis and optimization opportunities

**Network Performance Analysis:**  
- Protocol stack performance and optimization
- Network interface efficiency and driver optimizations
- Bandwidth utilization patterns and capacity planning
- Latency analysis and optimization opportunities

**Section 3: ARCHITECTURE OPTIMIZATION OPPORTUNITIES**

*Scalability Architecture Analysis:*
1. Use `capacity_analysis` and `predict_resource_needs` for scaling pattern analysis
2. Assess current architecture's ability to handle growth
3. Identify single points of failure and scaling bottlenecks
4. Analyze resource allocation efficiency across the fleet

*Microservice and Container Architecture:*
- Container resource allocation efficiency
- Service mesh performance and overhead analysis
- Load balancing effectiveness and optimization
- Inter-service communication optimization

*Data Architecture Performance:*
- Database query performance and optimization opportunities
- Caching strategy effectiveness and improvement potential
- Data pipeline performance and bottleneck analysis
- Storage architecture optimization for workload patterns

**Section 4: TECHNOLOGY STACK OPTIMIZATION**

*Operating System and Kernel Optimization:*
- Kernel parameter tuning opportunities
- System call overhead analysis and optimization
- Network stack tuning and performance enhancement
- File system selection and configuration optimization

*Application Runtime Optimization:*
- Runtime environment tuning (JVM, .NET, Python, etc.)
- Garbage collection optimization and impact analysis
- Thread pool and connection pool optimization
- Resource pooling and caching strategy optimization

*Infrastructure Software Optimization:*
- Load balancer configuration and algorithm optimization
- Reverse proxy performance and caching optimization  
- Message queue configuration and performance tuning
- Database configuration and query optimization

**Section 5: ADVANCED PERFORMANCE ENGINEERING**

*Performance Modeling and Prediction:*
- Workload characterization and performance modeling
- Capacity planning with performance degradation curves
- Response time distribution analysis and optimization
- Throughput optimization and scaling characteristics

*Observability and Performance Measurement:*
1. Use `analyze_alert_patterns` to identify measurement and monitoring gaps
2. Advanced metrics collection and analysis recommendations
3. Performance profiling strategy and implementation
4. Continuous performance regression detection

*Performance Testing and Validation:*
- Load testing strategy and infrastructure requirements
- Performance benchmark establishment and tracking
- Regression testing automation and alerting
- Capacity validation and stress testing procedures

**TECHNICAL DELIVERABLES:**

**PERFORMANCE ANALYSIS REPORT**

*System Performance Characteristics:*
```
CPU Utilization Profile:
- Average: 45.2% (Efficient)
- P95: 78.4% (Acceptable headroom)
- Peak: 94.1% (Transient spikes acceptable)
- Efficiency Score: 87/100 (Very good)

Memory Utilization Analysis:
- Working Set: 12.4 GB / 16 GB (77.5%)
- Cache Hit Ratio: 94.2% (Excellent)
- Page Fault Rate: 0.3/sec (Optimal)
- Memory Pressure Score: 15/100 (Low pressure)

Storage Performance Profile:
- IOPS: 8,540 (65% of maximum)
- Throughput: 890 MB/s (71% of maximum)  
- Average Latency: 2.4ms (Excellent)
- Queue Depth Utilization: 45% (Optimal)
```

*Performance Optimization Opportunities:*

**High-Impact Optimizations (30+ days to implement):**
1. **CPU Optimization**: Implement CPU affinity and NUMA-aware scheduling
   - Expected improvement: 12-15% performance gain
   - Implementation effort: 45 person-days
   - Risk level: Medium (requires testing)

2. **Memory Optimization**: Implement transparent huge pages and memory balancing
   - Expected improvement: 8-12% memory efficiency
   - Implementation effort: 20 person-days  
   - Risk level: Low

3. **Storage Optimization**: Implement NVMe over Fabrics for high-throughput workloads
   - Expected improvement: 40-60% I/O performance
   - Implementation effort: 60 person-days
   - Risk level: High (infrastructure change)

**Medium-Impact Optimizations (7-30 days to implement):**
1. **Network Tuning**: Optimize TCP window scaling and buffer sizes
2. **Application Tuning**: Implement connection pooling optimizations
3. **Caching Strategy**: Enhanced Redis configuration and clustering
4. **Load Balancing**: Algorithm optimization for workload patterns

**Quick Wins (1-7 days to implement):**
1. **Kernel Parameters**: TCP congestion control optimization
2. **File System**: Mount option optimization for performance
3. **Application Config**: JVM garbage collection tuning
4. **Monitoring**: Enhanced performance metric collection

**ARCHITECTURE IMPROVEMENT RECOMMENDATIONS**

*Scalability Architecture Enhancements:*

**Horizontal Scaling Improvements:**
- Implement stateless service design patterns
- Enhanced load balancing with health-aware routing
- Auto-scaling policies based on performance metrics
- Service mesh implementation for better traffic management

**Vertical Scaling Optimizations:**
- NUMA-aware memory allocation strategies
- CPU pinning for performance-critical workloads  
- Storage tiering for optimal cost/performance
- Network interface bonding and optimization

**Fault Tolerance and Resilience:**
- Circuit breaker pattern implementation
- Graceful degradation strategies
- Resource isolation and quotas
- Chaos engineering implementation

**PERFORMANCE ENGINEERING ROADMAP**

**Phase 1: Foundation (0-3 months)**
- Implement comprehensive performance monitoring
- Establish performance baselines and SLIs
- Deploy automated performance regression detection
- Create performance testing infrastructure

**Phase 2: Optimization (3-6 months)**  
- Execute high-impact performance optimizations
- Implement advanced caching strategies
- Deploy service mesh for traffic optimization
- Enhance database performance and scaling

**Phase 3: Advanced Engineering (6-12 months)**
- Implement predictive auto-scaling
- Deploy advanced observability and tracing
- Create performance-aware deployment strategies
- Establish continuous performance optimization

**TECHNICAL METRICS AND MONITORING**

*Performance KPIs:*
- Response time percentiles (P50, P95, P99)
- Throughput metrics (requests/second, transactions/second)
- Resource utilization efficiency ratios
- Error rates and performance impact correlation

*Advanced Observability:*
- Distributed tracing for end-to-end performance
- Custom metrics for business logic performance
- Performance regression detection automation
- Capacity planning with performance modeling

**IMPLEMENTATION STRATEGY**

*Risk Management:*
- Staged rollout with performance validation
- Rollback procedures for each optimization
- A/B testing for performance improvements
- Comprehensive testing in non-production environments

*Success Measurement:*
- Performance benchmark improvements
- Resource utilization efficiency gains
- Cost per transaction optimization
- User experience metric improvements

Focus on providing actionable technical recommendations with specific implementation guidance, expected outcomes, and risk assessments. Include detailed technical justifications and measurement strategies."""