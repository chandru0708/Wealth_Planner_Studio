const form = document.getElementById('plannerForm');
const riskLabel = document.getElementById('riskLabel');
const riskSub = document.getElementById('riskSub');
const confidenceValue = document.getElementById('confidenceValue');
const healthValue = document.getElementById('healthValue');
const sentimentValue = document.getElementById('sentimentValue');
const savingsRate = document.getElementById('savingsRate');
const dtiValue = document.getElementById('dtiValue');
const emergencyValue = document.getElementById('emergencyValue');
const annualSaveValue = document.getElementById('annualSaveValue');
const adviceList = document.getElementById('adviceList');
const goalBadge = document.getElementById('goalBadge');
const themeToggle = document.querySelector('[data-theme-toggle]');
const root = document.documentElement;

const nlpCategory = document.getElementById('nlpCategory');
const nlpKeywords = document.getElementById('nlpKeywords');
const nlpOrganizations = document.getElementById('nlpOrganizations');
const nlpSummary = document.getElementById('nlpSummary');

const dlTrend = document.getElementById('dlTrend');
const dlConfidence = document.getElementById('dlConfidence');
const dlVolatility = document.getElementById('dlVolatility');
const dlImprovement = document.getElementById('dlImprovement');

const slmSummary = document.getElementById('slmSummary');

const agentPriority = document.getElementById('agentPriority');
const agentAction = document.getElementById('agentAction');
const agentSafety = document.getElementById('agentSafety');
const agentHumanLoop = document.getElementById('agentHumanLoop');

const scenarioList = document.getElementById('scenarioList');
const confusionMatrixBox = document.getElementById('confusionMatrixBox');
const rocBox = document.getElementById('rocBox');

let currentTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
root.setAttribute('data-theme', currentTheme);

themeToggle?.addEventListener('click', () => {
  currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
  root.setAttribute('data-theme', currentTheme);
});

const chartCtx = document.getElementById('allocationChart');

let allocationChart = new Chart(chartCtx, {
  type: 'doughnut',
  data: {
    labels: ['Equity', 'Debt', 'Gold', 'Cash'],
    datasets: [
      {
        data: [45, 35, 10, 10],
        backgroundColor: ['#01696f', '#0f5d8c', '#b8860b', '#8b9095'],
        borderWidth: 0,
        hoverOffset: 8
      }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '68%',
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: '#9ba3a7',
          usePointStyle: true,
          boxWidth: 10,
          padding: 18
        }
      }
    }
  }
});

function formatINR(value) {
  return new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: 0
  }).format(value || 0);
}

function formatValue(value, fallback = 'Not available') {
  if (value === null || value === undefined) return fallback;
  const text = String(value).trim();
  return text ? text : fallback;
}

function formatList(value, fallback = 'Not detected', limit = null) {
  if (!Array.isArray(value)) return 'Not available';

  const cleaned = value
    .map(item => String(item).trim())
    .filter(Boolean);

  const finalList = limit ? cleaned.slice(0, limit) : cleaned;
  return finalList.length ? finalList.join(', ') : fallback;
}

function renderAdvice(items) {
  if (!items || !items.length) {
    adviceList.innerHTML = '<div class="empty-state compact"><p>No recommendations available.</p></div>';
    return;
  }

  adviceList.innerHTML = items
    .map(item => `<article class="advice-item">${item}</article>`)
    .join('');
}

function renderScenarios(items) {
  if (!items || !items.length) {
    scenarioList.innerHTML = '<div class="empty-state compact"><p>No scenario outputs available.</p></div>';
    return;
  }

  scenarioList.innerHTML = items.map(item => `
    <article class="scenario-card">
      <h4>${formatValue(item.scenario_name, 'Scenario')}</h4>
      <div class="scenario-meta">
        <span>Return: ${item.stress_result?.projected_return_pct ?? '--'}%</span>
        <span>Risk: ${formatValue(item.stress_result?.projected_risk, '--')}</span>
      </div>
      <p>${formatValue(item.commentary, 'No commentary available.')}</p>
    </article>
  `).join('');
}

function riskTone(risk) {
  if (risk === 'Aggressive') return 'Growth-oriented investor profile';
  if (risk === 'Conservative') return 'Capital-preservation investor profile';
  return 'Balanced investor profile';
}

function renderConfusionMatrix(confusionMatrix) {
  if (!confusionMatrix || !Array.isArray(confusionMatrix.labels) || !Array.isArray(confusionMatrix.matrix)) {
    confusionMatrixBox.innerHTML = '<div class="empty-state compact"><p>Confusion matrix not available.</p></div>';
    return;
  }

  const labels = confusionMatrix.labels;
  const matrix = confusionMatrix.matrix;

  let html = `
    <div class="matrix-row matrix-header">
      <strong>Actual \\ Pred</strong>
      ${labels.map(label => `<strong>${label}</strong>`).join('')}
    </div>
  `;

  matrix.forEach((row, rowIndex) => {
    html += `
      <div class="matrix-row">
        <span class="matrix-label">${labels[rowIndex] ?? `Class ${rowIndex + 1}`}</span>
        ${row.map(value => `<span class="matrix-cell">${value}</span>`).join('')}
      </div>
    `;
  });

  confusionMatrixBox.innerHTML = html;
}

function renderRoc(rocData) {
  if (!rocData) {
    rocBox.innerHTML = 'ROC information not available.';
    return;
  }

  const fpr = Array.isArray(rocData.fpr) ? rocData.fpr : [];
  const tpr = Array.isArray(rocData.tpr) ? rocData.tpr : [];

  rocBox.innerHTML = `
    <div class="split-emphasis">
      <div>
        <span class="mini-label">AUC</span>
        <strong>${formatValue(rocData.auc, '--')}</strong>
      </div>
      <div class="roc-points">
        ${
          fpr.length
            ? fpr.map((value, i) => `
              <span class="roc-point">(${value}, ${tpr[i] ?? '--'})</span>
            `).join('')
            : '<span class="roc-point">No ROC points available</span>'
        }
      </div>
    </div>
  `;
}

renderConfusionMatrix(window.initialConfusionMatrix);
renderRoc(window.initialRocCurve);

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const btn = form.querySelector('button[type="submit"]');
  btn.disabled = true;
  btn.textContent = 'Analyzing...';

  const payload = Object.fromEntries(new FormData(form).entries());

  try {
    const response = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const contentType = response.headers.get('content-type') || '';

    let data;
    if (contentType.includes('application/json')) {
      data = await response.json();
    } else {
      const text = await response.text();
      throw new Error(text || `Unexpected response type: ${contentType}`);
    }

    if (!response.ok) {
      throw new Error(data?.message || `HTTP ${response.status}`);
    }

    const ml = data.ml_result || {};
    const nlp = data.nlp_result || {};
    const profile = data.profile || {};
    const recommendations = Array.isArray(data.recommendations) ? data.recommendations : [];
    const dl = data.dl_result || {};
    const dlComparison = data.dl_comparison || {};
    const agent = data.agent_result || {};
    const scenarios = Array.isArray(data.scenario_results) ? data.scenario_results : [];
    const mlEvidence = data.ml_evidence || {};

    riskLabel.textContent = formatValue(ml.risk, '--');
    riskSub.textContent = riskTone(ml.risk || 'Moderate');

    confidenceValue.textContent =
      ml.confidence !== undefined ? `${ml.confidence}%` : '--';

    healthValue.textContent =
      ml.financial_health !== undefined ? `${ml.financial_health}/100` : '--';

    sentimentValue.textContent =
      nlp.sentiment !== undefined && nlp.sentiment_score !== undefined
        ? `${nlp.sentiment} (${nlp.sentiment_score > 0 ? '+' : ''}${nlp.sentiment_score})`
        : 'Not available';

    if (ml.summary) {
      savingsRate.textContent =
        ml.summary.savings_rate !== undefined ? `${ml.summary.savings_rate}%` : '--';

      dtiValue.textContent =
        ml.summary.debt_to_income !== undefined ? ml.summary.debt_to_income : '--';

      emergencyValue.textContent =
        ml.summary.emergency_months !== undefined ? `${ml.summary.emergency_months} months` : '--';

      annualSaveValue.textContent =
        ml.summary.annual_savings_capacity !== undefined
          ? `₹${formatINR(ml.summary.annual_savings_capacity)}`
          : '--';
    } else {
      const income = Number(profile.income || 0);
      const expense = Number(profile.expense || 0);
      const savings = Number(profile.savings || 0);
      const debt = Number(profile.debt || 0);

      const monthlySavings = income - expense;
      const annualSavings = monthlySavings * 12;
      const savingsRateValue = income > 0 ? ((monthlySavings / income) * 100).toFixed(1) : '--';
      const dti = income > 0 ? (debt / (income * 12)).toFixed(2) : '--';
      const emergencyMonths = expense > 0 ? (savings / expense).toFixed(1) : '--';

      savingsRate.textContent = savingsRateValue !== '--' ? `${savingsRateValue}%` : '--';
      dtiValue.textContent = dti;
      emergencyValue.textContent = emergencyMonths !== '--' ? `${emergencyMonths} months` : '--';
      annualSaveValue.textContent = `₹${formatINR(annualSavings)}`;
    }

    goalBadge.textContent = formatValue(profile.goal, 'Wealth Creation');

    if (ml.allocation && typeof ml.allocation === 'object') {
      allocationChart.data.labels = Object.keys(ml.allocation);
      allocationChart.data.datasets[0].data = Object.values(ml.allocation);
      allocationChart.update();
    }

    renderAdvice(recommendations);

    nlpCategory.textContent = formatValue(nlp.category, 'Not available');
    nlpKeywords.textContent = formatList(nlp.keywords, 'Not detected', 5);
    nlpOrganizations.textContent = formatList(nlp.entities?.organizations, 'Not detected');
    nlpSummary.textContent = formatValue(nlp.summary, 'Not available');

    dlTrend.textContent = formatValue(dl.forecast?.trend_label, 'Not available');
    dlConfidence.textContent =
      dl.forecast?.confidence !== undefined ? `${dl.forecast.confidence}%` : 'Not available';
    dlVolatility.textContent = formatValue(dl.forecast?.volatility, 'Not available');
    dlImprovement.textContent =
      dlComparison.absolute_improvement !== undefined ? `+${dlComparison.absolute_improvement}` : 'Not available';

    slmSummary.textContent = formatValue(data.slm_summary, 'No advisory summary available.');
    slmSummary.classList.add('clamped-text');

    agentPriority.textContent = formatValue(agent.agent_priority, 'Not available');
    agentAction.textContent = formatValue(agent.agent_action, 'Not available');
    agentSafety.textContent =
      agent.safety?.approved !== undefined
        ? (agent.safety.approved ? 'Approved' : 'Escalated')
        : 'Not available';
    agentHumanLoop.textContent =
      agent.safety?.human_in_loop !== undefined
        ? (agent.safety.human_in_loop ? 'Required' : 'Not required')
        : 'Not available';

    renderScenarios(scenarios);
    renderConfusionMatrix(mlEvidence.confusion_matrix);
    renderRoc(mlEvidence.roc_curve);
  } catch (error) {
    console.error('Fetch error:', error);

    adviceList.innerHTML =
      `<div class="empty-state compact"><p>${formatValue(error.message, 'Unable to generate recommendation.')}</p></div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate Recommendation';
  }
}); 