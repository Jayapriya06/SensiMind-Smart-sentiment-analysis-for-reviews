document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const reviewInput = document.getElementById('reviewInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const demoBtn = document.getElementById('demoBtn');
    const clearBtn = document.getElementById('clearBtn');
    const fileInput = document.getElementById('fileInput');
    const dropZone = document.getElementById('dropZone');
    const resultsList = document.getElementById('resultsList');
    const loader = document.getElementById('loader');

    // State
    let allResults = [];
    let sentimentChart = null;

    const stats = {
        total: document.getElementById('totalCount'),
        pos: document.getElementById('posCount'),
        neg: document.getElementById('negCount'),
        neu: document.getElementById('neuCount'),
        mix: document.getElementById('mixCount')
    };

    // Initialize/Update Chart
    function updateChart(counts) {
        const ctx = document.getElementById('sentimentChart').getContext('2d');
        const total = counts.pos + counts.neg + counts.neu + counts.mix;
        const percentages = total === 0 ? [0, 0, 0, 0] : [
            ((counts.pos / total) * 100).toFixed(1),
            ((counts.neg / total) * 100).toFixed(1),
            ((counts.neu / total) * 100).toFixed(1),
            ((counts.mix / total) * 100).toFixed(1)
        ];

        if (sentimentChart) {
            sentimentChart.data.datasets[0].data = [counts.pos, counts.neg, counts.neu, counts.mix];
            sentimentChart.update();
        } else {
            sentimentChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Positive', 'Negative', 'Neutral', 'Mixed'],
                    datasets: [{
                        data: [counts.pos, counts.neg, counts.neu, counts.mix],
                        backgroundColor: ['#22c55e', '#ef4444', '#eab308', '#a855f7'],
                        borderWidth: 0,
                        hoverOffset: 10
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (context) => {
                                    const value = context.raw;
                                    const perc = total === 0 ? 0 : ((value / total) * 100).toFixed(1);
                                    return `${context.label}: ${value} (${perc}%)`;
                                }
                            }
                        }
                    },
                    cutout: '70%'
                }
            });
        }
    }

    // Update UI
    function updateUI(newData) {
        // Handle single object or array
        const incoming = Array.isArray(newData.results) ? newData.results : [newData];
        
        // Accumulate state
        allResults = [...incoming, ...allResults];

        // Calculate aggregate stats
        const summary = allResults.reduce((acc, curr) => {
            acc.total++;
            const s = curr.sentiment.toLowerCase();
            if (s === 'positive') acc.pos++;
            else if (s === 'negative') acc.neg++;
            else if (s === 'neutral') acc.neu++;
            else if (s === 'mixed') acc.mix++;
            return acc;
        }, { total: 0, pos: 0, neg: 0, neu: 0, mix: 0 });

        // Update counts
        stats.total.innerText = summary.total;
        stats.pos.innerText = summary.pos;
        stats.neg.innerText = summary.neg;
        stats.neu.innerText = summary.neu;
        stats.mix.innerText = summary.mix;

        // Update chart
        updateChart(summary);

        // Render List
        renderList();
    }

    function renderList() {
        if (allResults.length === 0) {
            resultsList.innerHTML = `<div style="text-align: center; color: var(--text-muted); margin-top: 2rem;">No history yet.</div>`;
            return;
        }

        resultsList.innerHTML = allResults.map(item => `
            <div class="result-item ${item.sentiment.toLowerCase()}">
                <div class="result-header">
                    <span style="font-weight: 600; color: var(--${item.sentiment.toLowerCase()})">${item.sentiment}</span>
                    <span style="color: var(--text-muted)">Confidence: ${item.confidence}%</span>
                </div>
                <p class="result-text">${item.text}</p>
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 5px;">
                    POS: ${Math.round(item.scores.pos*100)}% | NEG: ${Math.round(item.scores.neg*100)}% | NEU: ${Math.round(item.scores.neu*100)}%
                </div>
            </div>
        `).join('');
    }

    // Actions
    async function analyzeText(text) {
        if (!text.trim()) return;
        toggleLoader(true);
        try {
            const formData = new FormData();
            formData.append('text', text);
            const response = await fetch('/analyze', { method: 'POST', body: formData });
            const data = await response.json();
            updateUI(data);
            reviewInput.value = ''; // Reset input
        } catch (error) {
            console.error('Error:', error);
        } finally {
            toggleLoader(false);
        }
    }

    async function uploadFile(file) {
        toggleLoader(true);
        try {
            const formData = new FormData();
            formData.append('file', file);
            const response = await fetch('/upload', { method: 'POST', body: formData });
            const data = await response.json();
            updateUI(data);
        } catch (error) {
            console.error('Error:', error);
        } finally {
            toggleLoader(false);
        }
    }

    const toggleLoader = (show) => { loader.style.display = show ? 'flex' : 'none'; };

    // Event Listeners
    analyzeBtn.addEventListener('click', () => analyzeText(reviewInput.value));
    demoBtn.addEventListener('click', async () => {
        toggleLoader(true);
        const r = await fetch('/demo');
        const data = await r.json();
        updateUI(data);
        toggleLoader(false);
    });

    clearBtn.addEventListener('click', () => {
        allResults = [];
        updateUI({ results: [] });
    });

    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => { if (e.target.files[0]) uploadFile(e.target.files[0]); });

    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.style.borderColor = 'var(--primary)'; });
    dropZone.addEventListener('dragleave', () => { dropZone.style.borderColor = 'var(--card-border)'; });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--card-border)';
        if (e.dataTransfer.files[0]) uploadFile(e.dataTransfer.files[0]);
    });

    // Initial Chart
    updateChart({ pos: 0, neg: 0, neu: 0, mix: 0 });
});
