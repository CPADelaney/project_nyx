# core/monitoring/cli.py

import argparse
import json
import sys
import os
from tabulate import tabulate
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.monitoring_system import get_monitoring_system

def format_timestamp(timestamp):
    """Format a timestamp for display."""
    return datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M:%S")

def display_system_status():
    """Display the current system status."""
    monitoring_system = get_monitoring_system()
    status = monitoring_system.get_system_status()
    
    print("\n=== System Status ===")
    print(f"Timestamp: {format_timestamp(status['timestamp'])}")
    print(f"System: {status['system']} {status['release']}")
    print("\n--- Resource Usage ---")
    print(f"CPU: {status['resources']['cpu']['percent']}%")
    print(f"Memory: {status['resources']['memory']['percent']}%")
    print(f"Disk: {status['resources']['disk']['percent']}%")
    
    print("\n--- Component Status ---")
    component_data = []
    for name, component in status["components"].items():
        component_data.append([
            name,
            component["status"],
            format_timestamp(component["last_check"]) if "last_check" in component else "N/A",
            component.get("errors", 0)
        ])
    
    print(tabulate(component_data, headers=["Component", "Status", "Last Check", "Errors"]))
    
    if status["alerts"]:
        print("\n--- Active Alerts ---")
        alert_data = []
        for alert in status["alerts"]:
            if alert["status"] == "active":
                alert_data.append([
                    alert["type"],
                    alert["message"],
                    alert["severity"],
                    format_timestamp(alert["timestamp"])
                ])
        
        print(tabulate(alert_data, headers=["Type", "Message", "Severity", "Timestamp"]))

def display_resources():
    """Display resource metrics."""
    monitoring_system = get_monitoring_system()
    metrics = monitoring_system.resource_monitor.metrics
    
    print("\n=== Resource Metrics ===")
    
    # Display CPU metrics
    print("\n--- CPU Usage ---")
    cpu_data = []
    for metric in metrics["cpu"][-10:]:  # Show last 10 entries
        cpu_data.append([
            format_timestamp(metric["timestamp"]),
            f"{metric['percent']}%"
        ])
    
    print(tabulate(cpu_data, headers=["Timestamp", "CPU %"]))
    
    # Display Memory metrics
    print("\n--- Memory Usage ---")
    memory_data = []
    for metric in metrics["memory"][-10:]:  # Show last 10 entries
        memory_data.append([
            format_timestamp(metric["timestamp"]),
            f"{metric['percent']}%",
            f"{metric['used'] / (1024 * 1024 * 1024):.2f} GB",
            f"{metric['total'] / (1024 * 1024 * 1024):.2f} GB"
        ])
    
    print(tabulate(memory_data, headers=["Timestamp", "Memory %", "Used (GB)", "Total (GB)"]))
    
    # Display Disk metrics
    print("\n--- Disk Usage ---")
    disk_data = []
    for metric in metrics["disk"][-10:]:  # Show last 10 entries
        disk_data.append([
            format_timestamp(metric["timestamp"]),
            f"{metric['percent']}%",
            f"{metric['used'] / (1024 * 1024 * 1024):.2f} GB",
            f"{metric['total'] / (1024 * 1024 * 1024):.2f} GB"
        ])
    
    print(tabulate(disk_data, headers=["Timestamp", "Disk %", "Used (GB)", "Total (GB)"]))

def display_components():
    """Display component status."""
    monitoring_system = get_monitoring_system()
    components = monitoring_system.component_monitor.components
    
    print("\n=== Component Status ===")
    component_data = []
    for name, component in components.items():
        component_data.append([
            name,
            component["status"],
            format_timestamp(component["last_check"]) if "last_check" in component else "N/A",
            component.get("errors", 0),
            component.get("last_error", "N/A")
        ])
    
    print(tabulate(component_data, headers=["Component", "Status", "Last Check", "Errors", "Last Error"]))

def display_performance():
    """Display performance metrics."""
    monitoring_system = get_monitoring_system()
    metrics = monitoring_system.performance_monitor.metrics
    
    print("\n=== Performance Metrics ===")
    
    # Display execution times
    print("\n--- Function Execution Times ---")
    execution_data = []
    for func, time in metrics["function_execution_times"].items():
        execution_data.append([func, f"{time:.4f}s"])
    
    print(tabulate(execution_data, headers=["Function", "Execution Time"]))
    
    # Display optimization success rate
    print(f"\nOptimization Success Rate: {metrics['optimization_success_rate']:.2f}%")
    
    # Display error rate
    print(f"Error Rate (per day): {metrics['error_rate']}")

def display_alerts():
    """Display system alerts."""
    monitoring_system = get_monitoring_system()
    alerts = monitoring_system.resource_monitor.alerts
    
    print("\n=== System Alerts ===")
    alert_data = []
    for alert in alerts:
        alert_data.append([
            alert["type"],
            alert["message"],
            alert["severity"],
            alert["status"],
            format_timestamp(alert["timestamp"])
        ])
    
    print(tabulate(alert_data, headers=["Type", "Message", "Severity", "Status", "Timestamp"]))

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Nyx Monitoring CLI")
    parser.add_argument("command", choices=["status", "resources", "components", "performance", "alerts"],
                        help="Command to execute")
    
    args = parser.parse_args()
    
    if args.command == "status":
        display_system_status()
    elif args.command == "resources":
        display_resources()
    elif args.command == "components":
        display_components()
    elif args.command == "performance":
        display_performance()
    elif args.command == "alerts":
        display_alerts()

if __name__ == "__main__":
    main()
