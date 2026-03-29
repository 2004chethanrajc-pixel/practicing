from flask import Flask, request, jsonify, send_from_directory
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

# ================= API ROUTES ================= #

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'FlipInsight API is running'})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    global current_analyzer, current_df
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            return jsonify({'error': 'Please upload CSV or Excel file'}), 400
        
        df.columns = df.columns.str.lower().str.strip()

        column_mapping = {
            'productname': 'product_name', 'name': 'product_name',
            'categories': 'category',
            'mrp': 'price',
            'discount': 'discount_percentage', 'discount%': 'discount_percentage',
            'user_rating': 'rating',
            'reviews': 'review_count',
            'transaction_id': 'order_id', 'invoice_no': 'order_id',
            'cost': 'cost_price', 'buy_price': 'cost_price',
            'sell_price': 'selling_price',
            'qty': 'quantity',
            'purchase_date': 'order_date',
            'expense': 'expenditure', 'spend': 'expenditure'
        }

        for old_col, new_col in column_mapping.items():
            if old_col in df.columns and new_col not in df.columns:
                df.rename(columns={old_col: new_col}, inplace=True)

        # Handle missing values
        if 'price' in df.columns:
            df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(df['price'].median())
        if 'rating' in df.columns:
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(df['rating'].median())

        current_df = df
        current_analyzer = FlipInsightAnalyzer(df)

        insights = current_analyzer.perform_eda()

        return jsonify({
            'success': True,
            'message': f'Successfully loaded {len(df)} rows',
            'insights': insights
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ask', methods=['POST'])
def ask_question():
    global current_analyzer

    if current_analyzer is None:
        return jsonify({'error': 'Upload data first'}), 400

    data = request.json
    question = data.get('question', '')

    try:
        answer = current_analyzer.answer_question(question)
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/insights', methods=['GET'])
def get_insights():
    global current_analyzer

    if current_analyzer is None:
        return jsonify({'error': 'No data loaded'}), 400

    try:
        insights = current_analyzer.perform_eda()
        return jsonify({'insights': insights})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ================= FRONTEND ROUTES ================= #

FRONTEND_FOLDER = os.path.join(os.path.dirname(__file__), "../frontend")

@app.route("/")
def serve_frontend():
    return send_from_directory(FRONTEND_FOLDER, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(FRONTEND_FOLDER, path)


# ================= RUN APP ================= #

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)