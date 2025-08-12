"""Troubleshooting prompts for Glances MCP server."""

from fastmcp import FastMCP


def register_troubleshooting_prompts(app: FastMCP) -> None:
    """Register troubleshooting prompts with the MCP server."""

    @app.prompt("incident_response_runbook")
    def incident_response_runbook(
        incident_type: str = "performance_degradation",
        severity: str = "high",
        affected_servers: str = "unknown"
    ) -> str:
        """Dynamic incident response procedures with context-aware troubleshooting steps."""
        return f"""You are a Senior Site Reliability Engineer leading incident response. Generate a comprehensive runbook for systematic incident investigation and resolution.

**INCIDENT CLASSIFICATION:**
- Incident Type: {incident_type}
- Severity Level: {severity}
- Affected Servers: {affected_servers}
- Response Time Target: {'< 15 minutes' if severity == 'critical' else '< 1 hour' if severity == 'high' else '< 4 hours'}

**INCIDENT RESPONSE FRAMEWORK:**

**Phase 1: IMMEDIATE ASSESSMENT (0-5 minutes)**

*Situation Assessment:*
1. Use `list_servers` to identify all monitored infrastructure
2. Use `get_server_status` for affected servers to verify accessibility
3. Use `check_alert_conditions` to get current alert status
4. Use `get_alert_summary` to understand alert patterns and trends

*Impact Assessment:*
- Determine scope of affected services
- Identify user/business impact
- Assess data integrity risks
- Evaluate cascading failure potential

*Initial Communication:*
- Notify stakeholders per severity escalation matrix
- Post initial status update
- Establish communication bridge if needed

**Phase 2: RAPID DIAGNOSIS (5-15 minutes)**

*System Health Check:*
1. Use `generate_health_score` for affected servers
2. Use `get_system_overview` to check resource utilization
3. Use `get_detailed_metrics` to examine CPU, memory, I/O in detail
4. Use `performance_comparison` to compare against recent baselines

*Resource Analysis by Priority:*

**If High CPU/Load:**
- Use `get_top_processes` to identify runaway processes
- Check for infinite loops or resource-intensive operations
- Examine process scheduling and priorities
- Consider immediate process termination if safe

**If Memory Issues:**
- Check for memory leaks in applications
- Examine swap usage and thrashing indicators
- Identify memory-heavy processes for potential restart
- Consider emergency memory management

**If Storage/I/O Issues:**
- Use `get_disk_usage` to check disk space critically low
- Examine I/O queue depths and wait times
- Identify processes causing heavy disk activity
- Check for filesystem corruption indicators

**If Network Issues:**
- Use `get_network_stats` to check error rates and utilization
- Verify network connectivity and routing
- Check for interface saturation or hardware issues

*Container/Service Analysis:*
- Use `get_containers` to check container health and resource usage
- Restart unhealthy containers if safe
- Examine container logs for error patterns

**Phase 3: STABILIZATION (15-30 minutes)**

*Immediate Mitigation Actions:*

**Performance/Resource Issues:**
- Kill runaway processes (with business approval)
- Restart services experiencing memory leaks
- Implement emergency rate limiting
- Activate traffic routing to healthy systems

**Storage Issues:**
- Emergency disk cleanup procedures
- Log rotation and cleanup
- Temporary file cleanup
- Consider temporary additional storage

**Network Issues:**
- Interface restart procedures
- Route table adjustments
- Traffic redirection to alternate paths

*Service Restoration:*
- Restart affected services in correct dependency order
- Verify service health after restart
- Confirm user accessibility restoration
- Update monitoring systems

**Phase 4: MONITORING & VALIDATION (30-60 minutes)**

*Stability Confirmation:*
1. Use `generate_health_score` to confirm improvement
2. Use `detect_anomalies` to verify metrics return to normal
3. Monitor alert conditions for new issues
4. Validate business function restoration

*Continuous Monitoring:*
- Set up enhanced monitoring for affected systems
- Increase alert sensitivity temporarily
- Schedule frequent health checks
- Monitor for incident recurrence

**Phase 5: COMMUNICATION & DOCUMENTATION**

*Stakeholder Updates:*
- Provide status updates at defined intervals
- Confirm service restoration to users
- Update incident tracking systems
- Schedule post-incident review

**INCIDENT-SPECIFIC PLAYBOOKS:**

**Performance Degradation:**
1. Resource utilization analysis (CPU, memory, I/O)
2. Process analysis and optimization
3. Historical comparison to identify changes
4. Gradual vs sudden performance change classification

**Service Outage:**
1. Service health verification
2. Dependency chain analysis
3. Configuration verification
4. Restart procedures with proper sequencing

**Resource Exhaustion:**
1. Immediate capacity relief measures
2. Resource cleanup procedures
3. Emergency scaling if available
4. Traffic reduction strategies

**Security Incident:**
1. System isolation procedures
2. Access logging examination
3. Integrity verification steps
4. Forensic preservation measures

**ESCALATION PROCEDURES:**

**When to Escalate:**
- Issue not resolved within target time
- Multiple systems affected simultaneously
- Data integrity concerns identified
- Require emergency change approvals

**Escalation Contacts:**
- On-call engineering manager
- Security team (for security incidents)
- Database team (for data issues)
- Network team (for connectivity issues)

**ROLLBACK PROCEDURES:**

*Change Rollback:*
- Identify recent changes from deployment logs
- Execute rollback procedures per change management
- Verify system stability post-rollback

*Configuration Rollback:*
- Restore known-good configurations
- Restart services with previous configurations
- Validate restoration of service functionality

**POST-INCIDENT ACTIONS:**

*Immediate Follow-up:*
- Use `analyze_alert_patterns` to understand incident patterns
- Document timeline and actions taken
- Preserve logs and metrics for analysis
- Schedule post-incident review meeting

*Prevention Planning:*
- Identify monitoring gaps exposed
- Plan infrastructure improvements
- Update alerting thresholds
- Enhance automation procedures

**VERIFICATION CHECKLIST:**

Before declaring incident resolved:
□ All critical alerts cleared
□ Health scores return to normal ranges
□ User functionality verified
□ Performance metrics within acceptable ranges
□ No new related alerts triggered
□ Stakeholders notified of resolution

**LESSONS LEARNED TEMPLATE:**

*What went well:*
- Effective detection and alerting
- Quick response and mitigation
- Good communication and coordination

*What could improve:*
- Earlier detection opportunities
- Faster resolution procedures
- Better preventive measures

*Action items:*
- Monitoring improvements
- Process enhancements
- Training needs
- Infrastructure changes

Focus on systematic approach with clear decision points and escalation criteria. Provide specific commands and verification steps for each action."""

    @app.prompt("maintenance_planning")
    def maintenance_planning(
        maintenance_type: str = "system_update",
        server_scope: str = "single_server",
        maintenance_window: str = "4_hours",
        risk_level: str = "medium"
    ) -> str:
        """Maintenance window planning with risk assessment and rollback procedures."""
        return f"""You are a Senior Site Reliability Engineer planning a maintenance operation. Create comprehensive procedures to ensure safe execution with minimal business impact.

**MAINTENANCE DETAILS:**
- Maintenance Type: {maintenance_type}
- Server Scope: {server_scope}
- Planned Window: {maintenance_window}
- Risk Assessment: {risk_level}

**PRE-MAINTENANCE PLANNING:**

**Phase 1: Impact Assessment**
1. Use `list_servers` to identify maintenance scope and dependencies
2. Use `compare_servers` to understand current workload distribution
3. Use `generate_health_score` to establish pre-maintenance baseline
4. Use `check_alert_conditions` to verify system stability

*Business Impact Analysis:*
- Services affected during maintenance
- User impact duration and scope
- Revenue impact estimation
- Compliance/SLA considerations

*Technical Dependencies:*
- Service dependency mapping
- Database connections and replication
- Load balancer configurations
- External integration impacts

**Phase 2: Risk Assessment and Mitigation**

*Risk Categories:*

**High Risk Factors:**
- Production database changes
- Network configuration modifications
- Kernel or OS updates
- Service architecture changes

**Medium Risk Factors:**
- Application updates with schema changes
- Configuration file modifications
- Hardware component replacement
- Security patch installation

**Low Risk Factors:**
- Static content updates
- Log rotation and cleanup
- Monitoring configuration updates
- Documentation updates

*Mitigation Strategies:*
- Staged rollout procedures
- Blue-green deployment options
- Database backup verification
- Configuration rollback procedures

**Phase 3: Pre-Maintenance Validation**

*System Health Verification:*
1. Use `generate_health_score` - all systems should score >70
2. Use `capacity_analysis` to ensure sufficient resources
3. Use `get_alert_summary` - no critical alerts should be active
4. Use `detect_anomalies` to identify any unusual patterns

*Backup and Recovery Readiness:*
- Complete system backups verified
- Database backups completed and tested
- Configuration snapshots taken
- Recovery procedures validated

*Team Readiness:*
- All maintenance team members confirmed
- Communication channels established
- Escalation contacts verified
- Emergency procedures reviewed

**MAINTENANCE EXECUTION PLAN:**

**Phase 1: Pre-Maintenance (T-30 minutes)**

*Communication:*
- Notify stakeholders of maintenance start
- Post maintenance notices
- Confirm team readiness

*System Preparation:*
1. Use `get_system_overview` to document pre-maintenance state
2. Use `get_detailed_metrics` to capture detailed baseline
3. Use `get_top_processes` to document running processes
4. Use `get_containers` to document container states

*Safety Measures:*
- Disable automated deployments
- Pause non-critical scheduled jobs
- Adjust monitoring sensitivity
- Prepare rollback artifacts

**Phase 2: Maintenance Window Execution**

*Maintenance Steps by Type:*

**System Updates:**
1. Stop affected services in proper dependency order
2. Apply updates following tested procedures
3. Restart services with health verification
4. Validate service functionality

**Configuration Changes:**
1. Create configuration backups
2. Apply changes with version control
3. Restart affected services
4. Verify configuration effectiveness

**Hardware Maintenance:**
1. Migrate workloads to redundant systems
2. Perform hardware maintenance
3. Validate hardware functionality
4. Migrate workloads back

*Continuous Monitoring During Maintenance:*
- Monitor system resource utilization
- Watch for unexpected errors or alerts
- Verify service startup success
- Check dependency service health

**Phase 3: Post-Maintenance Validation**

*System Health Verification:*
1. Use `generate_health_score` to verify system health restoration
2. Use `get_system_overview` to compare against pre-maintenance baseline
3. Use `check_alert_conditions` to verify no new alerts
4. Use `performance_comparison` to validate performance metrics

*Functional Testing:*
- Execute critical business function tests
- Verify all services are accessible
- Check database connectivity and queries
- Validate external integrations

*Performance Validation:*
- Compare response times to baseline
- Verify throughput metrics
- Check resource utilization patterns
- Monitor for any performance regressions

**ROLLBACK PROCEDURES:**

**Rollback Decision Criteria:**
- Critical functionality not restored within 30 minutes
- Performance degradation >25% from baseline
- Data integrity issues identified
- Critical alerts that cannot be resolved quickly

**Rollback Execution:**

**Application Rollback:**
1. Stop new version services
2. Restore previous version artifacts
3. Restart services with previous configuration
4. Verify functionality restoration

**Configuration Rollback:**
1. Restore previous configuration files
2. Restart affected services
3. Verify configuration effectiveness
4. Update related dependent configurations

**Database Rollback:**
1. Stop application connections
2. Restore database from backup
3. Verify data integrity
4. Restart application connections

*Post-Rollback Validation:*
- Verify system returns to pre-maintenance state
- Confirm all functionality restored
- Document rollback actions and timing
- Plan maintenance retry approach

**COMMUNICATION PLAN:**

**Stakeholder Notifications:**
- Pre-maintenance: T-24h, T-2h, T-30m
- During maintenance: Every 30 minutes or at milestone completion
- Post-maintenance: Success confirmation within 15 minutes
- Emergency escalation: Immediate for critical issues

**Status Page Updates:**
- Maintenance start confirmation
- Progress milestones
- Completion confirmation
- Any issues and resolution times

**MONITORING ENHANCEMENT:**

*Temporary Monitoring Adjustments:*
- Increase metric collection frequency
- Lower alert thresholds for early detection
- Enable detailed logging for maintenance period
- Set up additional dashboards for real-time monitoring

*Extended Monitoring Period:*
- Monitor for 24 hours post-maintenance
- Watch for delayed issues or regressions
- Gradual return to normal monitoring sensitivity
- Document any unusual patterns observed

**POST-MAINTENANCE DOCUMENTATION:**

*Maintenance Report:*
- Actual vs planned timeline
- Issues encountered and resolution
- System performance impact
- Lessons learned and improvements

*System Updates:*
- Update configuration management systems
- Document changes in service catalogs
- Update monitoring baselines if needed
- Refresh disaster recovery procedures

**CONTINUOUS IMPROVEMENT:**

*Process Evaluation:*
- Maintenance execution effectiveness
- Communication clarity and timing
- Risk mitigation success
- Team coordination efficiency

*Future Planning:*
- Update maintenance procedures based on lessons learned
- Enhance automation opportunities
- Improve rollback procedures
- Optimize maintenance window timing

Provide specific timelines, verification steps, and clear go/no-go decision criteria for each phase."""

    @app.prompt("security_assessment")
    def security_assessment(
        assessment_scope: str = "comprehensive",
        compliance_frameworks: str = "general_security",
        focus_areas: str = "system_hardening"
    ) -> str:
        """Security posture evaluation with vulnerability identification and hardening recommendations."""
        return f"""You are a Security Engineer conducting infrastructure security assessment. Perform comprehensive security evaluation using available monitoring data and system information.

**ASSESSMENT PARAMETERS:**
- Assessment Scope: {assessment_scope}
- Compliance Framework: {compliance_frameworks}
- Focus Areas: {focus_areas}

**SECURITY ASSESSMENT METHODOLOGY:**

**Phase 1: Infrastructure Inventory and Baseline**

*System Enumeration:*
1. Use `list_servers` to inventory all systems and their configurations
2. Use `get_system_overview` to identify OS versions, platforms, and architectures
3. Use `get_server_status` to verify system accessibility and health
4. Document environment classifications (production, staging, development)

*Service and Process Analysis:*
1. Use `get_top_processes` to identify all running services
2. Use `get_containers` to enumerate containerized applications
3. Use `get_network_connections` to map active network services
4. Document service exposure and attack surface

**Phase 2: Security Configuration Assessment**

*System Hardening Analysis:*

**Access and Authentication:**
- Review server access methods (SSH, console, remote management)
- Assess authentication mechanisms and policies
- Examine user account configurations and privileges
- Check for default accounts or weak credentials

**Network Security:**
- Use `get_network_stats` to analyze network interface configurations
- Review network segmentation and firewall rules
- Assess service exposure (listening ports and protocols)
- Check for unnecessary network services

**System Configuration:**
- Examine security-related system settings
- Review logging and auditing configurations
- Assess patch management status
- Check for security-related kernel parameters

**Process and Service Security:**
- Identify processes running with elevated privileges
- Assess service configurations for security best practices
- Review container security configurations
- Check for vulnerable service versions

**Phase 3: Vulnerability Assessment**

*Resource-Based Vulnerability Indicators:*

**Performance-Based Security Indicators:**
1. Use `detect_anomalies` to identify unusual resource consumption patterns
2. Use `performance_comparison` to detect deviations that might indicate compromise
3. Use `analyze_alert_patterns` to identify recurring issues that might indicate attacks
4. Look for unauthorized resource consumption or crypto-mining indicators

**System Resource Analysis:**
- Unusual CPU usage patterns (potential crypto-mining)
- Unexpected memory consumption (malware indicators)
- Abnormal network traffic patterns
- Suspicious disk I/O activity

**Alert Correlation for Security:**
- Frequent authentication failures
- Unusual access patterns
- Resource exhaustion attacks
- Service availability impacts

**Phase 4: Compliance Assessment**

*Security Controls Verification:*

**Logging and Monitoring:**
- Verify comprehensive logging is enabled
- Check log retention and protection
- Assess monitoring coverage and alert capabilities
- Review incident response readiness

**Access Controls:**
- Validate principle of least privilege implementation
- Check for proper privilege separation
- Assess administrative access controls
- Review service account configurations

**Data Protection:**
- Examine sensitive data exposure risks
- Assess encryption in transit and at rest
- Review backup security and access controls
- Check for data leakage indicators

**Change Management:**
- Review configuration management practices
- Assess deployment security procedures
- Check for unauthorized system changes
- Validate change tracking and approval

**SECURITY FINDINGS ANALYSIS:**

**Critical Security Issues:**
- Immediate threats requiring emergency response
- Active compromise indicators
- Critical vulnerabilities with known exploits
- Compliance violations with regulatory impact

**High-Risk Findings:**
- Significant security weaknesses
- Missing security controls
- Configuration vulnerabilities
- Elevated privilege risks

**Medium-Risk Observations:**
- Security hardening opportunities
- Best practice deviations
- Monitoring and alerting gaps
- Documentation deficiencies

**Low-Risk Recommendations:**
- Security enhancement opportunities
- Process improvements
- Training and awareness needs
- Documentation updates

**THREAT MODELING:**

*Attack Vector Analysis:*
- Network-based attack vectors
- Local privilege escalation risks
- Supply chain and dependency risks
- Social engineering vulnerabilities

*Asset Risk Assessment:*
- Critical asset identification and protection
- Data classification and handling
- Service availability requirements
- Business impact assessment

**HARDENING RECOMMENDATIONS:**

**Immediate Actions (0-7 days):**
- Critical vulnerability patching
- Emergency access control adjustments
- Immediate threat mitigation
- Security incident response activation

**Short-term Improvements (1-4 weeks):**
- Security configuration hardening
- Enhanced monitoring implementation
- Access control refinements
- Security process improvements

**Long-term Strategy (1-6 months):**
- Security architecture improvements
- Advanced security tool implementation
- Comprehensive security training
- Security automation development

**MONITORING AND DETECTION ENHANCEMENT:**

*Security Monitoring Improvements:*
- Enhanced alerting for security events
- Baseline establishment for anomaly detection
- Integration with security information systems
- Automated response capabilities

*Specific Monitoring Recommendations:*
1. Configure `detect_anomalies` for security-focused metrics
2. Set up `alert_patterns` analysis for attack pattern detection
3. Use `performance_comparison` to detect compromise indicators
4. Implement continuous `security_assessment` monitoring

**COMPLIANCE MAPPING:**

**General Security Framework:**
- Access control implementations
- Logging and monitoring coverage
- Change management processes
- Incident response capabilities

**Industry-Specific Requirements:**
- Regulatory compliance gaps
- Industry best practice adherence
- Audit readiness assessment
- Documentation requirements

**SECURITY METRICS AND KPIs:**

*Security Posture Metrics:*
- Vulnerability remediation times
- Security configuration compliance rates
- Security incident response times
- Security training completion rates

*Risk Metrics:*
- Critical vulnerability exposure time
- Mean time to security patch deployment
- Security alert resolution times
- Compliance score trends

**REMEDIATION ROADMAP:**

**Phase 1: Critical Risk Mitigation**
- Emergency security patches
- Critical configuration fixes
- Immediate access control adjustments
- Active threat response

**Phase 2: Security Enhancement**
- Comprehensive hardening implementation
- Enhanced monitoring deployment
- Security process optimization
- Team training and awareness

**Phase 3: Continuous Improvement**
- Advanced security capabilities
- Automation and orchestration
- Proactive threat hunting
- Security culture development

**VERIFICATION AND TESTING:**

*Security Control Testing:*
- Access control validation
- Security configuration verification
- Incident response procedure testing
- Disaster recovery security testing

*Continuous Assessment:*
- Regular security scanning
- Periodic vulnerability assessments
- Configuration drift detection
- Security metrics monitoring

Focus on actionable findings with clear risk levels, specific remediation steps, and measurable improvement metrics. Prioritize based on business risk and regulatory requirements."""
