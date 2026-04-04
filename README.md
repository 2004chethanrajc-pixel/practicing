# FlipInsight - E-commerce Intelligence & Analytics System

This project has two versions of the application:

## 1. Streamlit Version (Original)
**File:** `app.py`
- Complete Streamlit application with full UI
- Run with: `streamlit run app.py`
- Access at: `http://localhost:8501`

## 2. Flask + Frontend Version (Modified)
**Backend:** `backend/app.py` (Flask API)
**Frontend:** `frontend/` (HTML/CSS/JS)

### How to run Flask version:

1. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Run Flask backend:**
   ```bash
   python run_flask.py
   ```
   or
   ```bash
   cd backend
   python app.py
   ```

3. **Access the application:**
   - Frontend: `http://localhost:5000`
   - API endpoints: `http://localhost:5000/api/*`

### API Endpoints (Flask):

- `GET /api/health` - Health check
- `POST /api/upload` - Upload CSV/Excel file
- `POST /api/ask` - Ask questions about data

### Project Structure:

```
├── app.py                    # Streamlit version (unchanged)
├── run_flask.py             # Flask runner script
├── backend/
│   ├── app.py              # Flask API server
│   ├── analyzer.py         # Data analysis logic
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Main HTML page
│   ├── css/style.css      # Styles
│   └── js/script.js       # Frontend logic
└── sample_data.csv         # Sample dataset
```

### Features:
- Upload CSV/Excel files
- Automatic column normalization
- Key Performance Indicators (KPIs)
- Business insights and recommendations
- Market basket analysis
- Product filtering and sorting
- AI-powered question answering
- Interactive charts and visualizations

### Notes:
- The Streamlit version (`app.py`) remains unchanged as requested
- The Flask version uses the same backend analysis logic (`analyzer.py`)
- Both versions can be run independently
- Sample data file included for testing