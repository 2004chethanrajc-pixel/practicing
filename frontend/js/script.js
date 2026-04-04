// ===== CONFIG =====
const API_URL = 'http://localhost:5000/api';

// ===== STATE =====
let currentInsights = null;
let mainChartInstance = null;
let productListFull = [];

// ===== CHART COLORS (matching Streamlit accent palette) =====
const ACCENT   = '#39ff88';
const ACCENT2  = '#00c2ff';
const MUTED    = '#9aa4b2';
const PANEL2   = '#1b2130';
const BORDER   = 'rgba(255,255,255,0.08)';

const CHART_COLORS = [
    '#39ff88','#00c2ff','#ff6b9d','#ffd166','#a78bfa',
    '#f97316','#06b6d4','#84cc16','#ec4899','#14b8a6'
];

Chart.defaults.color = MUTED;
Chart.defaults.borderColor = BORDER;
Chart.defaults.font.family = "'IBM Plex Sans', sans-serif";
Chart.defaults.font.size = 13;

// ===== SIDEBAR NAVIGATION =====
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', function () {
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');

        const targetId = this.getAttribute('data-target');
        const el = document.getElementById(targetId);
        if (!el) return;

        // If data not loaded and not dashboard, still scroll but sections are hidden
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // If charts section becomes visible, render chart
        if (targetId === 'section-charts' && currentInsights) {
            renderSelectedChart();
        }
    });
});

// ===== FILE INPUT =====
document.getElementById('fileInput').addEventListener('change', function (e) {
    const file = e.target.files[0];
    if (file) {
        document.getElementById('fileNameDisplay').textContent = file.name;
        document.getElementById('uploadBtn').textContent = `📊 Upload & Analyze "${file.name}"`;
    }
});

// ===== UPLOAD =====
document.getElementById('uploadBtn').addEventListener('click', async function () {
    const file = document.getElementById('fileInput').files[0];
    if (!file) { showStatus('Please select a file first!', 'error'); return; }

    const formData = new FormData();
    formData.append('file', file);

    showStatus('📊 Loading and analyzing your data...', 'info');
    this.disabled = true;

    try {
        const res  = await fetch(`${API_URL}/upload`, { method: 'POST', body: formData });
        const data = await res.json();

        if (data.success) {
            currentInsights = data.insights;
            productListFull = data.insights.product_list || [];

            showStatus(`✅ ${data.message}`, 'success');
            renderAll(data.insights);

            // Update sidebar status
            document.getElementById('dataStatusSidebar').innerHTML =
                `✅ ${(data.insights.total_products || 0).toLocaleString()} rows loaded`;

            // Reveal all sections
            ['section-kpis','section-insights','section-charts',
             'section-products','section-basket','section-model','section-chat']
                .forEach(id => document.getElementById(id).classList.remove('hidden'));

            setTimeout(() => showStatus('', ''), 4000);
        } else {
            showStatus(`❌ ${data.error}`, 'error');
        }
    } catch (err) {
        showStatus('❌ Error uploading file. Make sure the backend server is running!', 'error');
        console.error(err);
    } finally {
        this.disabled = false;
        this.textContent = '📊 Upload & Analyze';
    }
});

// ===== RENDER ALL =====
function renderAll(insights) {
    renderKPIs(insights);
    renderInsights(insights);
    renderProducts(insights);
    renderBasket(insights);
    renderModel(insights);
    renderQuickQuestions();
    populateCategoryFilter(productListFull);
    renderProductTable();
    renderSelectedChart();
}

// ===== KPIs =====
function renderKPIs(ins) {
    document.getElementById('totalProducts').textContent = (ins.total_products || 0).toLocaleString();
    document.getElementById('totalCategories').textContent = ins.total_categories || 0;
    document.getElementById('avgPrice').textContent = `₹${Math.round(ins.avg_price || 0).toLocaleString()}`;
    document.getElementById('avgRating').textContent = `${(ins.avg_rating || 0).toFixed(1)} / 5`;
    document.getElementById('avgDiscount').textContent = `${Math.round(ins.avg_discount || 0)}%`;
}

// ===== INSIGHTS =====
function renderInsights(ins) {
    // Top revenue
    const revDiv = document.getElementById('topRevenue');
    if (ins.top_categories_by_revenue && Object.keys(ins.top_categories_by_revenue).length) {
        revDiv.innerHTML = '<ul>' +
            Object.entries(ins.top_categories_by_revenue).slice(0,5)
                .map(([c,v]) => `<li><strong>${c}</strong>: ₹${Math.round(v).toLocaleString()}</li>`).join('') +
            '</ul>';
    } else { revDiv.innerHTML = '<p class="placeholder">No revenue data available</p>'; }

    // Top rated
    const rateDiv = document.getElementById('topRated');
    if (ins.top_categories_by_rating && Object.keys(ins.top_categories_by_rating).length) {
        rateDiv.innerHTML = '<ul>' +
            Object.entries(ins.top_categories_by_rating).slice(0,5)
                .map(([c,v]) => `<li><strong>${c}</strong>: ${v.toFixed(1)} ⭐</li>`).join('') +
            '</ul>';
    } else { rateDiv.innerHTML = '<p class="placeholder">No rating data available</p>'; }

    // Segmentation
    const segDiv = document.getElementById('segmentation');
    if (ins.segmentation && Object.keys(ins.segmentation).length) {
        segDiv.innerHTML = '<ul>' +
            Object.entries(ins.segmentation)
                .map(([s,c]) => `<li><strong>${s}</strong>: ${c} products</li>`).join('') +
            '</ul>';
    } else { segDiv.innerHTML = '<p class="placeholder">No segmentation data available</p>'; }

    // Profit & Loss
    const plDiv = document.getElementById('profitLoss');
    if (ins.profit_loss && ins.profit_loss.available) {
        const pl = ins.profit_loss;
        plDiv.innerHTML = `<ul>
            <li><strong>Total Profit</strong>: ₹${Math.round(pl.total_profit).toLocaleString()}</li>
            <li><strong>Total Loss</strong>: ₹${Math.round(pl.total_loss).toLocaleString()}</li>
            <li><strong>Net Profit</strong>: ₹${Math.round(pl.net_profit).toLocaleString()}</li>
        </ul>`;
    } else { plDiv.innerHTML = `<p class="placeholder">${ins.profit_loss?.note || 'Profit/Loss data not available.'}</p>`; }

    // Annual expenditure
    const expDiv = document.getElementById('avgExpenditure');
    if (ins.avg_annual_expenditure && ins.avg_annual_expenditure.available) {
        const ae = ins.avg_annual_expenditure;
        expDiv.innerHTML = `<ul>
            <li><strong>Average</strong>: ₹${Math.round(ae.average_annual_expenditure).toLocaleString()}</li>
            <li><strong>Years</strong>: ${ae.years.join(', ')}</li>
        </ul>`;
    } else { expDiv.innerHTML = `<p class="placeholder">${ins.avg_annual_expenditure?.note || 'Annual expenditure not available.'}</p>`; }

    // Recommendations
    const recDiv = document.getElementById('recommendations');
    if (ins.recommendations && ins.recommendations.length) {
        recDiv.innerHTML = '<ul>' + ins.recommendations.slice(0,6).map(r => `<li>${r}</li>`).join('') + '</ul>';
    } else { recDiv.innerHTML = '<p class="placeholder">No recommendations available</p>'; }

    // Explanation
    const expEl = document.getElementById('insightsExplanation');
    if (ins.insights_explanation) {
        const lines = ins.insights_explanation.split('\n').filter(l => l.trim());
        expEl.innerHTML = '<ul>' + lines.slice(0,6).map(l => `<li>${l}</li>`).join('') + '</ul>';
    } else { expEl.innerHTML = '<p class="placeholder">No explanation available</p>'; }
}

// ===== CHARTS =====
document.getElementById('chartTypeSelect').addEventListener('change', renderSelectedChart);

function renderSelectedChart() {
    if (!currentInsights) return;
    const type = document.getElementById('chartTypeSelect').value;
    const noData = document.getElementById('chartNoData');

    if (mainChartInstance) { mainChartInstance.destroy(); mainChartInstance = null; }

    const canvas = document.getElementById('mainChart');
    canvas.style.display = 'block';
    noData.style.display = 'none';

    const ins = currentInsights;
    const products = ins.product_list || [];

    if (type === 'sales') {
        // ── Chart 1: Top Products by Sales (Bar) ──
        const salesData = ins.product_sales && ins.product_sales.length
            ? ins.product_sales
            : products.filter(p => typeof p.price === 'number').map(p => ({ product_name: p.product_name, value: p.price }));

        if (!salesData.length) { canvas.style.display='none'; noData.style.display='block'; return; }

        const top = salesData.slice(0, 20);
        mainChartInstance = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: top.map(d => truncate(d.product_name, 22)),
                datasets: [{
                    label: 'Sales',
                    data: top.map(d => d.value),
                    backgroundColor: top.map((_, i) => hexAlpha(CHART_COLORS[i % CHART_COLORS.length], 0.75)),
                    borderColor:     top.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]),
                    borderWidth: 1, borderRadius: 4,
                }]
            },
            options: chartOptions('Top Products by Sales', 'Product', 'Sales')
        });

    } else if (type === 'category') {
        // ── Chart 2: Category Distribution (Bar) ──
        const catMap = {};
        products.forEach(p => { if (p.category) catMap[p.category] = (catMap[p.category] || 0) + 1; });
        const entries = Object.entries(catMap).sort((a,b) => b[1]-a[1]);

        if (!entries.length) { canvas.style.display='none'; noData.style.display='block'; return; }

        mainChartInstance = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: entries.map(e => e[0]),
                datasets: [{
                    label: 'Products',
                    data: entries.map(e => e[1]),
                    backgroundColor: entries.map((_, i) => hexAlpha(CHART_COLORS[i % CHART_COLORS.length], 0.75)),
                    borderColor:     entries.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]),
                    borderWidth: 1, borderRadius: 4,
                }]
            },
            options: chartOptions('Category Distribution', 'Category', 'Number of Products')
        });

    } else if (type === 'price_rating') {
        // ── Chart 3: Price vs Rating Trend (Line) ──
        const pts = products.filter(p => typeof p.price === 'number' && typeof p.rating === 'number')
            .sort((a,b) => a.price - b.price);

        if (!pts.length) { canvas.style.display='none'; noData.style.display='block'; return; }

        mainChartInstance = new Chart(canvas, {
            type: 'line',
            data: {
                labels: pts.map(p => `₹${Math.round(p.price).toLocaleString()}`),
                datasets: [{
                    label: 'Rating',
                    data: pts.map(p => p.rating),
                    borderColor: ACCENT,
                    backgroundColor: hexAlpha(ACCENT, 0.12),
                    pointBackgroundColor: ACCENT,
                    pointRadius: 3,
                    tension: 0.35, fill: true,
                }]
            },
            options: chartOptions('Price vs Rating Trend', 'Price (₹)', 'Rating')
        });

    } else if (type === 'discount_rating') {
        // ── Chart 4: Discount vs Rating Trend (Line) ──
        const pts = products.filter(p => typeof p.discount_percentage === 'number' && typeof p.rating === 'number')
            .sort((a,b) => a.discount_percentage - b.discount_percentage);

        if (!pts.length) { canvas.style.display='none'; noData.style.display='block'; return; }

        mainChartInstance = new Chart(canvas, {
            type: 'line',
            data: {
                labels: pts.map(p => `${p.discount_percentage.toFixed(1)}%`),
                datasets: [{
                    label: 'Rating',
                    data: pts.map(p => p.rating),
                    borderColor: ACCENT2,
                    backgroundColor: hexAlpha(ACCENT2, 0.12),
                    pointBackgroundColor: ACCENT2,
                    pointRadius: 3,
                    tension: 0.35, fill: true,
                }]
            },
            options: chartOptions('Discount vs Rating Trend', 'Discount %', 'Rating')
        });

    } else if (type === 'rating_dist') {
        // ── Chart 5: Rating Distribution (Bar) ──
        const ratingMap = {};
        products.forEach(p => {
            if (typeof p.rating === 'number') {
                const key = p.rating.toFixed(1);
                ratingMap[key] = (ratingMap[key] || 0) + 1;
            }
        });
        const entries = Object.entries(ratingMap).sort((a,b) => parseFloat(a[0]) - parseFloat(b[0]));

        if (!entries.length) { canvas.style.display='none'; noData.style.display='block'; return; }

        mainChartInstance = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: entries.map(e => e[0]),
                datasets: [{
                    label: 'Products',
                    data: entries.map(e => e[1]),
                    backgroundColor: hexAlpha(ACCENT, 0.7),
                    borderColor: ACCENT,
                    borderWidth: 1, borderRadius: 4,
                }]
            },
            options: chartOptions('Rating Distribution', 'Rating', 'Number of Products')
        });
    }
}

function chartOptions(title, xLabel, yLabel) {
    return {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: { display: false },
            title: {
                display: true, text: title,
                color: '#eef0f6', font: { size: 16, weight: '600' }, padding: { bottom: 16 }
            },
            tooltip: {
                backgroundColor: '#141824',
                borderColor: 'rgba(255,255,255,0.1)',
                borderWidth: 1,
                titleColor: '#eef0f6',
                bodyColor: '#9aa4b2',
                padding: 10,
            }
        },
        scales: {
            x: {
                ticks: { color: MUTED, maxRotation: 45, font: { size: 11 } },
                grid: { color: BORDER },
                title: { display: true, text: xLabel, color: MUTED, font: { size: 12 } }
            },
            y: {
                ticks: { color: MUTED },
                grid: { color: BORDER },
                title: { display: true, text: yLabel, color: MUTED, font: { size: 12 } }
            }
        }
    };
}

// ===== PRODUCTS =====
function populateCategoryFilter(items) {
    const sel = document.getElementById('categoryFilter');
    const cats = [...new Set(items.map(i => i.category).filter(Boolean))].sort();
    sel.innerHTML = '<option value="all">All</option>' +
        cats.map(c => `<option value="${c}">${c}</option>`).join('');
}

function renderProductTable() {
    const container = document.getElementById('productTable');
    if (!productListFull.length) { container.innerHTML = '<p class="placeholder">No product list available.</p>'; return; }

    const search   = (document.getElementById('searchProduct')?.value || '').toLowerCase();
    const category = document.getElementById('categoryFilter')?.value || 'all';
    const sort     = document.getElementById('sortFilter')?.value || 'name_asc';

    let filtered = productListFull.filter(item => {
        const matchSearch = item.product_name.toLowerCase().includes(search);
        const matchCat    = category === 'all' || item.category === category;
        return matchSearch && matchCat;
    });

    const num = v => (typeof v === 'number' && !isNaN(v)) ? v : -Infinity;
    filtered.sort((a, b) => {
        switch (sort) {
            case 'price_high':    return num(b.price) - num(a.price);
            case 'price_low':     return num(a.price) - num(b.price);
            case 'rating_high':   return num(b.rating) - num(a.rating);
            case 'rating_low':    return num(a.rating) - num(b.rating);
            case 'discount_high': return num(b.discount_percentage) - num(a.discount_percentage);
            case 'discount_low':  return num(a.discount_percentage) - num(b.discount_percentage);
            case 'sales_high':    return num(b.sales) - num(a.sales);
            case 'sales_low':     return num(a.sales) - num(b.sales);
            default:              return a.product_name.localeCompare(b.product_name);
        }
    });

    const rows = filtered.map(item => `
        <tr>
            <td><strong>${item.product_name}</strong></td>
            <td>${item.category || 'N/A'}</td>
            <td>${item.price !== undefined ? '₹' + Math.round(item.price).toLocaleString() : 'N/A'}</td>
            <td>${item.rating != null ? item.rating.toFixed(1) : 'N/A'}</td>
            <td>${item.discount_percentage != null ? item.discount_percentage.toFixed(1) + '%' : 'N/A'}</td>
            <td>${item.sales !== undefined ? Math.round(item.sales).toLocaleString() : 'N/A'}</td>
        </tr>`).join('');

    container.innerHTML = `
        <table>
            <thead><tr>
                <th>Product</th><th>Category</th><th>Price</th>
                <th>Rating</th><th>Discount</th><th>Sales</th>
            </tr></thead>
            <tbody>${rows}</tbody>
        </table>`;
}

function renderProducts(ins) {
    // Top selling
    const topDiv = document.getElementById('topSelling');
    if (ins.top_selling_products && ins.top_selling_products.length) {
        const label = ins.sales_basis === 'review_count' ? 'Reviews' : 'Sales';
        topDiv.innerHTML = '<ul>' +
            ins.top_selling_products.slice(0,5)
                .map(i => `<li><strong>${i.product_name}</strong>: ${Math.round(i.sales).toLocaleString()} ${label}</li>`)
                .join('') + '</ul>';
    } else { topDiv.innerHTML = '<p class="placeholder">Top sellers data unavailable</p>'; }
}

// ===== MARKET BASKET =====
function renderBasket(ins) {
    const rulesDiv = document.getElementById('associationRules');
    const rules = ins.association_rules || [];
    const totalTx = ins.association_meta?.total_transactions || 0;

    if (rules.length) {
        rulesDiv.innerHTML = rules.slice(0,8).map(rule => {
            const suppPct = (rule.support * 100).toFixed(1);
            const confA   = (rule.confidence_a_to_b * 100).toFixed(1);
            return `<div class="bottle-card">
                <div class="bottle-title">${rule.product_a} ↔ ${rule.product_b}</div>
                <div class="bottle-content">When customers purchase <strong>${rule.product_a}</strong>, they also purchase <strong>${rule.product_b}</strong> in ${rule.count} out of ${totalTx} transactions. This happens <strong>${confA}%</strong> of the time.</div>
                <div class="bottle-stats">Support: ${suppPct}% | Confidence: ${confA}%</div>
            </div>`;
        }).join('');
    } else {
        rulesDiv.innerHTML = '<p class="placeholder">No association data available. Ensure your data contains transaction/order IDs.</p>';
    }

    const byProd = ins.association_by_product || {};
    const byProdDiv = document.getElementById('basketByProduct');
    const entries = Object.entries(byProd).slice(0,12);
    if (entries.length) {
        byProdDiv.innerHTML = entries.map(([product, items]) => {
            if (!items.length) return '';
            const top = items[0];
            const allItems = items.slice(0,3).map(i => `${i.product} (${i.count}x)`).join(', ');
            return `<div class="bottle-card">
                <div class="bottle-title">${product}</div>
                <div class="bottle-content"><strong>Often bought with:</strong> ${allItems}<br>
                When customers buy <strong>${product}</strong>, they frequently also purchase <strong>${top.product}</strong>. This occurs in <strong>${top.count}</strong> transactions.</div>
                <div class="bottle-stats">📦 ${items.length} complementary products identified</div>
            </div>`;
        }).join('');
    } else {
        byProdDiv.innerHTML = '<p class="placeholder">No product-level association data available.</p>';
    }
}

// ===== AI MODEL =====
function renderModel(ins) {
    const el = document.getElementById('modelAccuracy');
    const rm = ins.rating_model;
    if (rm && rm.accuracy !== undefined) {
        el.innerHTML = `
            <strong>🤖 Rating Prediction Model</strong><br><br>
            <strong>Model Performance Metrics:</strong><br>
            • Accuracy (R² Score): ${rm.accuracy.toFixed(1)}%<br>
            • RMSE: ${(rm.rmse || 0).toFixed(3)}<br>
            • R²: ${(rm.r2 || 0).toFixed(3)}<br><br>
            This model predicts product ratings based on price, discount, and category features.`;
    } else {
        el.textContent = '📊 Model ready for training (requires price, discount, and rating columns in your data)';
    }
}

// ===== CHAT =====
function renderQuickQuestions() {
    const questions = [
        'How many products?', 'Best performing category?', 'Average rating?',
        'Highest revenue products?', 'Discount insights?', 'Price insights?',
        'Products sold together?', 'What is market basket?'
    ];
    const container = document.getElementById('quickQuestions');
    container.innerHTML = questions.map(q =>
        `<button class="question-btn" onclick="sendMessage('${q.replace(/'/g, "\\'")}')">${q}</button>`
    ).join('');
}

async function sendMessage(message) {
    const msg = (message || '').trim();
    if (!msg) return;

    addChatMessage(msg, 'user');
    const typing = addTypingIndicator();

    try {
        const res  = await fetch(`${API_URL}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: msg })
        });
        const data = await res.json();
        typing.remove();
        addChatMessage(data.answer || data.error || 'No response', 'bot');
    } catch (err) {
        typing.remove();
        addChatMessage('❌ Error connecting to the server. Make sure the backend is running!', 'bot');
    }
}

function addChatMessage(text, role) {
    const box = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `<div class="message-content">${text.replace(/\n/g, '<br>')}</div>`;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

function addTypingIndicator() {
    const box = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = 'message bot';
    div.id = 'typingIndicator';
    div.innerHTML = `<div class="message-content"><span class="loading-dot"></span> Thinking...</div>`;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
    return div;
}

document.getElementById('clearChatBtn').addEventListener('click', () => {
    document.getElementById('chatMessages').innerHTML = `
        <div class="message bot">
            <div class="message-content">Chat cleared. Ask me anything about your data!</div>
        </div>`;
});

// ===== FILTER EVENTS =====
document.getElementById('searchProduct')?.addEventListener('input', renderProductTable);
document.getElementById('categoryFilter')?.addEventListener('change', renderProductTable);
document.getElementById('sortFilter')?.addEventListener('change', renderProductTable);

// ===== STATUS =====
function showStatus(msg, type) {
    const el = document.getElementById('uploadStatus');
    el.textContent = msg;
    el.className = 'status-message' + (type ? ` ${type}` : '');
}

// ===== HEALTH CHECK =====
async function checkHealth() {
    const pill = document.getElementById('statusPill');
    try {
        const res = await fetch(`${API_URL}/health`);
        await res.json();
        pill.textContent = '● ACTIVE';
        pill.classList.remove('offline');
    } catch {
        pill.textContent = '● OFFLINE';
        pill.classList.add('offline');
        showStatus('⚠️ Backend server is not running. Please start the backend first!', 'error');
    }
}

// ===== HELPERS =====
function truncate(str, n) { return str.length > n ? str.slice(0, n) + '…' : str; }
function hexAlpha(hex, alpha) {
    const r = parseInt(hex.slice(1,3),16);
    const g = parseInt(hex.slice(3,5),16);
    const b = parseInt(hex.slice(5,7),16);
    return `rgba(${r},${g},${b},${alpha})`;
}

// ===== INIT =====
window.addEventListener('load', () => {
    checkHealth();
    document.getElementById('reportDate').textContent = new Date().toLocaleDateString();
});
