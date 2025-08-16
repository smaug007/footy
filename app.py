"""
Main Flask application for China Super League corner prediction system.
"""
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from config import Config
from data.api_client import get_api_client, APIException
from data.database import get_db_manager
from data.data_importer import import_season, update_recent_statistics
from data.accuracy_tracker import get_system_overview
from data.data_processor import get_data_summary, import_more_corner_stats
from data.team_analyzer import analyze_team, compare_teams
from data.consistency_analyzer import predict_match_corners
from data.prediction_engine import predict_match_comprehensive, find_betting_opportunities
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
        try:
            season = request.args.get('season', 2024, type=int)
            
            # Get system accuracy overview
            accuracy_overview = get_system_overview(season)
            
            # Get database statistics
            db_manager = get_db_manager()
            db_stats = db_manager.get_database_stats()
            
            return jsonify({
                'status': 'success',
                'message': f'Accuracy statistics for season {season}',
                'data': {
                    'season': season,
                    'accuracy_overview': accuracy_overview,
                    'database_stats': {
                        'total_teams': db_stats.get('teams_count', 0),
                        'total_matches': db_stats.get('matches_count', 0),
                        'total_predictions': db_stats.get('predictions_count', 0),
                        'verified_results': db_stats.get('prediction_results_count', 0)
                    },
                    'available_seasons': db_stats.get('seasons', [])
                }
            })
            
        except Exception as e:
            app.logger.error(f'Error getting accuracy statistics: {e}')
            return jsonify({
                'status': 'error',
                'message': f'Failed to get accuracy statistics: {str(e)}',
                'data': {}
            }), 500
    
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
    
    @app.route('/api/team-analysis/<int:team_id>')
    def api_team_analysis(team_id):
        """Get comprehensive team corner analysis."""
        try:
            season = request.args.get('season', 2024, type=int)
            
            # Get team analysis
            team_analysis = analyze_team(team_id, season)
            
            if not team_analysis:
                return jsonify({
                    'status': 'error',
                    'message': f'Insufficient data for team analysis (need at least {Config.MIN_GAMES_FOR_PREDICTION} matches)',
                    'data': {}
                }), 404
            
            # Convert dataclass to dict for JSON serialization
            analysis_dict = {
                'team_id': team_analysis.team_id,
                'team_name': team_analysis.team_name,
                'season': team_analysis.season,
                'matches_analyzed': team_analysis.matches_analyzed,
                'analysis_date': team_analysis.analysis_date,
                
                'corners_won': {
                    'average': team_analysis.corners_won_avg,
                    'median': team_analysis.corners_won_median,
                    'std_dev': team_analysis.corners_won_std,
                    'min': team_analysis.corners_won_min,
                    'max': team_analysis.corners_won_max,
                    'consistency': team_analysis.corners_won_consistency,
                    'trend': team_analysis.corners_won_trend,
                    'reliability_90': team_analysis.corners_won_reliability_90,
                    'recent_form': team_analysis.corners_won_recent_form
                },
                
                'corners_conceded': {
                    'average': team_analysis.corners_conceded_avg,
                    'median': team_analysis.corners_conceded_median,
                    'std_dev': team_analysis.corners_conceded_std,
                    'min': team_analysis.corners_conceded_min,
                    'max': team_analysis.corners_conceded_max,
                    'consistency': team_analysis.corners_conceded_consistency,
                    'trend': team_analysis.corners_conceded_trend,
                    'reliability_90': team_analysis.corners_conceded_reliability_90,
                    'recent_form': team_analysis.corners_conceded_recent_form
                },
                
                'advanced_metrics': {
                    'home_away_split': team_analysis.home_away_split,
                    'vs_opponent_strength': team_analysis.vs_opponent_strength,
                    'monthly_trends': team_analysis.monthly_trends,
                    'form_analysis': team_analysis.form_analysis,
                    'prediction_difficulty': team_analysis.prediction_difficulty
                }
            }
            
            return jsonify({
                'status': 'success',
                'message': f'Team analysis for {team_analysis.team_name}',
                'data': analysis_dict
            })
            
        except Exception as e:
            app.logger.error(f'Error getting team analysis for team {team_id}: {e}')
            return jsonify({
                'status': 'error',
                'message': f'Failed to analyze team: {str(e)}',
                'data': {}
            }), 500
    
    @app.route('/api/team-comparison')
    def api_team_comparison():
        """Compare two teams' corner statistics."""
        try:
            team1_id = request.args.get('team1_id', type=int)
            team2_id = request.args.get('team2_id', type=int)
            season = request.args.get('season', 2024, type=int)
            
            if not team1_id or not team2_id:
                return jsonify({
                    'status': 'error',
                    'message': 'Both team1_id and team2_id parameters are required',
                    'data': {}
                }), 400
            
            # Get team comparison
            comparison = compare_teams(team1_id, team2_id, season)
            
            if 'error' in comparison:
                return jsonify({
                    'status': 'error',
                    'message': comparison['error'],
                    'data': {}
                }), 404
            
            return jsonify({
                'status': 'success',
                'message': f'Team comparison: {comparison["team1"]["name"]} vs {comparison["team2"]["name"]}',
                'data': comparison
            })
            
        except Exception as e:
            app.logger.error(f'Error comparing teams: {e}')
            return jsonify({
                'status': 'error',
                'message': f'Failed to compare teams: {str(e)}',
                'data': {}
            }), 500
    
    @app.route('/api/data-summary')
    def api_data_summary():
        """Get historical data summary."""
        try:
            season = request.args.get('season', 2024, type=int)
            
            # Get data summary
            data_summary = get_data_summary(season)
            
            return jsonify({
                'status': 'success',
                'message': f'Data summary for season {season}',
                'data': data_summary
            })
            
        except Exception as e:
            app.logger.error(f'Error getting data summary: {e}')
            return jsonify({
                'status': 'error',
                'message': f'Failed to get data summary: {str(e)}',
                'data': {}
            }), 500
    
    @app.route('/api/predict-match')
    def api_predict_match():
        """Generate corner prediction for a match."""
        try:
            home_team_id = request.args.get('home_team_id', type=int)
            away_team_id = request.args.get('away_team_id', type=int)
            season = request.args.get('season', 2024, type=int)
            
            if not home_team_id or not away_team_id:
                return jsonify({
                    'status': 'error',
                    'message': 'Both home_team_id and away_team_id parameters are required',
                    'data': {}
                }), 400
            
            # Generate comprehensive prediction
            prediction = predict_match_comprehensive(home_team_id, away_team_id, season)
            
            if not prediction:
                return jsonify({
                    'status': 'error',
                    'message': 'Insufficient data for prediction (need at least 3 matches per team)',
                    'data': {}
                }), 404
            
            # Convert prediction to dict for JSON serialization
            prediction_dict = {
                'match_info': {
                    'home_team': prediction.home_team_name,
                    'away_team': prediction.away_team_name,
                    'season': prediction.season
                },
                'predictions': {
                    'total_corners': prediction.predicted_total_corners,
                    'home_corners': prediction.predicted_home_corners,
                    'away_corners': prediction.predicted_away_corners,
                    'expected_range': {
                        'min': prediction.expected_total_range[0],
                        'max': prediction.expected_total_range[1]
                    },
                    'most_likely_outcome': prediction.most_likely_outcome
                },
                'line_predictions': {
                    'over_5_5': {
                        'prediction': prediction.over_5_5_prediction,
                        'confidence': prediction.over_5_5_confidence
                    },
                    'over_6_5': {
                        'prediction': prediction.over_6_5_prediction,
                        'confidence': prediction.over_6_5_confidence
                    },
                    'over_7_5': {
                        'prediction': prediction.over_7_5_prediction,
                        'confidence': prediction.over_7_5_confidence
                    }
                },
                'quality_metrics': {
                    'prediction_quality': prediction.prediction_quality,
                    'statistical_confidence': prediction.statistical_confidence,
                    'data_reliability': prediction.data_reliability,
                    'consistency_score': prediction.consistency_score
                },
                'team_analysis': {
                    'home_team_form': prediction.home_team_form,
                    'away_team_form': prediction.away_team_form
                },
                'analysis': {
                    'summary': prediction.analysis_summary,
                    'recommendation': prediction.recommendation
                }
            }
            
            return jsonify({
                'status': 'success',
                'message': f'Corner prediction for {prediction.home_team_name} vs {prediction.away_team_name}',
                'data': prediction_dict
            })
            
        except Exception as e:
            app.logger.error(f'Error generating match prediction: {e}')
            return jsonify({
                'status': 'error',
                'message': f'Failed to generate prediction: {str(e)}',
                'data': {}
            }), 500
    
    @app.route('/api/betting-opportunities')
    def api_betting_opportunities():
        """Find best betting opportunities from upcoming fixtures."""
        try:
            season = request.args.get('season', 2024, type=int)
            min_confidence = request.args.get('min_confidence', 70.0, type=float)
            
            # Get upcoming fixtures
            client = get_api_client()
            fixtures_response = client.get_upcoming_fixtures()
            fixtures = fixtures_response.get('response', [])
            
            if not fixtures:
                return jsonify({
                    'status': 'success',
                    'message': 'No upcoming fixtures found',
                    'data': {'opportunities': [], 'total_matches_analyzed': 0}
                })
            
            # Convert fixtures to match list (limit to avoid too many API calls)
            match_list = []
            db_manager = get_db_manager()
            
            for fixture in fixtures[:10]:  # Limit to first 10 fixtures
                teams_info = fixture.get('teams', {})
                home_api_id = teams_info.get('home', {}).get('id')
                away_api_id = teams_info.get('away', {}).get('id')
                
                if home_api_id and away_api_id:
                    # Get database team IDs
                    home_team = db_manager.get_team_by_api_id(home_api_id, season)
                    away_team = db_manager.get_team_by_api_id(away_api_id, season)
                    
                    if home_team and away_team:
                        match_list.append((home_team['id'], away_team['id']))
            
            if not match_list:
                return jsonify({
                    'status': 'success',
                    'message': 'No upcoming fixtures with sufficient team data',
                    'data': {'opportunities': [], 'total_matches_analyzed': 0}
                })
            
            # Find betting opportunities
            opportunities = find_betting_opportunities(match_list, season, min_confidence)
            
            return jsonify({
                'status': 'success',
                'message': f'Found {len(opportunities)} betting opportunities',
                'data': {
                    'opportunities': opportunities,
                    'total_matches_analyzed': len(match_list),
                    'min_confidence_threshold': min_confidence
                }
            })
            
        except Exception as e:
            app.logger.error(f'Error finding betting opportunities: {e}')
            return jsonify({
                'status': 'error',
                'message': f'Failed to find betting opportunities: {str(e)}',
                'data': {}
            }), 500
    
    @app.route('/api/import-data', methods=['POST'])
    def api_import_data():
        """Import or update season data."""
        try:
            data = request.get_json() or {}
            season = data.get('season', 2024)
            import_statistics = data.get('import_statistics', True)
            
            # Import season data
            if import_statistics:
                result = import_season(season, include_statistics=True)
            else:
                result = import_season(season, include_statistics=False)
            
            return jsonify({
                'status': 'success',
                'message': f'Successfully imported data for season {season}',
                'data': result
            })
            
        except Exception as e:
            app.logger.error(f'Error importing data: {e}')
            return jsonify({
                'status': 'error',
                'message': f'Failed to import data: {str(e)}',
                'data': {}
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
