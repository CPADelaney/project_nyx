# Updated core/monitoring/api.py

import flask
from flask import Flask, jsonify, request
from flask_cors import CORS
import logging

from core.monitoring_system import get_monitoring_system
from core.auth.middleware import token_auth_required, api_key_auth_required, authenticate

app = Flask(__name__)
CORS(app)  # Enable cross-origin requests

logger = logging.getLogger("NYX-API")

# Add an authentication endpoint
@app.route('/api/auth/login', methods=['POST'])
def login():
    """Handle user authentication and token generation."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
        
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
        
    token = authenticate(username, password)
    if not token:
        return jsonify({"error": "Invalid credentials"}), 401
        
    return jsonify({"token": token})

@app.route('/api/auth/logout', methods=['POST'])
@token_auth_required
def logout():
    """Handle user logout and token invalidation."""
    auth_header = request.headers.get('Authorization')
    token = auth_header[7:]  # Remove 'Bearer ' prefix
    
    from core.auth.middleware import invalidate_token
    invalidate_token(token)
    
    return jsonify({"message": "Logged out successfully"})

# Apply token authentication to all API endpoints
@app.route('/api/status', methods=['GET'])
@token_auth_required
def get_status():
    """Return the current system status."""
    monitoring_system = get_monitoring_system()
    return jsonify(monitoring_system.get_system_status())

@app.route('/api/resources', methods=['GET'])
@token_auth_required
def get_resources():
    """Return resource metrics."""
    monitoring_system = get_monitoring_system()
    return jsonify(monitoring_system.resource_monitor.metrics)

@app.route('/api/components', methods=['GET'])
@token_auth_required
def get_components():
    """Return component status."""
    monitoring_system = get_monitoring_system()
    return jsonify(monitoring_system.component_monitor.components)

@app.route('/api/performance', methods=['GET'])
@token_auth_required
def get_performance():
    """Return performance metrics."""
    monitoring_system = get_monitoring_system()
    return jsonify(monitoring_system.performance_monitor.metrics)

@app.route('/api/alerts', methods=['GET'])
@token_auth_required
def get_alerts():
    """Return system alerts."""
    monitoring_system = get_monitoring_system()
    return jsonify(monitoring_system.resource_monitor.alerts)

@app.route('/api/alerts/<alert_id>/resolve', methods=['POST'])
@token_auth_required
def resolve_alert(alert_id):
    """Resolve an alert."""
    monitoring_system = get_monitoring_system()
    # Implementation of resolve_alert would be needed in the monitoring system
    return jsonify({"success": True})

# Also add a health check endpoint that doesn't require authentication
@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check that doesn't require authentication."""
    return jsonify({"status": "healthy"})

# Add error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.error(f"Server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

def start_api(host='127.0.0.1', port=5000):
    """Start the API server."""
    # Print the API key during development
    from core.auth.middleware import print_api_key
    print_api_key()
    
    app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_api()
