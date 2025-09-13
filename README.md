# 🏈 China Super League Corner Prediction System

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-Educational-orange.svg)](#license)

A sophisticated corner and BTTS prediction system for China Super League matches using advanced statistical analysis and consistency-based algorithms.

## 🎯 Main Features

- **Corner Predictions** with Over 5.5/6.5 line analysis
- **BTTS Predictions** (Both Teams To Score) with probability analysis
- **Real-Time Fixtures** from API-Football integration
- **Team Analysis** with consistency and form evaluation
- **Prediction Interface** with confidence levels and recommendations

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+**
- **API-Football Subscription** (for fixture data)
- **Modern Web Browser**

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd corners
   ```

2. **Set up virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API Key**
   
   Edit `config.py` and update the API key:
   ```python
   API_FOOTBALL_KEY = 'your_api_key_here'
   ```

5. **Initialize Database**
   ```bash
   python -c "from data.database import get_db_manager; get_db_manager()"
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Open your browser**
   - Navigate to: `http://localhost:5000`
   - Start making predictions!

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Interface (Flask)                    │
├─────────────────────────────────────────────────────────────┤
│  Templates │  Static Assets │  API Routes │  Error Handling │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                  Prediction Engine                          │
├─────────────────────────────────────────────────────────────┤
│ Team Analysis │ Consistency │ H2H Analysis │ Confidence Calc │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                               │
├─────────────────────────────────────────────────────────────┤
│   API Client  │  Database   │   Storage   │   Validation    │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

```
├── app.py                         # Main Flask application
├── config.py                      # Configuration settings
├── requirements.txt               # Python dependencies
├── corners_prediction.db          # SQLite database
├── data/                          # Data processing modules
│   ├── api_client.py              # API-Football integration
│   ├── database.py                # Database operations
│   ├── prediction_engine.py       # Main prediction logic
│   ├── goal_analyzer.py           # BTTS prediction engine
│   ├── consistency_analyzer.py    # Consistency calculations
│   ├── head_to_head_analyzer.py   # H2H analysis
│   ├── team_analyzer.py           # Team statistics analysis
│   ├── accuracy_tracker.py        # Accuracy monitoring
│   └── prediction_storage.py      # Prediction storage
├── templates/                     # HTML templates
│   ├── base.html                  # Base template
│   └── index.html                 # Main prediction interface
└── static/                        # Static assets
    ├── css/style.css              # Custom styling
    └── js/main.js                 # JavaScript utilities
```

## 🔬 Prediction Methodology

### Advanced Statistical Analysis

#### 1. **Four-Metric Foundation**
```python
# Core metrics for each team:
- Corners Won (Home/Away splits)
- Corners Conceded (Home/Away splits)
- Weighted Recent Performance (last 5-10 games)
- Consistency Score (coefficient of variation)
```

#### 2. **Consistency Analysis**
```python
# Statistical reliability measures:
- Standard Deviation Analysis
- Coefficient of Variation (CV)
- 90% Confidence Intervals
- Trend Detection (linear regression)
```

#### 3. **BTTS Analysis**
```python
# Goal scoring probability:
- Team scoring rates (home/away)
- Defensive strength analysis
- Dynamic weight adjustment
- Venue-specific performance
```

## 🎮 Usage Guide

### Main Prediction Interface

1. **Fixtures Tab**: View upcoming matches with auto-generated predictions
2. **Custom Analysis Tab**: Select specific teams for detailed analysis
3. **System Performance**: View accuracy metrics and recent predictions

### Making Predictions

1. **From Fixtures**: Click "Predict" on any upcoming match
2. **Custom Teams**: Select home/away teams and generate prediction
3. **View Results**: Get corner totals, line predictions, and BTTS analysis

### Understanding Results

- **Total Corners**: Predicted match total
- **Over 5.5/6.5**: Confidence percentages for betting lines
- **BTTS**: Both Teams To Score probability
- **Quality Metrics**: Data reliability and confidence scores

## ⚙️ Configuration

### API Settings
```python
# config.py
API_FOOTBALL_KEY = 'your_api_key_here'
CHINA_SUPER_LEAGUE_ID = 169
API_CALLS_PER_DAY = 7500
API_CALLS_PER_MINUTE = 300
```

### Prediction Settings
```python
MIN_GAMES_FOR_PREDICTION = 3
MAX_GAMES_FOR_ANALYSIS = 20
TARGET_ACCURACY = 0.90
CORNER_TOLERANCE = 1  # ±1 corner considered correct
```

## 🛠️ Troubleshooting

### Common Issues

1. **API Key Invalid**: Update `API_FOOTBALL_KEY` in `config.py`
2. **No Fixtures**: Check internet connection and API limits
3. **Database Error**: Delete `corners_prediction.db` to recreate
4. **Import Error**: Run `pip install -r requirements.txt`

### Performance Tips

- **API Limits**: Monitor daily/minute call limits
- **Data Quality**: More historical data = better predictions
- **Browser**: Use modern browser for best experience

## 📊 File Structure

**Essential Files**: 20-25 files  
**Database Tables**: 6 normalized tables  
**API Endpoints**: 6 core endpoints for main page  
**Templates**: 2 HTML templates  
**JavaScript**: 2 JS files with utilities  

## 🔗 API Endpoints

Main page uses these endpoints:
- `/api/fixtures/upcoming` - Get upcoming matches
- `/api/teams` - Get team list for dropdowns
- `/api/predict` - Generate match predictions
- `/api/betting-opportunities` - High-confidence suggestions
- `/api/accuracy` - System performance metrics
- `/api/unverified-predictions` - Recent predictions

## 📝 License

This project is for educational purposes only. Always gamble responsibly and within your means.

---

**Status**: ✅ **PRODUCTION READY** - Main prediction interface fully functional!
