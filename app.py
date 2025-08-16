"""
Main Flask application for China Super League corner prediction system.
"""
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from config import Config
from data.api_client import get_api_client, APIException
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
        try:
            client = get_api_client()
            
            # Get upcoming fixtures (Not Started)
            upcoming_response = client.get_upcoming_fixtures()
            upcoming_fixtures = upcoming_response.get('response', [])
            
            # Format fixtures for frontend
            formatted_fixtures = []
            for fixture in upcoming_fixtures[:20]:  # Limit to 20 fixtures
                fixture_info = fixture.get('fixture', {})
                teams = fixture.get('teams', {})
                league = fixture.get('league', {})
                
                formatted_fixtures.append({
                    'id': fixture_info.get('id'),
                    'date': fixture_info.get('date'),
                    'home_team': {
                        'id': teams.get('home', {}).get('id'),
                        'name': teams.get('home', {}).get('name'),
                        'logo': teams.get('home', {}).get('logo')
                    },
                    'away_team': {
                        'id': teams.get('away', {}).get('id'),
                        'name': teams.get('away', {}).get('name'),
                        'logo': teams.get('away', {}).get('logo')
                    },
                    'venue': fixture_info.get('venue', {}).get('name'),
                    'status': fixture_info.get('status', {}).get('long')
                })
            
            return jsonify({
                'status': 'success',
                'message': f'Found {len(formatted_fixtures)} upcoming fixtures',
                'data': formatted_fixtures
            })
            
        except APIException as e:
            app.logger.error(f'API error getting fixtures: {e}')
            return jsonify({
                'status': 'error',
                'message': f'Failed to get fixtures: {str(e)}',
                'data': []
            }), 500
        except Exception as e:
            app.logger.error(f'Unexpected error getting fixtures: {e}')
            return jsonify({
                'status': 'error',
                'message': 'Internal server error',
                'data': []
            }), 500
    
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
        try:
            client = get_api_client()
            season = request.args.get('season', 2024, type=int)
            
            # Get CSL teams
            teams_response = client.get_china_super_league_teams(season)
            teams = teams_response.get('response', [])
            
            # Format teams for frontend
            formatted_teams = []
            for team in teams:
                team_info = team.get('team', {})
                venue_info = team.get('venue', {})
                
                formatted_teams.append({
                    'id': team_info.get('id'),
                    'name': team_info.get('name'),
                    'code': team_info.get('code'),
                    'logo': team_info.get('logo'),
                    'country': team_info.get('country'),
                    'founded': team_info.get('founded'),
                    'venue': {
                        'name': venue_info.get('name'),
                        'capacity': venue_info.get('capacity'),
                        'city': venue_info.get('city')
                    }
                })
            
            return jsonify({
                'status': 'success',
                'message': f'Found {len(formatted_teams)} teams for season {season}',
                'data': formatted_teams
            })
            
        except APIException as e:
            app.logger.error(f'API error getting teams: {e}')
            return jsonify({
                'status': 'error',
                'message': f'Failed to get teams: {str(e)}',
                'data': []
            }), 500
        except Exception as e:
            app.logger.error(f'Unexpected error getting teams: {e}')
            return jsonify({
                'status': 'error',
                'message': 'Internal server error',
                'data': []
            }), 500
    
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
    
    @app.route('/api/status')
    def api_status():
        """Get API and system status."""
        try:
            client = get_api_client()
            
            # Check API health
            is_healthy = client.health_check()
            rate_status = client.get_rate_limit_status()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'api_healthy': is_healthy,
                    'api_key_configured': bool(Config.API_FOOTBALL_KEY),
                    'rate_limits': rate_status,
                    'endpoints': {
                        'leagues': '/api/leagues' if is_healthy else 'unavailable',
                        'fixtures': '/api/fixtures' if is_healthy else 'unavailable', 
                        'teams': '/api/teams' if is_healthy else 'unavailable',
                        'statistics': 'available' if is_healthy else 'unavailable'
                    }
                }
            })
            
        except Exception as e:
            app.logger.error(f'Error getting API status: {e}')
            return jsonify({
                'status': 'error',
                'message': 'Failed to get API status',
                'data': {
                    'api_healthy': False,
                    'api_key_configured': bool(Config.API_FOOTBALL_KEY),
                    'error': str(e)
                }
            }), 500
    
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
