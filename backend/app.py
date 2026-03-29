from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from analyzer import FlipInsightAnalyzer

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variables
current_analyzer = None
current_df = None

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'FlipInsight API is running'})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload and process CSV/Excel file"""
    global current_analyzer, current_df
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Read the file
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            return jsonify({'error': 'Please upload CSV or Excel file'}), 400
        
        # Clean column names
        df.columns = df.columns.str.lower().str.strip()
        
        # Map common column names
        column_mapping = {
            'product_name': 'product_name', 'productname': 'product_name', 'name': 'product_name',
            'category': 'category', 'categories': 'category',
            'price': 'price', 'mrp': 'price', 'selling_price': 'price',
            'discount': 'discount_percentage', 'discount%': 'discount_percentage',
            'rating': 'rating', 'user_rating': 'rating',
            'reviews': 'review_count', 'review_count': 'review_count',
            'order_id': 'order_id', 'transaction_id': 'transaction_id', 'invoice_no': 'invoice_no',
            'cost_price': 'cost_price', 'cost': 'cost_price', 'buy_price': 'cost_price',
            'selling_price': 'selling_price', 'sell_price': 'selling_price',
            'quantity': 'quantity', 'qty': 'quantity',
            'order_date': 'order_date', 'purchase_date': 'order_date', 'date': 'date',
            'expenditure': 'expenditure', 'expense': 'expenditure', 'spend': 'expenditure'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns and new_col not in df.columns:
                df.rename(columns={old_col: new_col}, inplace=True)
        
        # Handle missing values
        if 'price' in df.columns:
            df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(df['price'].median())
        if 'selling_price' in df.columns:
            df['selling_price'] = pd.to_numeric(df['selling_price'], errors='coerce').fillna(df['selling_price'].median())
        if 'cost_price' in df.columns:
            df['cost_price'] = pd.to_numeric(df['cost_price'], errors='coerce').fillna(df['cost_price'].median())
        if 'discount_percentage' in df.columns:
            df['discount_percentage'] = pd.to_numeric(df['discount_percentage'], errors='coerce').fillna(0)
        if 'rating' in df.columns:
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(df['rating'].median())
        if 'quantity' in df.columns:
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(1)
        if 'expenditure' in df.columns:
            df['expenditure'] = pd.to_numeric(df['expenditure'], errors='coerce').fillna(0)
        
        # Create analyzer instance
        current_df = df
        current_analyzer = FlipInsightAnalyzer(df)
        
        # Perform analysis
        insights = current_analyzer.perform_eda()
        
        return jsonify({
            'success': True,
            'message': f'Successfully loaded {len(df)} rows with {len(df.columns)} columns',
            'insights': insights,
            'columns': list(df.columns),
            'row_count': len(df),
            'column_count': len(df.columns)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Answer questions about the data"""
    global current_analyzer
    
    if current_analyzer is None:
        return jsonify({'error': 'Please upload a dataset first'}), 400
    
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({'error': 'Please provide a question'}), 400
    
    try:
        answer = current_analyzer.answer_question(question)
        return jsonify({'answer': answer, 'question': question})
    except Exception as e:
        return jsonify({'error': f'Error processing question: {str(e)}'}), 500

@app.route('/api/insights', methods=['GET'])
def get_insights():
    """Get all insights without re-uploading"""
    global current_analyzer
    
    if current_analyzer is None:
        return jsonify({'error': 'No data loaded'}), 400
    
    try:
        insights = current_analyzer.perform_eda()
        return jsonify({'insights': insights})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 FlipInsight Backend Server Starting...")
    print("=" * 50)

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port, debug=False)
