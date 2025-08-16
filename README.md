# China Super League Corner Prediction System

A sophisticated corner prediction system for China Super League matches using consistency-based analysis and historical data.

## 🎯 Project Status

**Current Phase**: Phase 1 - Foundation Setup (Days 1-2 Complete)

### ✅ Completed
- [x] Git repository initialization
- [x] Python virtual environment setup
- [x] Dependencies installation (Python 3.13 compatible)
- [x] Project structure creation
- [x] Basic Flask application setup
- [x] Configuration system
- [x] HTML templates (Base, Index, Accuracy Dashboard, Verification)
- [x] CSS and JavaScript foundation

### 🔄 Next Steps
- [ ] API-Football integration (Days 3-4)
- [ ] Database setup (Days 5-7)
- [ ] Data analysis engine (Phase 2)

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ (tested with Python 3.13.1)
- API-Football subscription key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd corners
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   - Copy `env.example` to `.env`
   - Add your API-Football key:
     ```
     API_FOOTBALL_KEY=your_actual_api_key_here
     ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   - Navigate to: `http://localhost:5000`

## 📊 System Architecture

### Core Components
- **Flask Web Application**: Main interface and API endpoints
- **API-Football Integration**: Real-time match and statistics data
- **SQLite Database**: Local storage for predictions and accuracy tracking
- **Consistency Analysis Engine**: Advanced corner prediction algorithms
- **Accuracy Tracking System**: Performance monitoring and validation

### Prediction Methodology
1. **Four-Metric Analysis**: Corners won/conceded for both teams
2. **Consistency Scoring**: Statistical reliability measurement
3. **Reliability Thresholds**: 90% confidence floor calculations
4. **Seasonal Tracking**: Current season vs all-time performance
5. **Confidence vs Accuracy Separation**: Clear distinction between prediction certainty and historical performance

## 🎯 Features

### Current (Phase 1)
- ✅ Responsive web interface
- ✅ System status monitoring
- ✅ Configuration management
- ✅ Error handling and logging

### Coming Soon (Phase 2)
- 🔄 China Super League data fetching
- 🔄 Corner prediction algorithms
- 🔄 Accuracy tracking system
- 🔄 Manual verification interface

### Planned (Phase 3+)
- 📅 Advanced visualizations
- 📅 Historical analysis reports
- 📅 Betting recommendations
- 📅 Mobile optimization

## 🔧 Configuration

### Environment Variables
```bash
API_FOOTBALL_KEY=your_api_key_here    # Required: API-Football subscription key
SECRET_KEY=your_secret_key            # Flask secret key
FLASK_DEBUG=True                      # Development mode
DATABASE_PATH=corners_prediction.db   # SQLite database path
```

### API Limits
- **Daily Calls**: 7,500
- **Per Minute**: 300
- **League Focus**: China Super League (ID: 169)

## 📈 Prediction Targets

- **Primary Goal**: 90% accuracy for high-confidence predictions
- **Secondary Goal**: 75% accuracy for medium-confidence predictions
- **Line Accuracy**: 80%+ on over 5.5 and 6.5 corner predictions
- **Tolerance**: ±1 corner considered correct

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=.
```

## 📝 Development Log

### Phase 1 - Day 1-2 (Completed)
- ✅ Project initialization and structure
- ✅ Flask application framework
- ✅ Basic UI templates and styling
- ✅ Configuration system
- ✅ Development environment setup

### Phase 1 - Day 3-4 (Next)
- 🔄 API-Football client implementation
- 🔄 Rate limiting and caching
- 🔄 China Super League data fetching
- 🔄 Error handling and retry logic

## 🤝 Contributing

This is currently a personal project following a structured development plan. The system is being built in phases with clear milestones and testing at each stage.

## 📄 License

Educational use only. Not for commercial gambling purposes.

## ⚠️ Disclaimer

This system is for educational and analytical purposes only. Always gamble responsibly and within your means. Past performance does not guarantee future results.

---

**Last Updated**: Phase 1, Days 1-2 Complete
**Next Milestone**: API Integration (Days 3-4)
