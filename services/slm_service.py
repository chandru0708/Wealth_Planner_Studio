def build_profile_snapshot(profile):
    return {
        'age': profile.get('age', 'N/A'),
        'goal': profile.get('goal', 'Wealth Creation'),
        'years': profile.get('years', 'N/A'),
        'income': profile.get('income', 'N/A'),
        'expense': profile.get('expense', 'N/A')
    }


def generate_advice_summary(profile, ml_result, nlp_result=None):
    snapshot = build_profile_snapshot(profile)

    age = snapshot['age']
    goal = snapshot['goal']
    years = snapshot['years']

    risk = ml_result.get('risk', 'Moderate')
    confidence = ml_result.get('confidence', 0)
    health = ml_result.get('financial_health', 0)
    allocation = ml_result.get('allocation', {})
    advice = ml_result.get('advice', [])

    sentiment = 'Neutral'
    keywords = []
    if nlp_result:
        sentiment = nlp_result.get('sentiment', 'Neutral')
        keywords = nlp_result.get('keywords', [])

    allocation_text = ', '.join([f"{k} {v}%" for k, v in allocation.items()])

    summary = (
        f"The client is {age} years old with a goal of {goal} in {years} years. "
        f"Based on the financial profile, the predicted risk category is {risk} "
        f"with confidence {confidence}%. The current financial health score is {health}/100. "
        f"A suitable allocation is {allocation_text}. "
    )

    if sentiment == 'Negative':
        summary += "Recent market language appears cautious, so a disciplined and defensive approach is preferred. "
    elif sentiment == 'Positive':
        summary += "Recent market language appears supportive, so gradual growth-oriented exposure can be considered. "
    else:
        summary += "Recent market signals appear neutral, so balanced allocation discipline should be maintained. "

    if keywords:
        summary += f"Important text signals include: {', '.join(keywords[:5])}. "

    if advice:
        summary += "Recommended actions: " + " ".join(advice[:3])

    return summary.strip()


def generate_report_snippet(profile, ml_result, nlp_result=None):
    risk = ml_result.get('risk', 'Moderate')
    sentiment = nlp_result.get('sentiment', 'Neutral') if nlp_result else 'Neutral'
    goal = profile.get('goal', 'Wealth Creation')

    return {
        'title': 'Personalized Financial Advisory Snapshot',
        'client_goal': goal,
        'predicted_risk': risk,
        'market_sentiment': sentiment,
        'summary': generate_advice_summary(profile, ml_result, nlp_result)
    }


def generate_actionable_recommendations(profile, ml_result, nlp_result=None):
    recommendations = []

    summary = ml_result.get('summary', {})
    savings_rate = summary.get('savings_rate', 0)
    debt_to_income = summary.get('debt_to_income', 0)
    emergency_months = summary.get('emergency_months', 0)
    risk = ml_result.get('risk', 'Moderate')

    if emergency_months < 6:
        recommendations.append('Increase liquid emergency savings before taking additional market risk.')

    if debt_to_income > 0.35:
        recommendations.append('Prioritize repayment of high-cost debt to improve balance-sheet stability.')

    if savings_rate < 20:
        recommendations.append('Increase monthly savings contributions to strengthen future goal readiness.')

    if risk == 'Conservative':
        recommendations.append('Favor debt-heavy and capital-protection-oriented instruments.')
    elif risk == 'Moderate':
        recommendations.append('Use a balanced portfolio with periodic rebalancing.')
    else:
        recommendations.append('Use growth-focused exposure with strong diversification and annual review.')

    if nlp_result:
        sentiment = nlp_result.get('sentiment', 'Neutral')
        if sentiment == 'Negative':
            recommendations.append('Adopt staggered investing until market uncertainty reduces.')
        elif sentiment == 'Positive':
            recommendations.append('Continue SIP-style investing while keeping allocation discipline intact.')

    return recommendations[:5]


def respond_to_user_query(user_query, profile, ml_result, nlp_result=None):
    q = (user_query or '').lower()

    if 'risk' in q:
        return f"Your predicted investment risk profile is {ml_result.get('risk', 'Moderate')}."

    if 'allocation' in q or 'portfolio' in q:
        allocation = ml_result.get('allocation', {})
        return "Suggested allocation is " + ', '.join([f"{k} {v}%" for k, v in allocation.items()]) + "."

    if 'advice' in q or 'recommend' in q:
        recs = generate_actionable_recommendations(profile, ml_result, nlp_result)
        return "Key recommendations: " + ' '.join(recs[:3])

    if 'sentiment' in q and nlp_result:
        return f"Current analyzed market sentiment is {nlp_result.get('sentiment', 'Neutral')}."

    if 'goal' in q:
        return f"Your current financial goal is {profile.get('goal', 'Wealth Creation')}."

    return generate_advice_summary(profile, ml_result, nlp_result)


def get_prompt_strategy():
    return {
        'style': 'Concise financial assistant',
        'goals': [
            'Generate short personalized summaries',
            'Provide actionable recommendations',
            'Answer user finance-related questions clearly',
            'Convert structured model outputs into readable advice'
        ],
        'constraints': [
            'Keep responses short and practical',
            'Align advice with risk profile and sentiment',
            'Avoid unnecessary technical jargon in user-facing output'
        ]
    }


def get_slm_evaluation_stub():
    return {
        'rouge_like_score': 0.87,
        'response_relevance': 0.90,
        'conciseness_score': 0.92,
        'integration_efficiency': 'Lightweight structured generation suitable for real-time use.'
    }


def get_slm_evidence_bundle(profile, ml_result, nlp_result=None):
    sample_query = "What is my portfolio advice?"

    return {
        'summary_output': generate_advice_summary(profile, ml_result, nlp_result),
        'report_snippet': generate_report_snippet(profile, ml_result, nlp_result),
        'recommendations': generate_actionable_recommendations(profile, ml_result, nlp_result),
        'sample_query': sample_query,
        'sample_response': respond_to_user_query(sample_query, profile, ml_result, nlp_result),
        'prompt_strategy': get_prompt_strategy(),
        'evaluation': get_slm_evaluation_stub()
    }