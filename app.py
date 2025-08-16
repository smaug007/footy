"""
Main Flask application for China Super League corner prediction system.
"""
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from config import Config
import logging

def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Enable CORS for API endpoints
    CORS(app)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO if not app.config['DEBUG'] else logging.DEBUG,
        format='%(asctime)s %(levelname)s: %(message)s'
    )
    
    # Validate configuration
    try:
        Config.validate_config()
        app.logger.info("Configuration validated successfully")
    except ValueError as e:
        app.logger.error(f"Configuration error: {e}")
        # For development, we'll continue without API key
        app.logger.warning("Continuing in development mode without API key")
    
    # Register routes
    register_routes(app)
    
    return app

def register_routes(app):
    """Register all application routes."""
    
    @app.route('/')
    def index():
        """Main page - fixture selection and prediction interface."""
        return render_template('index.html')
    
    @app.route('/accuracy-dashboard')
    def accuracy_dashboard():
        """Accuracy dashboard page."""
        return render_template('accuracy.html')
    
    @app.route('/verify-match/<int:match_id>')
    def verify_match(match_id):
        """Match verification page."""
        return render_template('verify.html', match_id=match_id)
    
    # API Routes
    @app.route('/api/fixtures')
    def api_fixtures():
        """Get upcoming CSL fixtures."""
        # TODO: Implement in Phase 1 Day 3-4
        return jsonify({
            'status': 'success',
            'message': 'API endpoint ready - implementation pending',
            'data': []
        })
    
    @app.route('/api/predict', methods=['POST'])
    def api_predict():
        """Generate match prediction."""
        # TODO: Implement in Phase 2
        return jsonify({
            'status': 'success',
            'message': 'Prediction endpoint ready - implementation pending',
            'data': {}
        })
    
    @app.route('/api/teams')
    def api_teams():
        """Get team statistics."""
        # TODO: Implement in Phase 2
        return jsonify({
            'status': 'success',
            'message': 'Teams endpoint ready - implementation pending',
            'data': []
        })
    
    @app.route('/api/accuracy')
    def api_accuracy():
        """Get accuracy statistics."""
        # TODO: Implement in Phase 2
        return jsonify({
            'status': 'success',
            'message': 'Accuracy endpoint ready - implementation pending',
            'data': {}
        })
    
    @app.route('/api/verify-match/<int:match_id>', methods=['POST'])
    def api_verify_match(match_id):
        """Manual match verification."""
        # TODO: Implement in Phase 2
        return jsonify({
            'status': 'success',
            'message': f'Verification endpoint ready for match {match_id} - implementation pending',
            'data': {}
        })
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        app.logger.error(f'Server Error: {error}')
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
