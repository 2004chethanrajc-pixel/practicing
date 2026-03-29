import pandas as pd
import numpy as np
from itertools import combinations
from collections import Counter
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

class FlipInsightAnalyzer:
    def __init__(self, df):
        self.df = df
        self.label_encoders = {}
        self.rating_model = None
        self.sales_model = None
        
    def perform_eda(self):
        """Perform comprehensive EDA"""
        insights = {}

        price_col = 'price' if 'price' in self.df.columns else ('selling_price' if 'selling_price' in self.df.columns else None)
        
        # Basic statistics
        insights['total_products'] = int(len(self.df))
        insights['total_categories'] = int(self.df['category'].nunique()) if 'category' in self.df.columns else 0
        insights['avg_price'] = float(self.df[price_col].mean()) if price_col else 0
        insights['avg_discount'] = float(self.df['discount_percentage'].mean()) if 'discount_percentage' in self.df.columns else 0
        insights['avg_rating'] = float(self.df['rating'].mean()) if 'rating' in self.df.columns else 0
        
        # Revenue insights
        if 'category' in self.df.columns and price_col:
            category_revenue = self.df.groupby('category')[price_col].sum().sort_values(ascending=False)
            insights['top_categories_by_revenue'] = category_revenue.head(5).to_dict()
            
            if 'rating' in self.df.columns:
                category_rating = self.df.groupby('category')['rating'].mean().sort_values(ascending=False)
                insights['top_categories_by_rating'] = category_rating.head(5).to_dict()
        
        # Price band analysis
        if price_col:
            # Create price bands
            self.df['price_band'] = pd.cut(self.df[price_col], 
                bins=[0, 500, 1000, 2000, 5000, 10000, float('inf')], 
                labels=['Budget (<500)', 'Economy (500-1000)', 'Standard (1000-2000)', 
                       'Premium (2000-5000)', 'Luxury (5000-10000)', 'Ultra-Luxury (>10000)'])
            insights['price_band_distribution'] = self.df['price_band'].value_counts().to_dict()
            insights['avg_price_by_category'] = self.df.groupby('category')[price_col].mean().head(10).to_dict() if 'category' in self.df.columns else {}
        
        # Discount insights
        if 'discount_percentage' in self.df.columns:
            insights['avg_discount_by_category'] = self.df.groupby('category')['discount_percentage'].mean().head(10).to_dict() if 'category' in self.df.columns else {}
            
            if 'rating' in self.df.columns:
                high_discount = self.df[self.df['discount_percentage'] > 30]
                insights['high_discount_avg_rating'] = float(high_discount['rating'].mean()) if len(high_discount) > 0 else 0
        
        # Product segmentation
        insights['segmentation'] = self.segment_products()
        
        # Build models
        rating_model_result = self.build_rating_predictor()
        if rating_model_result:
            insights['rating_model'] = {
                'accuracy': rating_model_result['accuracy'],
                'rmse': rating_model_result['rmse'],
                'r2': rating_model_result['r2']
            }
        
        sales_model_result = self.build_sales_predictor()
        if sales_model_result:
            insights['sales_model'] = {
                'rmse': sales_model_result['rmse'],
                'mae': sales_model_result['mae'],
                'r2': sales_model_result['r2']
            }

        # Product list and top sellers
        product_list, top_sellers, sales_basis = self.get_product_list_and_top_sellers()
        insights['product_list'] = product_list
        insights['top_selling_products'] = top_sellers
        insights['sales_basis'] = sales_basis
        insights['product_sales'] = self.get_product_sales_series(sales_basis)

        # Recommendations
        insights['recommendations'] = self.generate_recommendations(sales_basis)
        insights['insights_explanation'] = self.get_insights_explanation(sales_basis)

        # Profit & loss insights
        insights['profit_loss'] = self.compute_profit_loss()
        insights['avg_annual_expenditure'] = self.compute_avg_annual_expenditure()

        # Association rules (market basket)
        association_result = self.compute_association_rules()
        insights['association_rules'] = association_result.get('rules', [])
        insights['association_meta'] = {
            'total_transactions': association_result.get('total_transactions', 0),
            'unique_products': association_result.get('unique_products', 0),
            'note': association_result.get('note', '')
        }
        insights['association_by_product'] = association_result.get('by_product', {})
        
        return insights
    
    def segment_products(self):
        """Segment products into Star, Hidden Gem, Declining, Dead Weight"""
        price_col = 'price' if 'price' in self.df.columns else ('selling_price' if 'selling_price' in self.df.columns else None)
        if 'rating' in self.df.columns and price_col:
            high_rating = self.df['rating'] >= 4.0
            low_rating = self.df['rating'] < 3.0
            median_price = self.df[price_col].median()
            high_price = self.df[price_col] > median_price
            low_price = self.df[price_col] <= median_price
            
            segmentation = {
                'Star Products (High Rating, High Price)': int(len(self.df[high_rating & high_price])),
                'Hidden Gems (High Rating, Low Price)': int(len(self.df[high_rating & low_price])),
                'Declining Products (Low Rating, High Price)': int(len(self.df[low_rating & high_price])),
                'Dead Weight (Low Rating, Low Price)': int(len(self.df[low_rating & low_price]))
            }
            return segmentation
        return {}
    
    def build_rating_predictor(self):
        """Build Random Forest model to predict product ratings"""
        price_col = 'price' if 'price' in self.df.columns else ('selling_price' if 'selling_price' in self.df.columns else None)
        if price_col and all(col in self.df.columns for col in ['discount_percentage', 'rating']):
            try:
                # Prepare features
                features = [price_col, 'discount_percentage']
                X = self.df[features].copy()
                y = self.df['rating'].copy()
                
                # Add category encoding if available
                if 'category' in self.df.columns:
                    le = LabelEncoder()
                    self.df['category_encoded'] = le.fit_transform(self.df['category'].astype(str))
                    features.append('category_encoded')
                    X = self.df[features].copy()
                    self.label_encoders['category'] = le
                
                # Handle any missing values
                X = X.fillna(X.mean())
                y = y.fillna(y.mean())
                
                # Split data
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                
                # Train model
                model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
                model.fit(X_train, y_train)
                
                # Evaluate
                y_pred = model.predict(X_test)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                r2 = r2_score(y_test, y_pred)
                
                self.rating_model = model
                
                return {
                    'model': model,
                    'accuracy': r2 * 100,
                    'rmse': float(rmse),
                    'r2': float(r2),
                    'features': features
                }
            except Exception as e:
                print(f"Rating model error: {e}")
                return None
        return None
    
    def build_sales_predictor(self):
        """Build Random Forest model for sales prediction"""
        price_col = 'price' if 'price' in self.df.columns else ('selling_price' if 'selling_price' in self.df.columns else None)
        if price_col and all(col in self.df.columns for col in ['rating', 'discount_percentage']):
            try:
                # Create synthetic sales volume based on rating, price, and discount
                np.random.seed(42)
                self.df['sales_volume'] = (
                    self.df['rating'] * np.random.uniform(500, 2000, len(self.df)) * 
                    (1 + self.df['discount_percentage']/100) * 
                    np.where(self.df[price_col] < 1000, 2, 1)
                ).astype(int)
                
                features = [price_col, 'discount_percentage', 'rating']
                X = self.df[features].copy()
                y = self.df['sales_volume'].copy()
                
                # Add category if available
                if 'category' in self.df.columns and 'category_encoded' in self.df.columns:
                    features.append('category_encoded')
                    X = self.df[features].copy()
                
                # Handle missing values
                X = X.fillna(X.mean())
                
                # Split data
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                
                # Train model
                model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
                model.fit(X_train, y_train)
                
                # Evaluate
                y_pred = model.predict(X_test)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                self.sales_model = model
                
                return {
                    'model': model,
                    'rmse': float(rmse),
                    'mae': float(mae),
                    'r2': float(r2)
                }
            except Exception as e:
                print(f"Sales model error: {e}")
                return None
        return None
    
    def generate_recommendations(self, sales_basis):
        """Generate business recommendations based on insights"""
        recommendations = []
        df = self.df

        if 'rating' in df.columns:
            low_rated = df[df['rating'] < 3.0]
            if len(low_rated) > 0:
                recommendations.append(
                    f"⚠️ {len(low_rated)} products have low ratings (<3.0). Improve quality, listings, or consider discontinuation."
                )
        
        if 'discount_percentage' in df.columns and 'rating' in df.columns:
            high_discount_low_rating = df[(df['discount_percentage'] > 30) & (df['rating'] < 3.5)]
            if len(high_discount_low_rating) > 0:
                recommendations.append(
                    f"📊 {len(high_discount_low_rating)} products have high discount but low rating. Review quality or positioning."
                )
        
        price_col = 'price' if 'price' in df.columns else ('selling_price' if 'selling_price' in df.columns else None)
        if price_col and 'rating' in df.columns:
            high_rating_products = df[df['rating'] >= 4.0]
            if len(high_rating_products) > 0:
                optimal_price = high_rating_products[price_col].median()
                recommendations.append(
                    f"💰 Price anchor: high-rated products cluster around ₹{optimal_price:,.0f}. Keep new launches near this band."
                )
        
        if 'category' in df.columns and 'rating' in df.columns:
            best_category = df.groupby('category')['rating'].mean().idxmax()
            worst_category = df.groupby('category')['rating'].mean().idxmin()
            recommendations.append(f"🏆 Best performing category: {best_category}")
            recommendations.append(f"📉 Category needing improvement: {worst_category}")

        if sales_basis != 'unavailable':
            recommendations.append(
                f"📈 Top sellers are based on {sales_basis}. Use these items for bundles, ads, and cross-sell placement."
            )
        
        if not recommendations:
            recommendations.append("✅ Your data looks good! Upload more data for detailed insights.")
        
        return recommendations

    def get_insights_explanation(self, sales_basis):
        """Explain how suggestions are generated and what they are based on."""
        lines = []
        lines.append("How suggestions are generated:")
        lines.append("• Ratings: We flag low-rated products (<3.0) because they usually drive returns or poor reviews.")
        lines.append("• Discounts vs Ratings: High discounts with low ratings often indicate quality or expectation gaps.")
        lines.append("• Price Anchor: We find the median price of high-rated products to suggest a strong pricing band.")
        lines.append("• Category Performance: We compare average ratings per category to spot winners and underperformers.")
        if sales_basis == 'sales_volume':
            lines.append("• Top sellers are derived from the synthetic sales volume model based on rating, price, and discount.")
        elif sales_basis == 'review_count':
            lines.append("• Top sellers are inferred from review counts (as a proxy for demand).")
        else:
            lines.append("• Top sellers are unavailable because no sales or review signals were found.")
        return "\n".join(lines)
    
    def answer_question(self, question):
        """Answer user questions about the data"""
        question_lower = question.lower()

        # Concept explanations
        if 'what is market basket' in question_lower:
            return "🧺 Market basket means products people buy together in one order."
        if 'what is association rule' in question_lower:
            return "🔗 Association rules are simple links that show which products are often bought together."
        if 'what is sales volume' in question_lower:
            return "📦 Sales volume means how many units of a product are sold."
        if 'how do you decide top sellers' in question_lower:
            return "🏆 Top sellers are chosen by the strongest sales signal available (sales volume or review count)."
        if 'how do you calculate profit' in question_lower:
            return "💰 Profit is selling price minus cost price, multiplied by quantity sold."
        if 'what is a category' in question_lower:
            return "🗂️ A category is a group of similar products, like Electronics or Shoes."
        if 'what is average price' in question_lower:
            if 'price' in self.df.columns:
                return f"💰 Average price is ₹{self.df['price'].mean():,.0f}."
            return "Average price is not available."
        if 'what is discount percentage' in question_lower:
            return "🏷️ Discount percentage tells you how much price is reduced compared to the original price."
        if 'what is rating' in question_lower:
            return "⭐ Rating is the average score given by customers, usually out of 5."
        
        # Best selling products
        if 'best selling' in question_lower or 'top product' in question_lower or 'most sold' in question_lower:
            if 'price' in self.df.columns:
                if 'product_name' in self.df.columns:
                    top_products = self.df.nlargest(5, 'price')[['product_name', 'price', 'category']]
                    result = "🏆 Top 5 Products by Price:\n\n"
                    for idx, row in top_products.iterrows():
                        result += f"• {row['product_name'][:50]}\n  Price: ₹{row['price']:,.0f} | Category: {row['category']}\n\n"
                    return result
                else:
                    return f"💰 Price range: ₹{self.df['price'].min():,.0f} - ₹{self.df['price'].max():,.0f}\nAverage Price: ₹{self.df['price'].mean():,.0f}"
            return "Price data not available."
        
        # Category performance
        elif 'which category' in question_lower or 'best category' in question_lower or 'top category' in question_lower:
            if 'category' in self.df.columns and 'rating' in self.df.columns:
                best_cat = self.df.groupby('category')['rating'].mean().sort_values(ascending=False).head(3)
                result = "🌟 Best Performing Categories:\n\n"
                for cat, rating in best_cat.items():
                    count = len(self.df[self.df['category'] == cat])
                    result += f"• {cat}: {rating:.1f} ⭐ ({count} products)\n"
                return result
            return "Category or rating data not available."
        
        # Revenue insights
        elif 'revenue' in question_lower or 'highest revenue' in question_lower or 'top revenue' in question_lower:
            if 'category' in self.df.columns and 'price' in self.df.columns:
                top_revenue = self.df.groupby('category')['price'].sum().sort_values(ascending=False).head(3)
                result = "💰 Top Revenue Categories:\n\n"
                for cat, revenue in top_revenue.items():
                    result += f"• {cat}: ₹{revenue:,.0f}\n"
                return result
            return "Revenue data not available."
        
        # Discount insights
        elif 'discount' in question_lower:
            if 'discount_percentage' in self.df.columns:
                avg_discount = self.df['discount_percentage'].mean()
                max_discount = self.df['discount_percentage'].max()
                min_discount = self.df['discount_percentage'].min()
                return f"💸 Discount Insights:\n\n• Average Discount: {avg_discount:.1f}%\n• Maximum Discount: {max_discount:.1f}%\n• Minimum Discount: {min_discount:.1f}%"
            return "Discount data not available."
        
        # Rating insights
        elif 'rating' in question_lower:
            if 'rating' in self.df.columns:
                avg_rating = self.df['rating'].mean()
                best_rating = self.df['rating'].max()
                worst_rating = self.df['rating'].min()
                return f"⭐ Rating Insights:\n\n• Average Rating: {avg_rating:.1f}/5\n• Best Rating: {best_rating:.1f}/5\n• Lowest Rating: {worst_rating:.1f}/5"
            return "Rating data not available."
        
        # Product count
        elif 'how many' in question_lower or 'total products' in question_lower or 'count' in question_lower:
            return f"📦 Total Products: {len(self.df):,}"
        
        # Price insights
        elif 'price' in question_lower or 'cost' in question_lower:
            price_col = 'price' if 'price' in self.df.columns else ('selling_price' if 'selling_price' in self.df.columns else None)
            if price_col:
                return f"💰 Price Insights:\n\n• Average Price: ₹{self.df[price_col].mean():,.0f}\n• Median Price: ₹{self.df[price_col].median():,.0f}\n• Price Range: ₹{self.df[price_col].min():,.0f} - ₹{self.df[price_col].max():,.0f}"
            return "Price data not available."

        # Association rules / product pairs
        elif 'association' in question_lower or 'sold with' in question_lower or 'bought with' in question_lower or 'together' in question_lower:
            association_result = self.compute_association_rules()
            rules = association_result.get('rules', [])
            if not rules:
                note = association_result.get('note', 'Association rules not available for this dataset.')
                return f"🔗 Product Associations:\n\n{note}"
            top_rules = rules[:10]
            result = "🔗 Top Product Pairs (sold together):\n\n"
            for rule in top_rules:
                result += (
                    f"• {rule['product_a']} + {rule['product_b']} "
                    f"(Count: {rule['count']}, Support: {rule['support']:.2%})\n"
                )
            return result
        
        # Default response
        else:
            return self.get_general_insights()

    def compute_association_rules(self):
        """Compute simple association rules based on transaction baskets."""
        # Detect required columns
        product_col = None
        for candidate in ['product_name', 'product', 'item_name', 'item', 'sku']:
            if candidate in self.df.columns:
                product_col = candidate
                break

        transaction_col = None
        for candidate in [
            'transaction_id', 'order_id', 'orderid', 'invoice_no', 'invoice',
            'bill_no', 'basket_id', 'txn_id'
        ]:
            if candidate in self.df.columns:
                transaction_col = candidate
                break

        if product_col is None:
            return {'rules': [], 'note': 'Product name column not found.', 'by_product': {}}

        if transaction_col is None:
            return {
                'rules': [],
                'note': 'Transaction ID column not found. Add an order/transaction/basket ID column to compute product pairs.'
            }

        baskets = self.df[[transaction_col, product_col]].dropna()
        if baskets.empty:
            return {'rules': [], 'note': 'No transaction data available to compute product pairs.', 'by_product': {}}

        baskets[product_col] = baskets[product_col].astype(str).str.strip()
        grouped = baskets.groupby(transaction_col)[product_col].apply(lambda x: sorted(set(x)))

        total_transactions = int(len(grouped))
        if total_transactions == 0:
            return {'rules': [], 'note': 'No valid transactions found.', 'by_product': {}}

        pair_counts = Counter()
        item_counts = Counter()

        for items in grouped:
            if not items:
                continue
            for item in items:
                item_counts[item] += 1
            if len(items) < 2:
                continue
            for a, b in combinations(items, 2):
                pair_counts[(a, b)] += 1

        rules = []
        by_product = {}
        for (a, b), count in pair_counts.items():
            support = count / total_transactions
            conf_a = count / item_counts[a] if item_counts[a] else 0
            conf_b = count / item_counts[b] if item_counts[b] else 0
            rules.append({
                'product_a': a,
                'product_b': b,
                'count': int(count),
                'support': float(round(support, 4)),
                'confidence_a_to_b': float(round(conf_a, 4)),
                'confidence_b_to_a': float(round(conf_b, 4))
            })
            by_product.setdefault(a, []).append({
                'product': b,
                'count': int(count),
                'support': float(round(support, 4))
            })
            by_product.setdefault(b, []).append({
                'product': a,
                'count': int(count),
                'support': float(round(support, 4))
            })

        rules.sort(key=lambda x: (-x['count'], -x['support'], x['product_a']))
        for key in list(by_product.keys()):
            by_product[key].sort(key=lambda x: (-x['count'], -x['support'], x['product']))

        return {
            'rules': rules,
            'total_transactions': total_transactions,
            'unique_products': int(len(item_counts)),
            'by_product': by_product
        }

    def get_product_list_and_top_sellers(self):
        """Return full product list with pricing and top sellers."""
        product_col = None
        for candidate in ['product_name', 'product', 'item_name', 'item', 'sku']:
            if candidate in self.df.columns:
                product_col = candidate
                break

        if product_col is None:
            return [], [], 'unavailable'

        price_col = 'price' if 'price' in self.df.columns else ('selling_price' if 'selling_price' in self.df.columns else None)

        sales_basis = 'unavailable'
        sales_col = None
        if 'sales_volume' in self.df.columns:
            sales_col = 'sales_volume'
            sales_basis = 'sales_volume'
        elif 'review_count' in self.df.columns:
            sales_col = 'review_count'
            sales_basis = 'review_count'

        columns = [product_col]
        if price_col:
            columns.append(price_col)
        if sales_col:
            columns.append(sales_col)
        if 'category' in self.df.columns:
            columns.append('category')
        if 'rating' in self.df.columns:
            columns.append('rating')
        if 'discount_percentage' in self.df.columns:
            columns.append('discount_percentage')

        product_df = self.df[columns].copy()
        product_df[product_col] = product_df[product_col].astype(str).str.strip()

        group_fields = {}
        if price_col:
            group_fields[price_col] = 'mean'
        if sales_col:
            group_fields[sales_col] = 'sum'
        if 'rating' in product_df.columns:
            group_fields['rating'] = 'mean'
        if 'discount_percentage' in product_df.columns:
            group_fields['discount_percentage'] = 'mean'

        if group_fields:
            grouped = product_df.groupby(product_col).agg(group_fields).reset_index()
        else:
            grouped = product_df[[product_col]].drop_duplicates()

        if 'category' in product_df.columns:
            categories = (
                product_df.groupby(product_col)['category']
                .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0])
                .reset_index()
            )
            grouped = grouped.merge(categories, on=product_col, how='left')

        product_list = []
        for _, row in grouped.iterrows():
            entry = {
                'product_name': row[product_col]
            }
            if price_col:
                entry['price'] = float(row[price_col])
            if sales_col:
                entry['sales'] = float(row[sales_col])
            if 'category' in grouped.columns:
                entry['category'] = row.get('category', '')
            if 'rating' in grouped.columns:
                entry['rating'] = float(row['rating']) if pd.notna(row['rating']) else None
            if 'discount_percentage' in grouped.columns:
                entry['discount_percentage'] = float(row['discount_percentage']) if pd.notna(row['discount_percentage']) else None
            product_list.append(entry)

        if sales_col:
            top_sellers_df = grouped.sort_values(by=sales_col, ascending=False).head(10)
            top_sellers = [
                {
                    'product_name': row[product_col],
                    'sales': float(row[sales_col])
                }
                for _, row in top_sellers_df.iterrows()
            ]
        else:
            top_sellers = []

        product_list.sort(key=lambda x: x['product_name'])

        return product_list, top_sellers, sales_basis

    def get_product_sales_series(self, sales_basis):
        """Return a list for plotting product sales or demand."""
        product_col = None
        for candidate in ['product_name', 'product', 'item_name', 'item', 'sku']:
            if candidate in self.df.columns:
                product_col = candidate
                break
        if product_col is None:
            return []

        sales_col = None
        if sales_basis == 'sales_volume' and 'sales_volume' in self.df.columns:
            sales_col = 'sales_volume'
        elif sales_basis == 'review_count' and 'review_count' in self.df.columns:
            sales_col = 'review_count'

        if sales_col is None:
            return []

        tmp = self.df[[product_col, sales_col]].copy()
        tmp[product_col] = tmp[product_col].astype(str).str.strip()
        series = tmp.groupby(product_col)[sales_col].sum().sort_values(ascending=False)
        return [{'product_name': k, 'value': float(v)} for k, v in series.items()]

    def compute_profit_loss(self):
        """Compute profit and loss if relevant columns exist."""
        df = self.df.copy()

        cost_col = None
        for candidate in ['cost_price', 'cost', 'buy_price', 'buy', 'purchase_price', 'expenditure']:
            if candidate in df.columns:
                cost_col = candidate
                break

        sell_col = None
        for candidate in ['selling_price', 'sell_price', 'price', 'revenue', 'sold_price']:
            if candidate in df.columns:
                sell_col = candidate
                break

        qty_col = None
        for candidate in ['quantity', 'qty', 'units_sold', 'sold_units']:
            if candidate in df.columns:
                qty_col = candidate
                break

        if cost_col is None or sell_col is None:
            return {'available': False, 'note': 'Cost and selling price columns not found.'}

        df[cost_col] = pd.to_numeric(df[cost_col], errors='coerce').fillna(0)
        df[sell_col] = pd.to_numeric(df[sell_col], errors='coerce').fillna(0)
        if qty_col:
            df[qty_col] = pd.to_numeric(df[qty_col], errors='coerce').fillna(1)
        else:
            df['_qty'] = 1
            qty_col = '_qty'

        df['profit_value'] = (df[sell_col] - df[cost_col]) * df[qty_col]
        total_profit = df['profit_value'][df['profit_value'] > 0].sum()
        total_loss = (-df['profit_value'][df['profit_value'] < 0]).sum()
        net = df['profit_value'].sum()

        return {
            'available': True,
            'total_profit': float(total_profit),
            'total_loss': float(total_loss),
            'net_profit': float(net),
            'basis': f"Computed from {sell_col} - {cost_col} x {qty_col}"
        }

    def compute_avg_annual_expenditure(self):
        """Compute average annual expenditure if date/year and expenditure exist."""
        df = self.df.copy()

        exp_col = None
        for candidate in ['expenditure', 'expense', 'spend', 'cost', 'buy', 'purchase_value']:
            if candidate in df.columns:
                exp_col = candidate
                break
        if exp_col is None:
            return {'available': False, 'note': 'No expenditure column found.'}

        date_col = None
        for candidate in ['date', 'order_date', 'purchase_date', 'invoice_date', 'txn_date', 'year']:
            if candidate in df.columns:
                date_col = candidate
                break
        if date_col is None:
            return {'available': False, 'note': 'No date/year column found.'}

        df[exp_col] = pd.to_numeric(df[exp_col], errors='coerce').fillna(0)

        if date_col == 'year':
            df['year_val'] = pd.to_numeric(df['year'], errors='coerce')
        else:
            df['year_val'] = pd.to_datetime(df[date_col], errors='coerce').dt.year

        annual = df.dropna(subset=['year_val']).groupby('year_val')[exp_col].sum()
        if annual.empty:
            return {'available': False, 'note': 'No valid yearly expenditure data found.'}

        avg_annual = annual.mean()
        return {
            'available': True,
            'average_annual_expenditure': float(avg_annual),
            'years': [int(y) for y in annual.index.tolist()]
        }
    
    def get_general_insights(self):
        """Provide general insights about the data"""
        insights = []
        insights.append(f"📊 Data Overview: {len(self.df)} products analyzed")
        
        if 'category' in self.df.columns:
            insights.append(f"📁 Categories: {self.df['category'].nunique()} unique categories")
        
        price_col = 'price' if 'price' in self.df.columns else ('selling_price' if 'selling_price' in self.df.columns else None)
        if price_col:
            insights.append(f"💰 Price Range: ₹{self.df[price_col].min():,.0f} - ₹{self.df[price_col].max():,.0f}")
            insights.append(f"💰 Average Price: ₹{self.df[price_col].mean():,.0f}")
        
        if 'rating' in self.df.columns:
            insights.append(f"⭐ Average Rating: {self.df['rating'].mean():.1f}/5")
        
        if 'discount_percentage' in self.df.columns:
            insights.append(f"💸 Average Discount: {self.df['discount_percentage'].mean():.1f}%")
        
        return "\n".join(insights)
