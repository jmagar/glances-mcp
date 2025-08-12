"""Knowledge base resources for Glances MCP server."""

import json
from datetime import datetime
from typing import Dict, List

from fastmcp import FastMCP


def register_knowledge_resources(app: FastMCP) -> None:
    """Register knowledge base resources with the MCP server."""
    
    @app.resource("glances://knowledge/runbooks")
    async def operational_runbooks() -> str:
        """Operational runbooks, best practices, and troubleshooting procedures."""
        runbooks = {
            "high_cpu_utilization": {
                "title": "High CPU Utilization Response",
                "severity": "medium",
                "symptoms": [
                    "CPU usage consistently above 80%",
                    "Application response time degradation",
                    "High system load averages",
                    "User complaints about system slowness"
                ],
                "investigation_steps": [
                    "1. Use get_top_processes to identify CPU-intensive processes",
                    "2. Check get_detailed_metrics for CPU breakdown (user vs system vs iowait)",
                    "3. Analyze process command lines and resource usage patterns",
                    "4. Review recent deployments or configuration changes",
                    "5. Check for runaway processes or infinite loops"
                ],
                "resolution_actions": [
                    "Kill or restart problematic processes (with business approval)",
                    "Adjust process priorities using nice/renice",
                    "Scale out workload to additional servers if available",
                    "Implement CPU throttling for non-critical processes",
                    "Schedule resource-intensive tasks for off-peak hours"
                ],
                "prevention": [
                    "Implement CPU usage monitoring and alerting",
                    "Regular performance testing of applications",
                    "Capacity planning and resource allocation reviews",
                    "Process resource limits and controls"
                ]
            },
            "memory_exhaustion": {
                "title": "Memory Exhaustion Response",
                "severity": "high",
                "symptoms": [
                    "Memory usage above 90%",
                    "Swap usage increasing rapidly",
                    "OOMKiller events in system logs",
                    "Application crashes or restarts"
                ],
                "investigation_steps": [
                    "1. Use get_detailed_metrics to analyze memory usage patterns",
                    "2. Identify memory-heavy processes with get_top_processes",
                    "3. Check for memory leaks in long-running applications",
                    "4. Review swap usage and thrashing indicators",
                    "5. Analyze memory allocation patterns and growth trends"
                ],
                "resolution_actions": [
                    "Restart memory-leaking applications",
                    "Clear caches and buffers where safe",
                    "Adjust application memory limits",
                    "Add more RAM if hardware capacity allows",
                    "Implement memory-based auto-scaling"
                ],
                "prevention": [
                    "Memory leak testing in development",
                    "Proper application memory configuration",
                    "Regular memory usage trend analysis",
                    "Automated memory alerts and responses"
                ]
            },
            "disk_space_full": {
                "title": "Disk Space Exhaustion Response",
                "severity": "critical",
                "symptoms": [
                    "Disk usage above 95%",
                    "Applications unable to write files",
                    "Database transaction log full",
                    "System unable to create temporary files"
                ],
                "investigation_steps": [
                    "1. Use get_disk_usage to identify full filesystems",
                    "2. Locate large files and directories consuming space",
                    "3. Check log file sizes and rotation policies",
                    "4. Identify any core dumps or temporary files",
                    "5. Review backup and archive processes"
                ],
                "resolution_actions": [
                    "Clean up log files and temporary directories",
                    "Remove old backup files and core dumps",
                    "Compress or archive large files",
                    "Move non-critical data to other filesystems",
                    "Extend filesystem or add additional storage"
                ],
                "prevention": [
                    "Implement disk space monitoring and alerting",
                    "Automated log rotation and cleanup",
                    "Regular disk usage reviews and cleanup",
                    "Capacity planning for storage growth"
                ]
            },
            "network_performance_issues": {
                "title": "Network Performance Issues",
                "severity": "medium", 
                "symptoms": [
                    "High network error rates",
                    "Packet drops or retransmissions",
                    "Network interface saturation",
                    "Application timeout errors"
                ],
                "investigation_steps": [
                    "1. Use get_network_stats to check interface statistics",
                    "2. Analyze error rates, dropped packets, and collisions",
                    "3. Check network utilization and bandwidth saturation",
                    "4. Review network configuration and routing",
                    "5. Test connectivity to dependent services"
                ],
                "resolution_actions": [
                    "Restart network interfaces if errors are high",
                    "Adjust network buffer sizes and TCP parameters",
                    "Redistribute network load across interfaces",
                    "Contact network team for infrastructure issues",
                    "Implement traffic shaping or QoS if needed"
                ],
                "prevention": [
                    "Network performance monitoring and baselines",
                    "Regular network configuration reviews",
                    "Redundant network paths for critical services",
                    "Network capacity planning and upgrades"
                ]
            },
            "container_issues": {
                "title": "Container Performance and Issues",
                "severity": "medium",
                "symptoms": [
                    "Container crashes or restarts",
                    "High container resource usage",
                    "Container networking issues",
                    "Image or volume problems"
                ],
                "investigation_steps": [
                    "1. Use get_containers to check container status and resources",
                    "2. Review container logs for errors or warnings",
                    "3. Check container resource limits and usage",
                    "4. Verify container networking and port mappings",
                    "5. Examine container image and volume health"
                ],
                "resolution_actions": [
                    "Restart problematic containers",
                    "Adjust container resource limits",
                    "Update container images to latest versions",
                    "Recreate containers with fresh configurations",
                    "Scale container deployments horizontally"
                ],
                "prevention": [
                    "Container resource monitoring and limits",
                    "Regular container image updates and security scanning",
                    "Container orchestration health checks",
                    "Backup and disaster recovery for container data"
                ]
            }
        }
        
        # General troubleshooting best practices
        best_practices = {
            "general_troubleshooting": {
                "methodology": [
                    "Define the problem clearly and gather symptoms",
                    "Check recent changes (deployments, configs, infrastructure)",
                    "Reproduce the issue in a controlled environment if possible", 
                    "Gather relevant logs, metrics, and diagnostic information",
                    "Form hypotheses about root causes",
                    "Test hypotheses systematically",
                    "Implement fix and verify resolution",
                    "Document findings and update procedures"
                ],
                "data_collection": [
                    "Always collect baseline metrics before making changes",
                    "Use multiple data sources (logs, metrics, traces)",
                    "Capture both current state and historical trends",
                    "Document timeline of events and changes",
                    "Preserve evidence for post-incident analysis"
                ]
            },
            "escalation_guidelines": {
                "when_to_escalate": [
                    "Issue not resolved within SLA timeframes",
                    "Multiple systems or services affected",
                    "Data integrity or security concerns",
                    "Need for emergency change approvals",
                    "Expertise required outside current team"
                ],
                "escalation_information": [
                    "Clear problem statement and business impact",
                    "Steps already taken and results",
                    "Current system state and metrics", 
                    "Proposed next steps or recommendations",
                    "Timeline constraints and dependencies"
                ]
            }
        }
        
        runbooks_resource = {
            "resource_info": {
                "uri": "glances://knowledge/runbooks",
                "name": "Operational Runbooks and Procedures",
                "description": "Comprehensive troubleshooting procedures and operational best practices",
                "type": "knowledge_base",
                "last_updated": datetime.now().isoformat(),
                "format": "JSON"
            },
            "runbooks": runbooks,
            "best_practices": best_practices,
            "usage_guidelines": {
                "procedure_execution": "Follow runbooks systematically, document deviations and outcomes",
                "customization": "Adapt procedures to your specific environment and requirements",
                "updates": "Keep runbooks current with infrastructure and process changes",
                "training": "Ensure team members are familiar with relevant runbooks"
            }
        }
        
        return json.dumps(runbooks_resource, indent=2)
    
    @app.resource("glances://knowledge/baselines")
    async def performance_baselines_knowledge() -> str:
        """Performance baselines, capacity planning data, and optimization guidance."""
        baselines_knowledge = {
            "performance_baselines": {
                "cpu_baselines": {
                    "typical_ranges": {
                        "web_servers": {"idle": "5-15%", "normal": "20-50%", "peak": "60-80%"},
                        "database_servers": {"idle": "10-20%", "normal": "30-60%", "peak": "70-90%"},
                        "application_servers": {"idle": "5-10%", "normal": "15-40%", "peak": "50-75%"},
                        "batch_processing": {"idle": "5-15%", "normal": "70-95%", "peak": "95-100%"}
                    },
                    "warning_indicators": [
                        "Sustained CPU usage above 80% for more than 15 minutes",
                        "High iowait (>20%) indicating storage bottlenecks",
                        "High steal time (>10%) in virtualized environments",
                        "Excessive context switching or interrupt handling"
                    ]
                },
                "memory_baselines": {
                    "typical_ranges": {
                        "web_servers": {"normal": "40-70%", "with_cache": "60-85%"},
                        "database_servers": {"normal": "60-85%", "cache_heavy": "80-95%"},
                        "application_servers": {"normal": "30-60%", "java_apps": "50-80%"}
                    },
                    "warning_indicators": [
                        "Memory usage consistently above 85%",
                        "Swap usage above 10% of physical memory",
                        "High page fault rates or memory pressure",
                        "Frequent garbage collection in managed runtimes"
                    ]
                },
                "storage_baselines": {
                    "typical_iops": {
                        "ssd": {"random_read": "10000-100000", "random_write": "5000-80000"},
                        "hdd": {"random_read": "100-200", "random_write": "100-200"},
                        "nvme": {"random_read": "100000-1000000", "random_write": "50000-500000"}
                    },
                    "latency_targets": {
                        "ssd": {"read": "<1ms", "write": "<1ms"},
                        "hdd": {"read": "<10ms", "write": "<10ms"},
                        "nvme": {"read": "<0.1ms", "write": "<0.1ms"}
                    }
                },
                "network_baselines": {
                    "error_rates": {
                        "acceptable": "<0.01%",
                        "concerning": "0.01-0.1%", 
                        "critical": ">0.1%"
                    },
                    "utilization": {
                        "normal": "<70%",
                        "peak_acceptable": "<85%",
                        "saturation": ">95%"
                    }
                }
            },
            "capacity_planning": {
                "growth_patterns": {
                    "typical_growth_rates": {
                        "cpu": "5-15% per quarter",
                        "memory": "10-25% per quarter",
                        "storage": "20-40% per quarter",
                        "network": "15-30% per quarter"
                    },
                    "seasonal_factors": [
                        "Business cycles and reporting periods",
                        "Holiday and promotional traffic spikes",
                        "Batch processing windows and data loads",
                        "Backup and maintenance schedules"
                    ]
                },
                "scaling_thresholds": {
                    "horizontal_scaling": {
                        "triggers": ["CPU >70% sustained", "Memory >80% sustained", "Response time degradation"],
                        "benefits": ["Better fault tolerance", "Linear performance scaling", "Cost efficiency"]
                    },
                    "vertical_scaling": {
                        "triggers": ["Memory-bound applications", "Single-threaded workloads", "Database workloads"],
                        "limitations": ["Single point of failure", "Hardware limitations", "Cost scaling"]
                    }
                }
            },
            "optimization_guidance": {
                "cpu_optimization": [
                    "Profile application code for hotspots and inefficiencies",
                    "Optimize algorithms and data structures",
                    "Use CPU affinity for performance-critical processes",
                    "Implement caching to reduce computational overhead",
                    "Consider multi-threading or async processing patterns"
                ],
                "memory_optimization": [
                    "Implement proper memory management and garbage collection tuning",
                    "Use memory profiling tools to identify leaks and excessive usage",
                    "Optimize data structures and reduce memory fragmentation",
                    "Implement object pooling and memory caching strategies",
                    "Configure appropriate heap and memory limits"
                ],
                "storage_optimization": [
                    "Use appropriate storage types for workload patterns",
                    "Implement proper indexing and query optimization",
                    "Use compression and deduplication where appropriate",
                    "Optimize I/O patterns and reduce random access",
                    "Implement proper backup and archival strategies"
                ],
                "network_optimization": [
                    "Optimize TCP parameters and buffer sizes",
                    "Use connection pooling and keep-alive connections",
                    "Implement proper load balancing and traffic distribution",
                    "Use compression and caching for network-transferred data",
                    "Monitor and optimize network topology and routing"
                ]
            }
        }
        
        recommendations = {
            "baseline_establishment": [
                "Collect at least 2 weeks of data before establishing baselines",
                "Account for business cycles and seasonal variations",
                "Update baselines quarterly or after major changes",
                "Use statistical methods (percentiles) rather than simple averages",
                "Maintain separate baselines for different workload types"
            ],
            "threshold_setting": [
                "Set warning thresholds 10-15% below critical levels",
                "Use trend-based alerting for gradual degradation",
                "Adjust thresholds based on business criticality",
                "Implement time-of-day and day-of-week threshold variations",
                "Regular review and adjustment of thresholds based on false positive rates"
            ]
        }
        
        baselines_resource = {
            "resource_info": {
                "uri": "glances://knowledge/baselines",
                "name": "Performance Baselines and Optimization Knowledge",
                "description": "Performance baseline data, capacity planning guidance, and optimization best practices",
                "type": "knowledge_base",
                "last_updated": datetime.now().isoformat(),
                "format": "JSON"
            },
            "baselines_knowledge": baselines_knowledge,
            "recommendations": recommendations,
            "application_guidance": {
                "baseline_usage": "Use these baselines as starting points, adjust based on your specific environment",
                "monitoring_setup": "Implement comprehensive monitoring before optimization efforts",
                "change_management": "Always baseline before and after changes to measure impact",
                "continuous_improvement": "Regular review and optimization should be part of operational procedures"
            }
        }
        
        return json.dumps(baselines_resource, indent=2)