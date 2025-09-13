# 🔌 API Documentation - CSL Corner Prediction System

## Overview

The China Super League Corner Prediction System provides a comprehensive REST API for accessing prediction data, team statistics, accuracy metrics, and system management functions.

**Base URL**: `http://localhost:5000/api`  
**Content-Type**: `application/json`  
**Authentication**: None required (local system)

---

## 📊 Core Prediction Endpoints

### Generate Match Prediction

**Endpoint**: `POST /api/predict`  
**Description**: Generate comprehensive corner prediction for a specific match

#### Request Body
```json
{
  "home_team_id": 123,
  "away_team_id": 456,
  "season": 2024
}
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `home_team_id` | integer | ✅ | ID of the home team |
| `away_team_id` | integer | ✅ | ID of the away team |
| `season` | integer | ❌ | Season year (default: current year) |

#### Response Format
```json
{
  "status": "success",
  "message": "Prediction generated for Team A vs Team B",
  "data": {
    "match_info": {
      "home_team": "Shanghai SIPG",
      "away_team": "Guangzhou FC",
      "season": 2024,
      "prediction_date": "2024-01-15T10:30:00Z"
    },
    "predictions": {
      "total_corners": 8.2,
      "home_corners": 4.8,
      "away_corners": 3.4,
      "expected_range": {
        "min": 6.5,
        "max": 10.1
      },
      "most_likely_outcome": "8-9 corners"
    },
    "line_predictions": {
      "over_5_5": {
        "prediction": "OVER",
        "confidence": 87.3,
        "recommendation": "BET"
      },
      "over_6_5": {
        "prediction": "OVER",
        "confidence": 74.1,
        "recommendation": "CONSIDER"
      },
      "over_7_5": {
        "prediction": "OVER",
        "confidence": 58.9,
        "recommendation": "AVOID"
      }
    },
    "quality_metrics": {
      "prediction_quality": "Excellent",
      "statistical_confidence": 89.2,
      "data_reliability": "High",
      "consistency_score": 82.4
    },
    "team_analysis": {
      "home_team_form": "Strong - 6.2 avg corners won",
      "away_team_form": "Moderate - 3.8 avg corners won"
    },
    "analysis": {
      "summary": "Detailed statistical analysis...",
      "recommendation": "Strong recommendation for Over 5.5 line",
      "methodology": "Based on weighted averages, consistency analysis..."
    }
  }
}
```

#### Error Response
```json
{
  "status": "error",
  "message": "Insufficient data for prediction (need at least 3 matches per team)",
  "data": {}
}
```

---

## 🎯 Team & Match Data Endpoints

### Get Teams List

**Endpoint**: `GET /api/teams`  
**Description**: Retrieve list of teams with basic information

#### Response Format
```json
{
  "status": "success",
  "message": "Teams retrieved successfully",
  "data": {
    "teams": [
      {
        "id": 123,
        "name": "Shanghai SIPG",
        "api_id": 1234,
        "season": 2024
      }
    ],
    "total_teams": 16
  }
}
```

### Get Team Analysis

**Endpoint**: `GET /api/team-analysis/<int:team_id>`  
**Description**: Get comprehensive analysis for a specific team

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `team_id` | integer | ✅ | Team ID in URL path |
| `season` | integer | ❌ | Season filter (query param) |

#### Response Format
```json
{
  "status": "success",
  "message": "Team analysis completed",
  "data": {
    "team_info": {
      "id": 123,
      "name": "Shanghai SIPG",
      "season": 2024
    },
    "corner_statistics": {
      "corners_won": {
        "average": 5.2,
        "median": 5.0,
        "std_dev": 1.8,
        "consistency": 78.5,
        "trend": "Increasing",
        "reliability_threshold": 3.5
      },
      "corners_conceded": {
        "average": 3.8,
        "median": 4.0,
        "std_dev": 1.2,
        "consistency": 82.1,
        "trend": "Stable",
        "reliability_threshold": 2.5
      }
    },
    "home_away_splits": {
      "home": {
        "corners_won_avg": 5.8,
        "corners_conceded_avg": 3.2
      },
      "away": {
        "corners_won_avg": 4.6,
        "corners_conceded_avg": 4.4
      }
    },
    "recent_form": {
      "last_5_games": {
        "corners_won_avg": 5.6,
        "form_rating": "Good"
      }
    },
    "prediction_difficulty": "Medium"
  }
}
```

### Compare Teams

**Endpoint**: `GET /api/team-comparison`  
**Description**: Compare two teams head-to-head

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `team1_id` | integer | ✅ | First team ID |
| `team2_id` | integer | ✅ | Second team ID |
| `season` | integer | ❌ | Season filter |

#### Response Format
```json
{
  "status": "success",
  "message": "Team comparison completed",
  "data": {
    "team1": {
      "name": "Shanghai SIPG",
      "corners_won_avg": 5.2,
      "consistency": 78.5
    },
    "team2": {
      "name": "Guangzhou FC",
      "corners_won_avg": 4.1,
      "consistency": 71.2
    },
    "head_to_head": {
      "total_meetings": 8,
      "avg_total_corners": 7.8,
      "home_advantage": 1.2
    },
    "recommendation": "Shanghai SIPG shows higher consistency"
  }
}
```

### Get Upcoming Fixtures

**Endpoint**: `GET /api/fixtures`  
**Description**: Get upcoming China Super League fixtures

#### Response Format
```json
{
  "status": "success",
  "message": "Fixtures retrieved successfully",
  "data": {
    "fixtures": [
      {
        "id": 789,
        "home_team": "Shanghai SIPG",
        "away_team": "Guangzhou FC",
        "date": "2024-01-20T07:30:00Z",
        "status": "NS"
      }
    ],
    "total_fixtures": 5
  }
}
```

---

## 📈 Accuracy & Performance Endpoints

### Get System Accuracy Overview

**Endpoint**: `GET /api/accuracy`  
**Description**: Get overall system accuracy metrics

#### Response Format
```json
{
  "status": "success",
  "message": "Accuracy data retrieved",
  "data": {
    "total_predictions": 247,
    "verified_predictions": 189,
    "overall_accuracy": 82.4,
    "over_5_5_accuracy": 85.2,
    "over_6_5_accuracy": 78.9,
    "over_7_5_accuracy": 71.3,
    "high_confidence_accuracy": 91.2,
    "accuracy_by_quality": {
      "excellent": 94.1,
      "good": 84.7,
      "fair": 72.3,
      "poor": 58.9
    },
    "recent_performance": {
      "last_30_days": 86.1,
      "trend": "Improving"
    }
  }
}
```

### Get Betting Opportunities

**Endpoint**: `GET /api/betting-opportunities`  
**Description**: Find high-confidence betting opportunities

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `min_confidence` | float | ❌ | Minimum confidence threshold (default: 70.0) |
| `season` | integer | ❌ | Season filter |

#### Response Format
```json
{
  "status": "success",
  "message": "Found 3 high-confidence opportunities",
  "data": {
    "opportunities": [
      {
        "match": "Shanghai SIPG vs Guangzhou FC",
        "line": "Over 5.5",
        "confidence": 87.3,
        "predicted_total": 8.2,
        "recommendation": "STRONG BET",
        "quality": "Excellent"
      }
    ],
    "total_opportunities": 3
  }
}
```

---

## 🔍 Verification & Management Endpoints

### Verify Match Result

**Endpoint**: `POST /api/verify-match/<int:match_id>`  
**Description**: Manually verify match results and update prediction accuracy

#### Request Body
```json
{
  "actual_home_corners": 6,
  "actual_away_corners": 3,
  "notes": "Regular match conditions"
}
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `match_id` | integer | ✅ | Match ID in URL path |
| `actual_home_corners` | integer | ✅ | Actual home team corners |
| `actual_away_corners` | integer | ✅ | Actual away team corners |
| `notes` | string | ❌ | Optional verification notes |

#### Response Format
```json
{
  "status": "success",
  "message": "Match 123 verified with 6-3 corners",
  "data": {
    "match_id": 123,
    "actual_result": {
      "home_corners": 6,
      "away_corners": 3,
      "total_corners": 9
    },
    "verification_results": [
      {
        "prediction_id": 456,
        "predicted_total": 8.2,
        "actual_total": 9,
        "error": 0.8,
        "within_tolerance": true,
        "line_accuracy": {
          "over_5_5": true,
          "over_6_5": true,
          "over_7_5": true
        }
      }
    ],
    "summary": {
      "total_predictions_verified": 1,
      "successful_verifications": 1,
      "average_error": 0.8
    }
  }
}
```

### Get Unverified Predictions

**Endpoint**: `GET /api/unverified-predictions`  
**Description**: Get list of predictions awaiting verification

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `season` | integer | ❌ | Season filter |
| `limit` | integer | ❌ | Results limit (default: 50) |

#### Response Format
```json
{
  "status": "success",
  "message": "Unverified predictions retrieved",
  "data": {
    "unverified_predictions": [
      {
        "id": 456,
        "match_info": {
          "home_team": "Shanghai SIPG",
          "away_team": "Guangzhou FC"
        },
        "predicted_total_corners": 8.2,
        "confidence_5_5": 87.3,
        "prediction_date": "2024-01-15T10:30:00Z",
        "quality": "Excellent"
      }
    ],
    "total_unverified": 12
  }
}
```

---

## 🛠️ System Management Endpoints

### Import Season Data

**Endpoint**: `POST /api/import-data`  
**Description**: Import team and match data for a season

#### Request Body
```json
{
  "season": 2024,
  "update_existing": false
}
```

#### Response Format
```json
{
  "status": "success",
  "message": "Data import completed successfully",
  "data": {
    "teams_imported": 16,
    "matches_imported": 240,
    "statistics_updated": 180,
    "import_duration": "45.2 seconds"
  }
}
```

### Get System Status

**Endpoint**: `GET /api/status`  
**Description**: Get API health and rate limit status

#### Response Format
```json
{
  "status": "success",
  "message": "System operational",
  "data": {
    "api_health": "Healthy",
    "rate_limits": {
      "calls_today": 1247,
      "daily_limit": 7500,
      "calls_this_minute": 3,
      "minute_limit": 300
    },
    "database": {
      "status": "Connected",
      "total_predictions": 247,
      "total_teams": 16
    },
    "cache": {
      "status": "Active",
      "cached_items": 45,
      "hit_rate": 78.3
    }
  }
}
```

### Get Data Summary

**Endpoint**: `GET /api/data-summary`  
**Description**: Get overview of available data quality

#### Response Format
```json
{
  "status": "success",
  "message": "Data summary generated",
  "data": {
    "season_2024": {
      "total_teams": 16,
      "teams_ready_for_analysis": 14,
      "total_matches": 240,
      "matches_with_corner_data": 180,
      "data_quality": "Good"
    },
    "recommendations": [
      "2 teams need more historical data",
      "60 matches missing corner statistics"
    ]
  }
}
```

---

## 🔍 Head-to-Head Analysis Endpoint

### Get Head-to-Head Analysis

**Endpoint**: `GET /api/head-to-head`  
**Description**: Get detailed head-to-head analysis between two teams

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `team1_id` | integer | ✅ | First team ID |
| `team2_id` | integer | ✅ | Second team ID |
| `seasons` | integer | ❌ | Number of seasons to analyze (default: 3) |

#### Response Format
```json
{
  "status": "success",
  "message": "Head-to-head analysis completed",
  "data": {
    "teams": {
      "team1": "Shanghai SIPG",
      "team2": "Guangzhou FC"
    },
    "historical_meetings": {
      "total_meetings": 12,
      "meetings_with_data": 10,
      "date_range": "2022-2024"
    },
    "corner_statistics": {
      "avg_total_corners": 7.8,
      "avg_home_corners": 4.2,
      "avg_away_corners": 3.6,
      "corner_range": [5.2, 10.4]
    },
    "consistency": {
      "h2h_consistency": 72.4,
      "reliability": "Medium"
    },
    "trends": {
      "recent_trend": "Increasing",
      "home_advantage_factor": 1.15
    },
    "prediction_adjustments": {
      "adjustment_factor": 0.85,
      "confidence_boost": 5.2
    }
  }
}
```

---

## 📊 Error Responses

### Standard Error Format
```json
{
  "status": "error",
  "message": "Description of what went wrong",
  "data": {},
  "error_code": "SPECIFIC_ERROR_CODE",
  "suggestions": [
    "Try selecting different teams",
    "Check if the API service is available"
  ]
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INSUFFICIENT_DATA` | 404 | Not enough historical data for analysis |
| `INVALID_TEAM_ID` | 400 | Team ID not found or invalid |
| `SAME_TEAMS` | 400 | Home and away teams cannot be the same |
| `API_RATE_LIMIT` | 429 | API rate limit exceeded |
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `INTERNAL_ERROR` | 500 | Internal server error |

---

## 🔒 Rate Limiting

The system implements intelligent rate limiting for API-Football requests:

- **Daily Limit**: 7,500 calls
- **Per Minute**: 300 calls
- **Caching**: 6-hour cache reduces API calls
- **Automatic Throttling**: Requests are automatically spaced to avoid limits

### Rate Limit Headers
```http
X-RateLimit-Daily-Remaining: 6253
X-RateLimit-Minute-Remaining: 297
X-Cache-Status: HIT
```

---

## 📝 Usage Examples

### Python Example
```python
import requests

# Generate prediction
response = requests.post('http://localhost:5000/api/predict', json={
    'home_team_id': 123,
    'away_team_id': 456,
    'season': 2024
})

prediction = response.json()
print(f"Predicted corners: {prediction['data']['predictions']['total_corners']}")
```

### JavaScript Example
```javascript
// Generate prediction
const response = await fetch('/api/predict', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        home_team_id: 123,
        away_team_id: 456,
        season: 2024
    })
});

const prediction = await response.json();
console.log(`Confidence for Over 5.5: ${prediction.data.line_predictions.over_5_5.confidence}%`);
```

### cURL Example
```bash
# Generate prediction
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"home_team_id": 123, "away_team_id": 456, "season": 2024}'

# Get system status
curl http://localhost:5000/api/status
```

---

## 🧪 Testing the API

### Health Check
```bash
curl http://localhost:5000/api/status
```

### Basic Prediction Test
```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"home_team_id": 1, "away_team_id": 2, "season": 2024}'
```

### Get Teams List
```bash
curl http://localhost:5000/api/teams
```

---

## 📚 Additional Resources

- **Interactive API Explorer**: Available at `/api-docs` when running the application
- **Postman Collection**: Available in the repository
- **OpenAPI Specification**: Available at `/api/openapi.json`

---

*This documentation is automatically updated with each system release.*
