# core/monitoring/api.py

import flask
from flask import Flask, jsonify
from flask_cors import CORS

from core.monitoring_system import get_monitoring_system

app = Flask(__name__)
CORS(app)  # Enable cross-origin requests

@app.route('/api/status', methods=['GET'])
def get_status():
    """Return the current system status."""
    monitoring_system = get_monitoring_system()
    return jsonify(monitoring_system.get_system_status())

@app.route('/api/resources', methods=['GET'])
def get_resources():
    """Return resource metrics."""
    monitoring_system = get_monitoring_system()
    return jsonify(monitoring_system.resource_monitor.metrics)

@app.route('/api/components', methods=['GET'])
def get_components():
    """Return component status."""
    monitoring_system = get_monitoring_system()
    return jsonify(monitoring_system.component_monitor.components)

@app.route('/api/performance', methods=['GET'])
def get_performance():
    """Return performance metrics."""
    monitoring_system = get_monitoring_system()
    return jsonify(monitoring_system.performance_monitor.metrics)

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Return system alerts."""
    monitoring_system = get_monitoring_system()
    return jsonify(monitoring_system.resource_monitor.alerts)

@app.route('/api/alerts//resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Resolve an alert."""
    monitoring_system = get_monitoring_system()
    # Implementation of resolve_alert would be needed in the monitoring system
    return jsonify({"success": True})

def start_api(host='0.0.0.0', port=5000):
    """Start the API server."""
    app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    start_api()
