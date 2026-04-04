from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import os
import json
import sys

# Add current directory to path for analyzer import
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from analyzer import FlipInsightAnalyzer
    analyzer_available = True
except ImportError as e:
    print(f"Warning: Could not import analyzer: {e}")
    print("Creating a mock analyzer for testing...")
    analyzer_available = False
    
    # Create a mock analyzer class for testing
    class MockFlipInsightAnalyzer:
        def __init__(self, df):
            self.df = df
            
        def perform_eda(self):
            return {
                "total_products": len(self.df),
                "total_categories": self.df['category'].nunique() if 'category' in self.df.columns else 0,
                "avg_price": self.df['price'].mean() if 'price' in self.df.columns else 0,
                "avg_rating": self.df['rating'].mean() if 'rating' in self.df.columns else 0,
                "avg_discount": self.df['discount_percentage'].mean() if 'discount_percentage' in self.df.columns else 0,
                "top_categories_by_revenue": {"Electronics": 100000, "Clothing": 80000, "Home": 60000} if 'category' in self.df.columns else {},
                "top_categories_by_rating": {"Electronics": 4.5, "Clothing": 4.2, "Home": 4.0} if 'category' in self.df.columns else {},
                "recommendations": [
                    "Increase marketing for top-performing categories",
                    "Consider bundling frequently purchased products",
                    "Review pricing strategy for low-rated products"
                ],
                "product_list": [
                    {"product_name": "Sample Product 1", "category": "Electronics", "price": 999, "rating": 4.5, "discount_percentage": 10, "sales": 100},
                    {"product_name": "Sample Product 2", "category": "Clothing", "price": 499, "rating": 4.2, "discount_percentage": 15, "sales": 150}
                ]
            }
            
        def answer_question(self, question):
            return f"This is a mock response to: '{question}'. In a real implementation, this would analyze your data."

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Global variables to store data
current_analyzer = None
current_insights = None
current_df = None

# Path to frontend folder
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), '../frontend')

# Serve frontend files
@app.route('/')
def serve_frontend():
    return send_from_directory(FRONTEND_PATH, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(FRONTEND_PATH, path)

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy", 
        "message": "FlipInsight API is running",
        "analyzer_available": analyzer_available
    })

# File upload endpoint
@app.route('/api/upload', methods=['POST'])
def upload_file():
    global current_analyzer, current_insights, current_df
    
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400
    
    try:
        # Read file based on extension
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            return jsonify({"success": False, "error": "Unsupported file format. Use CSV or Excel."}), 400
        
        # Normalize columns
        df = normalize_columns(df)
        
        # Create analyzer and get insights
        if analyzer_available:
            analyzer = FlipInsightAnalyzer(df)
        else:
            analyzer = MockFlipInsightAnalyzer(df)
            
        insights = analyzer.perform_eda()
        
        # Store globally
        current_df = df
        current_analyzer = analyzer
        current_insights = insights
        
        return jsonify({
            "success": True,
            "message": f"Successfully loaded {len(df):,} rows of data!",
            "insights": insights
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Question answering endpoint
@app.route('/api/ask', methods=['POST'])
def ask_question():
    global current_analyzer
    
    if not current_analyzer:
        return jsonify({"error": "No data loaded. Please upload a file first."}), 400
    
    data = request.get_json()
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    try:
        answer = current_analyzer.answer_question(question)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get current insights
@app.route('/api/insights', methods=['GET'])
def get_insights():
    global current_insights
    if current_insights:
        return jsonify(current_insights)
    return jsonify({"error": "No data loaded"}), 400

# Helper function to normalize columns
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.lower().str.strip()

    column_mapping = {
        "productname": "product_name",
        "name": "product_name",
        "categories": "category",
        "mrp": "price",
        "discount": "discount_percentage",
        "discount%": "discount_percentage",
        "user_rating": "rating",
        "reviews": "review_count",
        "transaction_id": "order_id",
        "invoice_no": "order_id",
        "cost": "cost_price",
        "buy_price": "cost_price",
        "sell_price": "selling_price",
        "qty": "quantity",
        "purchase_date": "order_date",
        "expense": "expenditure",
        "spend": "expenditure",
    }

    for old_col, new_col in column_mapping.items():
        if old_col in df.columns and new_col not in df.columns:
            df.rename(columns={old_col: new_col}, inplace=True)

    if "price" in df.columns:
        df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(df["price"].median() if not df["price"].isnull().all() else 0)
    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(df["rating"].median() if not df["rating"].isnull().all() else 0)

    return df

if __name__ == '__main__':
    print("=" * 60)
    print("Starting FlipInsight Flask Application...")
    print("=" * 60)
    print("\n📊 Application URLs:")
    print("  • Main Application: http://localhost:5000")
    print("  • API Health Check: http://localhost:5000/api/health")
    print("\n🚀 Features:")
    print("  • Serving frontend from: frontend/ folder")
    print("  • File upload (CSV/Excel) and automatic analysis")
    print("  • Interactive dashboard with KPIs and metrics")
    print("  • Business insights and recommendations")
    print("  • Market basket analysis")
    print("  • AI-powered question answering")
    print("\n⚙️  Status:")
    print(f"  • Analyzer available: {'✅ Yes' if analyzer_available else '⚠️ Using mock analyzer'}")
    print(f"  • Frontend path: {FRONTEND_PATH}")
    print("\n🛑 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(debug=True, port=5000, use_reloader=False)