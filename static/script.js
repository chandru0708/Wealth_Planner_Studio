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
    datasets: [{
      data: [45, 35, 10, 10],
      backgroundColor: ['#01696f', '#0f5d8c', '#b8860b', '#8b9095'],
      borderWidth: 0,
      hoverOffset: 8,
    }],
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
          padding: 18,
        },
      },
    },
  },
});

function formatINR(value) {
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(value);
}

function renderAdvice(items) {
  if (!items || !items.length) {
    adviceList.innerHTML = '<div class="empty-state compact"><p>No recommendations available.</p></div>';
    return;
  }
  adviceList.innerHTML = items.map(item => `<article class="advice-item">${item}</article>`).join('');
}

function riskTone(risk) {
  if (risk === 'Aggressive') return 'Growth-oriented investor profile';
  if (risk === 'Conservative') return 'Capital-preservation investor profile';
  return 'Balanced investor profile';
}

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
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error('Fetch error:', error);
}

    riskLabel.textContent = data.risk;
    riskSub.textContent = riskTone(data.risk);
    confidenceValue.textContent = `${data.confidence}%`;
    healthValue.textContent = `${data.financial_health}/100`;
    sentimentValue.textContent = `${data.sentiment} (${data.sentiment_score > 0 ? '+' : ''}${data.sentiment_score})`;
    savingsRate.textContent = `${data.summary.savings_rate}%`;
    dtiValue.textContent = data.summary.debt_to_income;
    emergencyValue.textContent = `${data.summary.emergency_months} months`;
    annualSaveValue.textContent = `₹${formatINR(data.summary.annual_savings_capacity)}`;
    goalBadge.textContent = data.summary.goal;

    allocationChart.data.labels = Object.keys(data.allocation);
    allocationChart.data.datasets[0].data = Object.values(data.allocation);
    allocationChart.update();

    renderAdvice(data.advice);
  } catch (error) {
    adviceList.innerHTML = '<div class="empty-state compact"><p>Unable to generate recommendation. Check backend and model artifact path.</p></div>';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate Recommendation';
  }
});
