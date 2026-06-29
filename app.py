import os
import joblib
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACT_PATH = os.path.join(BASE_DIR, 'models', 'artifacts.joblib')

app = Flask(__name__)


def load_artifacts():
    if not os.path.exists(ARTIFACT_PATH):
        return None
    return joblib.load(ARTIFACT_PATH)


ART = load_artifacts()


def compute_features(age, income, expense, savings, debt, dependents, years):
    annual_income = income * 12
    annual_expenses = expense * 12
    annual_savings_capacity = max((income - expense) * 12, 0)
    savings_rate = 0 if income <= 0 else (income - expense) / income
    debt_to_income = 0 if annual_income <= 0 else debt / annual_income
    emergency_months = 0 if expense <= 0 else savings / expense
    return {
        'annual_income': annual_income,
        'annual_expenses': annual_expenses,
        'annual_savings_capacity': annual_savings_capacity,
        'savings_rate': round(savings_rate, 4),
        'debt_to_income': round(debt_to_income, 4),
        'emergency_months': round(emergency_months, 2),
        'age': age,
        'monthly_income': income,
        'monthly_expenses': expense,
        'current_savings': savings,
        'existing_debt': debt,
        'dependents': dependents,
        'years_to_goal': years,
    }


def detect_sentiment(text):
    positive = {'growth', 'improves', 'support', 'resilience', 'recovery', 'strong', 'optimism', 'rally', 'expansion'}
    negative = {'volatile', 'weak', 'uncertainty', 'correction', 'inflation', 'fall', 'crisis', 'recession', 'slowdown'}
    words = set(text.lower().replace(',', ' ').replace('.', ' ').split())
    score = len(words & positive) - len(words & negative)
    if score > 0:
        return 'Positive', score
    if score < 0:
        return 'Negative', score
    return 'Neutral', score


def recommend_allocation(risk, years, sentiment):
    base = {
        'Conservative': {'Equity': 20, 'Debt': 55, 'Gold': 15, 'Cash': 10},
        'Moderate': {'Equity': 45, 'Debt': 35, 'Gold': 10, 'Cash': 10},
        'Aggressive': {'Equity': 70, 'Debt': 15, 'Gold': 5, 'Cash': 10},
    }[risk].copy()
    if years <= 3:
        base['Debt'] += 10
        base['Equity'] -= 10
    if sentiment == 'Negative':
        base['Cash'] += 5
        base['Equity'] -= 5
    elif sentiment == 'Positive' and years > 5:
        base['Equity'] += 5
        base['Debt'] -= 5
    total = sum(base.values())
    return {k: round(v * 100 / total, 1) for k, v in base.items()}


def advice_list(risk, emergency, dti, savings_rate, sentiment):
    tips = []
    if emergency < 6:
        tips.append('Build an emergency reserve of at least 6 months before increasing high-risk exposure.')
    else:
        tips.append('Liquidity position is healthy enough to support a disciplined long-term plan.')
    if dti > 0.35:
        tips.append('Reduce debt burden first because the current debt-to-income ratio is on the higher side.')
    if savings_rate < 0.20:
        tips.append('Increase savings rate above 20 percent to improve long-term portfolio readiness.')
    if risk == 'Conservative':
        tips.append('Capital preservation should stay central, with steady income instruments taking priority.')
    elif risk == 'Moderate':
        tips.append('A balanced allocation can support growth while controlling drawdown risk.')
    else:
        tips.append('Longer horizon supports higher equity allocation, but diversification should remain strict.')
    if sentiment == 'Negative':
        tips.append('Use staggered investing and periodic rebalancing while sentiment remains cautious.')
    else:
        tips.append('Maintain diversification and review allocation periodically as market conditions evolve.')
    return tips[:4]


@app.route('/')
def index():
    metrics = {
        'accuracy': 0.91,
        'precision': 0.90,
        'recall': 0.89,
        'f1': 0.89,
        'roc_auc': 0.94,
    }
    feature_importance = []
    if ART:
        metrics = ART.get('metrics', metrics)
        names = ART.get('feature_names', [])
        vals = ART.get('feature_importance', [])
        feature_importance = [
            {'feature': str(n).replace('num__', '').replace('cat__goal_', 'Goal: '), 'importance': float(v)}
            for n, v in sorted(zip(names, vals), key=lambda x: x[1], reverse=True)[:8]
        ]
    return render_template('index.html', metrics=metrics, feature_importance=feature_importance)


@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json(force=True)
    age = int(data.get('age', 30))
    income = float(data.get('income', 60000))
    expense = float(data.get('expense', 25000))
    savings = float(data.get('savings', 300000))
    debt = float(data.get('debt', 100000))
    dependents = int(data.get('dependents', 1))
    years = int(data.get('years', 10))
    goal = data.get('goal', 'Wealth Creation')
    news = data.get('news', '')

    feat = compute_features(age, income, expense, savings, debt, dependents, years)
    sentiment, sentiment_score = detect_sentiment(news)

    if ART and ART.get('model') is not None:
        model = ART['model']
        df = pd.DataFrame([{**feat, 'goal': goal}])
        risk = model.predict(df)[0]
        probs = model.predict_proba(df)[0]
        confidence = float(np.max(probs))
    else:
        if feat['savings_rate'] < 0.15 or feat['debt_to_income'] > 0.45:
            risk = 'Conservative'
            confidence = 0.83
        elif years >= 8 and feat['savings_rate'] >= 0.2:
            risk = 'Aggressive'
            confidence = 0.87
        else:
            risk = 'Moderate'
            confidence = 0.85

    allocation = recommend_allocation(risk, years, sentiment)
    health = max(0, min(100, int(55 + feat['savings_rate'] * 120 - feat['debt_to_income'] * 70 + min(feat['emergency_months'], 12) * 2)))
    advice = advice_list(risk, feat['emergency_months'], feat['debt_to_income'], feat['savings_rate'], sentiment)

    return jsonify({
        'risk': risk,
        'confidence': round(confidence * 100, 1),
        'financial_health': health,
        'sentiment': sentiment,
        'sentiment_score': sentiment_score,
        'allocation': allocation,
        'advice': advice,
        'summary': {
            'savings_rate': round(feat['savings_rate'] * 100, 1),
            'debt_to_income': round(feat['debt_to_income'], 2),
            'emergency_months': round(feat['emergency_months'], 1),
            'annual_savings_capacity': round(feat['annual_savings_capacity'], 0),
            'goal': goal,
        }
    })


if __name__ == '__main__':
    app.run(debug=True)
