// API Configuration
const API_URL = 'http://localhost:5000/api';

// Global variables
let currentData = null;
let productChart = null;
let productListFull = [];

// File upload handling
document.getElementById('fileInput').addEventListener('change', function (e) {
    const fileName = e.target.files[0]?.name;
    if (fileName) {
        document.getElementById('uploadBtn').innerHTML = `<i class="fas fa-file"></i> ${fileName} selected`;
    }
});

// Upload file function
async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (!file) {
        showStatus('Please select a file first!', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    showStatus('Uploading and analyzing...', 'info');
    document.getElementById('uploadBtn').disabled = true;

    try {
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showStatus(data.message, 'success');
            currentData = data;
            displayDashboard(data);
            document.getElementById('dashboard').classList.remove('hidden');

            // Scroll to dashboard
            document.getElementById('dashboard').scrollIntoView({ behavior: 'smooth' });
        } else {
            showStatus(data.error, 'error');
        }
    } catch (error) {
        showStatus('Error uploading file. Make sure the backend server is running!', 'error');
        console.error('Error:', error);
    } finally {
        document.getElementById('uploadBtn').disabled = false;
        document.getElementById('uploadBtn').innerHTML = '<i class="fas fa-upload"></i> Upload & Analyze';
    }
}

// Display dashboard with insights
function displayDashboard(data) {
    const insights = data.insights;

    // Update metrics
    document.getElementById('totalProducts').innerText = insights.total_products?.toLocaleString() || '0';
    document.getElementById('totalCategories').innerText = insights.total_categories || '0';
    document.getElementById('avgPrice').innerText = `₹${Math.round(insights.avg_price || 0).toLocaleString()}`;
    document.getElementById('avgRating').innerText = (insights.avg_rating || 0).toFixed(1);
    document.getElementById('avgDiscount').innerText = `${Math.round(insights.avg_discount || 0)}%`;

    // Display top categories by revenue
    if (insights.top_categories_by_revenue) {
        const revenueDiv = document.getElementById('topRevenue');
        revenueDiv.innerHTML = '<ul>';
        Object.entries(insights.top_categories_by_revenue).slice(0, 5).forEach(([cat, revenue]) => {
            revenueDiv.innerHTML += `<li><strong>${cat}</strong>: ₹${Math.round(revenue).toLocaleString()}</li>`;
        });
        revenueDiv.innerHTML += '</ul>';
    }

    // Display top rated categories
    if (insights.top_categories_by_rating) {
        const ratingDiv = document.getElementById('topRated');
        ratingDiv.innerHTML = '<ul>';
        Object.entries(insights.top_categories_by_rating).slice(0, 5).forEach(([cat, rating]) => {
            ratingDiv.innerHTML += `<li><strong>${cat}</strong>: ${rating.toFixed(1)} ⭐</li>`;
        });
        ratingDiv.innerHTML += '</ul>';
    }

    // Display segmentation
    if (insights.segmentation) {
        const segDiv = document.getElementById('segmentation');
        segDiv.innerHTML = '<ul>';
        Object.entries(insights.segmentation).forEach(([segment, count]) => {
            segDiv.innerHTML += `<li><strong>${segment}</strong>: ${count} products</li>`;
        });
        segDiv.innerHTML += '</ul>';
    }

    // Display recommendations
    if (insights.recommendations && insights.recommendations.length > 0) {
        const recDiv = document.getElementById('recommendations');
        recDiv.innerHTML = '<ul>';
        insights.recommendations.forEach(rec => {
            recDiv.innerHTML += `<li>${rec}</li>`;
        });
        recDiv.innerHTML += '</ul>';
    }

    // Explanation of insights
    const explanationDiv = document.getElementById('insightsExplanation');
    if (insights.insights_explanation) {
        const lines = insights.insights_explanation.split('\n');
        explanationDiv.innerHTML = '<ul>';
        lines.forEach(line => {
            explanationDiv.innerHTML += `<li>${line}</li>`;
        });
        explanationDiv.innerHTML += '</ul>';
    }

    // Profit & loss
    const profitLossDiv = document.getElementById('profitLoss');
    if (insights.profit_loss && insights.profit_loss.available) {
        const pl = insights.profit_loss;
        profitLossDiv.innerHTML = `
            <ul>
                <li><strong>Total Profit</strong>: ₹${Math.round(pl.total_profit).toLocaleString()}</li>
                <li><strong>Total Loss</strong>: ₹${Math.round(pl.total_loss).toLocaleString()}</li>
                <li><strong>Net Profit</strong>: ₹${Math.round(pl.net_profit).toLocaleString()}</li>
                <li><strong>Basis</strong>: ${pl.basis}</li>
            </ul>
        `;
    } else {
        profitLossDiv.innerHTML = `<p class="placeholder">${insights.profit_loss?.note || 'Profit/Loss data not available.'}</p>`;
    }

    // Avg annual expenditure
    const avgExpDiv = document.getElementById('avgExpenditure');
    if (insights.avg_annual_expenditure && insights.avg_annual_expenditure.available) {
        avgExpDiv.innerHTML = `
            <ul>
                <li><strong>Average Annual Expenditure</strong>: ₹${Math.round(insights.avg_annual_expenditure.average_annual_expenditure).toLocaleString()}</li>
                <li><strong>Years Found</strong>: ${insights.avg_annual_expenditure.years.join(', ')}</li>
            </ul>
        `;
    } else {
        avgExpDiv.innerHTML = `<p class="placeholder">${insights.avg_annual_expenditure?.note || 'Annual expenditure not available.'}</p>`;
    }

    // Store full product list and render filters/table
    productListFull = insights.product_list || [];
    populateCategoryFilter(productListFull);
    renderProductTable();

    // Top selling products
    const topSellingDiv = document.getElementById('topSelling');
    if (insights.top_selling_products && insights.top_selling_products.length > 0) {
        topSellingDiv.innerHTML = '<ul>';
        insights.top_selling_products.forEach(item => {
            const salesBasis = insights.sales_basis || 'sales';
            const salesLabel = salesBasis === 'review_count' ? 'Reviews' : 'Sales';
            topSellingDiv.innerHTML += `<li><strong>${item.product_name}</strong>: ${Math.round(item.sales).toLocaleString()} ${salesLabel}</li>`;
        });
        topSellingDiv.innerHTML += '</ul>';
    } else {
        topSellingDiv.innerHTML = '<p class="placeholder">Top sellers unavailable (no sales or review signals found).</p>';
    }

    // Display association rules
    const associationMeta = document.getElementById('associationMeta');
    const associationDiv = document.getElementById('associationRules');
    if (insights.association_meta) {
        const note = insights.association_meta.note || '';
        const totalTx = insights.association_meta.total_transactions || 0;
        const uniqueProducts = insights.association_meta.unique_products || 0;
        let metaText = '';
        if (note) {
            metaText = note;
        } else {
            metaText = `Transactions: ${totalTx.toLocaleString()} | Products: ${uniqueProducts.toLocaleString()}`;
        }
        associationMeta.innerText = metaText;
    }

    if (insights.association_rules && insights.association_rules.length > 0) {
        associationDiv.innerHTML = '';
        insights.association_rules.forEach(rule => {
            const row = document.createElement('div');
            row.className = 'pair-row';

            const names = document.createElement('div');
            names.className = 'pair-names';
            names.innerText = `${rule.product_a} + ${rule.product_b}`;

            const metrics = document.createElement('div');
            metrics.className = 'pair-metrics';
            const supportPct = (rule.support * 100).toFixed(2);
            const confA = (rule.confidence_a_to_b * 100).toFixed(2);
            const confB = (rule.confidence_b_to_a * 100).toFixed(2);
            metrics.innerHTML = `<span>Count: ${rule.count}</span><span>Support: ${supportPct}%</span><span>A→B: ${confA}%</span><span>B→A: ${confB}%</span>`;

            row.appendChild(names);
            row.appendChild(metrics);
            associationDiv.appendChild(row);
        });
    } else {
        associationDiv.innerHTML = '<p class="placeholder">No association rules available for this dataset.</p>';
    }

    // Market basket by product
    const basketDiv = document.getElementById('basketByProduct');
    if (insights.association_by_product && Object.keys(insights.association_by_product).length > 0) {
        basketDiv.innerHTML = '';
        Object.entries(insights.association_by_product).forEach(([product, list]) => {
            const row = document.createElement('div');
            row.className = 'pair-row';
            const name = document.createElement('div');
            name.className = 'pair-names';
            name.innerText = product;
            const metrics = document.createElement('div');
            metrics.className = 'pair-metrics';
            if (list.length === 0) {
                metrics.innerHTML = '<span>No sub products</span>';
            } else {
                metrics.innerHTML = list
                    .map(item => `${item.product} (count: ${item.count})`)
                    .join(' | ');
            }
            row.appendChild(name);
            row.appendChild(metrics);
            basketDiv.appendChild(row);
        });
    } else if (insights.product_list && insights.product_list.length > 0) {
        basketDiv.innerHTML = '';
        insights.product_list.forEach(item => {
            const row = document.createElement('div');
            row.className = 'pair-row';
            const name = document.createElement('div');
            name.className = 'pair-names';
            name.innerText = item.product_name;
            const metrics = document.createElement('div');
            metrics.className = 'pair-metrics';
            metrics.innerHTML = '<span>No sub products</span>';
            row.appendChild(name);
            row.appendChild(metrics);
            basketDiv.appendChild(row);
        });
    } else {
        basketDiv.innerHTML = '<p class="placeholder">No product list available.</p>';
    }

    // Model accuracy display
    if (insights.rating_model && insights.rating_model.accuracy !== undefined) {
        const acc = insights.rating_model.accuracy.toFixed(1);
        document.getElementById('modelAccuracy').innerText = `Model Accuracy: ${acc}%`;
    }

    // Product chart
    const chartSeries = (insights.product_sales && insights.product_sales.length > 0)
        ? insights.product_sales
        : buildPriceSeriesFromProducts(productListFull);
    renderProductChart(chartSeries);
}

// Render product chart
function renderProductChart(series) {
    const canvas = document.getElementById('productChart');
    if (!canvas) return;

    if (!series || series.length === 0) {
        const parent = canvas.parentElement;
        if (parent) {
            parent.innerHTML = '<p class="placeholder">No chart data available.</p>';
        }
        return;
    }

    const ctx = canvas.getContext('2d');
    const width = canvas.clientWidth || 420;
    let height = canvas.height || 320;
    canvas.width = width;
    canvas.height = height;

    const items = series;
    const maxVal = Math.max(...items.map(item => item.value)) || 1;

    ctx.clearRect(0, 0, width, height);

    const padding = 16;
    const labelWidth = 140;
    const chartWidth = width - padding * 2 - labelWidth;
    const barHeight = 18;
    const gap = 12;
    const requiredHeight = padding * 2 + items.length * (barHeight + gap);
    if (requiredHeight > height) {
        canvas.height = requiredHeight;
        canvas.style.height = `${requiredHeight}px`;
        height = canvas.height;
    } else {
        canvas.style.height = `${height}px`;
    }

    ctx.font = '12px "IBM Plex Sans", sans-serif';
    ctx.fillStyle = '#9aa4b2';

    items.forEach((item, idx) => {
        const y = padding + idx * (barHeight + gap);
        // Label on the left
        const labelText = item.product_name.length > 18
            ? `${item.product_name.slice(0, 18)}…`
            : item.product_name;
        ctx.fillText(labelText, padding, y + 13);

        // Bar track (right side)
        const barX = padding + labelWidth;
        const barY = y;
        const barLen = Math.max(6, (item.value / maxVal) * chartWidth);

        // Track
        ctx.fillStyle = 'rgba(255, 255, 255, 0.08)';
        ctx.fillRect(barX, barY, chartWidth, barHeight);

        // Fill from right to left
        ctx.fillStyle = '#39ff88';
        ctx.fillRect(barX + chartWidth - barLen, barY, barLen, barHeight);

        // Value
        ctx.fillStyle = '#9aa4b2';
        ctx.fillText(Math.round(item.value).toLocaleString(), barX + chartWidth + 6, barY + 13);
    });
}

function buildPriceSeriesFromProducts(products) {
    if (!products || products.length === 0) return [];
    const series = products
        .filter(p => typeof p.price === 'number')
        .map(p => ({ product_name: p.product_name, value: p.price }));
    return series;
}

// Populate category dropdown
function populateCategoryFilter(items) {
    const categoryFilter = document.getElementById('categoryFilter');
    if (!categoryFilter) return;
    const categories = Array.from(new Set(items.map(i => i.category).filter(Boolean))).sort();
    categoryFilter.innerHTML = '<option value="all">All Categories</option>';
    categories.forEach(cat => {
        const opt = document.createElement('option');
        opt.value = cat;
        opt.innerText = cat;
        categoryFilter.appendChild(opt);
    });
}

// Render product table based on filters
function renderProductTable() {
    const container = document.getElementById('productTable');
    if (!container) return;
    if (!productListFull || productListFull.length === 0) {
        container.innerHTML = '<p class="placeholder">No product list available.</p>';
        return;
    }

    const searchValue = (document.getElementById('searchProduct')?.value || '').toLowerCase();
    const categoryValue = document.getElementById('categoryFilter')?.value || 'all';
    const sortValue = document.getElementById('sortFilter')?.value || 'name_asc';

    let filtered = productListFull.filter(item => {
        const matchesSearch = item.product_name.toLowerCase().includes(searchValue);
        const matchesCategory = categoryValue === 'all' || item.category === categoryValue;
        return matchesSearch && matchesCategory;
    });

    const getNumber = (v) => (typeof v === 'number' && !isNaN(v)) ? v : -Infinity;

    filtered.sort((a, b) => {
        switch (sortValue) {
            case 'price_high':
                return getNumber(b.price) - getNumber(a.price);
            case 'price_low':
                return getNumber(a.price) - getNumber(b.price);
            case 'rating_high':
                return getNumber(b.rating) - getNumber(a.rating);
            case 'rating_low':
                return getNumber(a.rating) - getNumber(b.rating);
            case 'discount_high':
                return getNumber(b.discount_percentage) - getNumber(a.discount_percentage);
            case 'discount_low':
                return getNumber(a.discount_percentage) - getNumber(b.discount_percentage);
            case 'sales_high':
                return getNumber(b.sales) - getNumber(a.sales);
            case 'sales_low':
                return getNumber(a.sales) - getNumber(b.sales);
            default:
                return a.product_name.localeCompare(b.product_name);
        }
    });

    const rows = filtered.map(item => {
        const price = item.price !== undefined ? `₹${Math.round(item.price).toLocaleString()}` : 'N/A';
        const rating = item.rating !== undefined && item.rating !== null ? item.rating.toFixed(1) : 'N/A';
        const discount = item.discount_percentage !== undefined && item.discount_percentage !== null ? `${item.discount_percentage.toFixed(1)}%` : 'N/A';
        const sales = item.sales !== undefined ? Math.round(item.sales).toLocaleString() : 'N/A';
        const category = item.category || 'N/A';
        return `
            <tr>
                <td><strong>${item.product_name}</strong></td>
                <td>${category}</td>
                <td>${price}</td>
                <td>${rating}</td>
                <td>${discount}</td>
                <td>${sales}</td>
            </tr>
        `;
    }).join('');

    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Category</th>
                    <th>Price</th>
                    <th>Rating</th>
                    <th>Discount</th>
                    <th>Sales</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;
}

// Send message to AI assistant
async function sendMessage(message) {
    const cleanMessage = (message || '').trim();
    if (!cleanMessage) return;

    // Add user message to chat
    addMessageToChat(cleanMessage, 'user');

    // Show typing indicator
    const typingIndicator = addTypingIndicator();

    try {
        const response = await fetch(`${API_URL}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: cleanMessage })
        });

        const data = await response.json();

        // Remove typing indicator
        typingIndicator.remove();

        if (data.answer) {
            addMessageToChat(data.answer, 'bot');
        } else if (data.error) {
            addMessageToChat(`❌ ${data.error}`, 'bot');
        }
    } catch (error) {
        typingIndicator.remove();
        addMessageToChat('❌ Error connecting to the server. Make sure the backend is running!', 'bot');
        console.error('Error:', error);
    }
}

// Add message to chat
function addMessageToChat(message, sender) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    // Convert newlines to <br> tags
    contentDiv.innerHTML = message.replace(/\n/g, '<br>');

    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add typing indicator
function addTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot';
    typingDiv.id = 'typingIndicator';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = '<div class="loading"></div> Thinking...';

    typingDiv.appendChild(contentDiv);
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return typingDiv;
}

// Show status message
function showStatus(message, type) {
    const statusDiv = document.getElementById('uploadStatus');
    statusDiv.className = `status-message ${type}`;
    statusDiv.innerHTML = message;

    setTimeout(() => {
        statusDiv.className = 'status-message';
        statusDiv.innerHTML = '';
    }, 5000);
}

// Check backend health on page load
async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        console.log('Backend status:', data);
    } catch (error) {
        console.error('Backend not running:', error);
        showStatus('⚠️ Backend server is not running. Please start the backend first!', 'error');
    }
}

// Render quick question buttons
function renderQuickQuestions() {
    const quickQuestions = [
        'How many products do we have?',
        'Which category performs best?',
        'What is the average rating?',
        'Which products generate highest revenue?',
        'Tell me about discounts',
        'Show me price insights',
        'Which products are sold together?',
        'What is market basket?',
        'What is association rule?',
        'What is a category?',
        'What is discount percentage?',
        'What is average price?',
        'How do you calculate profit?',
        'What is sales volume?',
        'What is rating?',
        'How do you decide top sellers?'
    ];

    const container = document.getElementById('quickQuestions');
    if (!container) return;
    container.innerHTML = '';
    quickQuestions.forEach(q => {
        const btn = document.createElement('button');
        btn.className = 'question-btn';
        btn.type = 'button';
        btn.innerText = q;
        btn.addEventListener('click', () => sendMessage(q));
        container.appendChild(btn);
    });
}

// Initialize on page load
window.addEventListener('load', () => {
    checkBackendHealth();
    renderQuickQuestions();
    document.getElementById('searchProduct')?.addEventListener('input', renderProductTable);
    document.getElementById('categoryFilter')?.addEventListener('change', renderProductTable);
    document.getElementById('sortFilter')?.addEventListener('change', renderProductTable);
    document.getElementById('downloadPdf')?.addEventListener('click', downloadPdf);
    const reportDate = document.getElementById('reportDate');
    if (reportDate) {
        reportDate.textContent = new Date().toLocaleDateString();
    }
});

function downloadPdf() {
    window.print();
}
