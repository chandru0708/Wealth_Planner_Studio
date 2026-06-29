from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import HTTPException

from services.ml_service import (
    predict_risk_profile,
    get_model_metrics,
    get_feature_importance,
    get_confusion_matrix,
    get_roc_curve_data,
    get_ml_evidence_bundle
)

from services.nlp_service import (
    analyze_text,
    get_nlp_evidence_bundle
)

from services.slm_service import (
    generate_advice_summary,
    generate_report_snippet,
    generate_actionable_recommendations,
    respond_to_user_query,
    get_slm_evidence_bundle
)

from services.genai_service import (
    simulate_scenarios,
    get_genai_evidence_bundle
)

from services.agent_service import run_agent

from services.dl_service import (
    simulate_dl_forecast,
    compare_with_ml_baseline,
    get_dl_evidence_bundle
)

app = Flask(__name__)


class APIValidationError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@app.errorhandler(APIValidationError)
def handle_api_validation_error(error):
    return jsonify({
        'status': 'error',
        'message': error.message
    }), error.status_code


@app.errorhandler(HTTPException)
def handle_http_exception(error):
    return jsonify({
        'status': 'error',
        'message': error.description,
        'code': error.code
    }), error.code


@app.errorhandler(Exception)
def handle_generic_exception(error):
    return jsonify({
        'status': 'error',
        'message': str(error)
    }), 500


def get_json_data():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        raise APIValidationError('Invalid JSON body. Expected a JSON object.')
    return data


def parse_int(data, key, default=None, minimum=None, maximum=None, required=False):
    value = data.get(key, default)

    if required and (value is None or value == ''):
        raise APIValidationError(f'Missing required field: {key}')

    if value in (None, ''):
        return default

    try:
        value = int(value)
    except (TypeError, ValueError):
        raise APIValidationError(f'Field "{key}" must be an integer')

    if minimum is not None and value < minimum:
        raise APIValidationError(f'Field "{key}" must be at least {minimum}')

    if maximum is not None and value > maximum:
        raise APIValidationError(f'Field "{key}" must be at most {maximum}')

    return value


def parse_float(data, key, default=None, minimum=None, maximum=None, required=False):
    value = data.get(key, default)

    if required and (value is None or value == ''):
        raise APIValidationError(f'Missing required field: {key}')

    if value in (None, ''):
        return default

    try:
        value = float(value)
    except (TypeError, ValueError):
        raise APIValidationError(f'Field "{key}" must be a number')

    if minimum is not None and value < minimum:
        raise APIValidationError(f'Field "{key}" must be at least {minimum}')

    if maximum is not None and value > maximum:
        raise APIValidationError(f'Field "{key}" must be at most {maximum}')

    return value


def parse_profile(data):
    allowed_goals = {
        'Emergency Fund',
        'Retirement',
        'Wealth Creation',
        'House Purchase',
        'Child Education'
    }

    goal = (data.get('goal') or 'Wealth Creation').strip()
    if goal not in allowed_goals:
        raise APIValidationError('Invalid goal selected')

    profile = {
        'age': parse_int(data, 'age', default=30, minimum=18, maximum=100),
        'income': parse_float(data, 'income', default=60000, minimum=0),
        'expense': parse_float(data, 'expense', default=25000, minimum=0),
        'savings': parse_float(data, 'savings', default=300000, minimum=0),
        'debt': parse_float(data, 'debt', default=100000, minimum=0),
        'dependents': parse_int(data, 'dependents', default=1, minimum=0, maximum=20),
        'years': parse_int(data, 'years', default=10, minimum=1, maximum=60),
        'goal': goal
    }

    return profile


def default_nlp_result():
    return {
        'original_text': '',
        'preprocessing': {
            'original_length': 0,
            'token_count': 0,
            'normalized': True,
            'special_characters_removed': True
        },
        'sentiment': 'Neutral',
        'sentiment_score': 0,
        'positive_matches': 0,
        'negative_matches': 0,
        'category': 'general_finance',
        'category_scores': {},
        'keywords': [],
        'entities': {
            'organizations': [],
            'economic_terms': [],
            'financial_assets': [],
            'numeric_values': []
        },
        'summary': ''
    }


def safe_dict(value, default=None):
    if isinstance(value, dict):
        return value
    return default if default is not None else {}


def safe_list(value, default=None):
    if isinstance(value, list):
        return value
    return default if default is not None else []


@app.route('/')
def index():
    return render_template(
        'index.html',
        metrics=get_model_metrics(),
        feature_importance=get_feature_importance(),
        confusion_matrix=get_confusion_matrix(),
        roc_curve=get_roc_curve_data()
    )


@app.route('/predict', methods=['POST'])
def predict():
    data = get_json_data()
    profile = parse_profile(data)

    market_text = (data.get('news') or '').strip()

    nlp_result = analyze_text(market_text) if market_text else default_nlp_result()
    nlp_result = safe_dict(nlp_result, default_nlp_result())

    sentiment = nlp_result.get('sentiment', 'Neutral')

    ml_result = predict_risk_profile(
        age=profile['age'],
        income=profile['income'],
        expense=profile['expense'],
        savings=profile['savings'],
        debt=profile['debt'],
        dependents=profile['dependents'],
        years=profile['years'],
        goal=profile['goal'],
        sentiment=sentiment
    )
    ml_result = safe_dict(ml_result)

    allocation = safe_dict(
        ml_result.get('allocation'),
        {'Equity': 45, 'Debt': 35, 'Gold': 10, 'Cash': 10}
    )

    dl_mode = 'stable'
    if sentiment.lower() == 'positive':
        dl_mode = 'bullish'
    elif sentiment.lower() == 'negative':
        dl_mode = 'bearish'

    dl_result = safe_dict(simulate_dl_forecast(dl_mode))
    dl_comparison = safe_dict(compare_with_ml_baseline())
    scenarios = safe_list(simulate_scenarios(allocation))
    slm_summary = generate_advice_summary(profile, ml_result, nlp_result)
    recommendations = safe_list(generate_actionable_recommendations(profile, ml_result, nlp_result))
    report = generate_report_snippet(profile, ml_result, nlp_result)
    agent_result = safe_dict(run_agent(profile, ml_result, nlp_result, scenarios))

    return jsonify({
        'profile': profile,
        'ml_result': ml_result,
        'ml_evidence': safe_dict(get_ml_evidence_bundle()),
        'nlp_result': nlp_result,
        'nlp_evidence': safe_dict(get_nlp_evidence_bundle(market_text)) if market_text else None,
        'dl_result': dl_result,
        'dl_comparison': dl_comparison,
        'dl_evidence': safe_dict(get_dl_evidence_bundle(dl_mode)),
        'scenario_results': scenarios,
        'genai_evidence': safe_dict(get_genai_evidence_bundle(allocation)),
        'slm_summary': slm_summary,
        'recommendations': recommendations,
        'report': report,
        'slm_evidence': safe_dict(get_slm_evidence_bundle(profile, ml_result, nlp_result)),
        'agent_result': agent_result
    })


@app.route('/market-insights', methods=['POST'])
def market_insights():
    data = get_json_data()
    text = (data.get('text') or '').strip()

    if not text:
        raise APIValidationError('Field "text" is required')

    return jsonify(safe_dict(get_nlp_evidence_bundle(text)))


@app.route('/trend-forecast', methods=['POST'])
def trend_forecast():
    data = get_json_data()
    mode = (data.get('mode') or 'stable').strip().lower()

    allowed_modes = {'stable', 'bullish', 'bearish'}
    if mode not in allowed_modes:
        raise APIValidationError('Field "mode" must be one of: stable, bullish, bearish')

    return jsonify(safe_dict(get_dl_evidence_bundle(mode)))


@app.route('/summarize', methods=['POST'])
def summarize():
    data = get_json_data()
    profile = safe_dict(data.get('profile'))
    ml_result = safe_dict(data.get('ml_result'))
    nlp_result = safe_dict(data.get('nlp_result'), default_nlp_result())

    return jsonify({
        'summary': generate_advice_summary(profile, ml_result, nlp_result),
        'report': generate_report_snippet(profile, ml_result, nlp_result),
        'recommendations': safe_list(generate_actionable_recommendations(profile, ml_result, nlp_result)),
        'slm_evidence': safe_dict(get_slm_evidence_bundle(profile, ml_result, nlp_result))
    })


@app.route('/simulate', methods=['POST'])
def simulate():
    data = get_json_data()
    allocation = safe_dict(
        data.get('allocation'),
        {'Equity': 45, 'Debt': 35, 'Gold': 10, 'Cash': 10}
    )

    return jsonify(safe_dict(get_genai_evidence_bundle(allocation)))


@app.route('/agent/run', methods=['POST'])
def agent_run():
    data = get_json_data()
    profile = safe_dict(data.get('profile'))
    ml_result = safe_dict(data.get('ml_result'))
    nlp_result = safe_dict(data.get('nlp_result'), default_nlp_result())
    scenario_results = safe_list(data.get('scenario_results'))

    return jsonify(safe_dict(run_agent(profile, ml_result, nlp_result, scenario_results)))


@app.route('/ask', methods=['POST'])
def ask():
    data = get_json_data()
    query = (data.get('query') or '').strip()
    profile = safe_dict(data.get('profile'))
    ml_result = safe_dict(data.get('ml_result'))
    nlp_result = safe_dict(data.get('nlp_result'), default_nlp_result())

    if not query:
        raise APIValidationError('Field "query" is required')

    return jsonify({
        'response': respond_to_user_query(query, profile, ml_result, nlp_result)
    })


@app.route('/ml-evidence', methods=['GET'])
def ml_evidence():
    return jsonify(safe_dict(get_ml_evidence_bundle()))


@app.route('/nlp-evidence', methods=['POST'])
def nlp_evidence():
    data = get_json_data()
    text = (data.get('text') or '').strip()

    if not text:
        raise APIValidationError('Field "text" is required')

    return jsonify(safe_dict(get_nlp_evidence_bundle(text)))


@app.route('/slm-evidence', methods=['POST'])
def slm_evidence():
    data = get_json_data()
    profile = safe_dict(data.get('profile'))
    ml_result = safe_dict(data.get('ml_result'))
    nlp_result = safe_dict(data.get('nlp_result'), default_nlp_result())

    return jsonify(safe_dict(get_slm_evidence_bundle(profile, ml_result, nlp_result)))


@app.route('/genai-evidence', methods=['POST'])
def genai_evidence():
    data = get_json_data()
    allocation = safe_dict(
        data.get('allocation'),
        {'Equity': 45, 'Debt': 35, 'Gold': 10, 'Cash': 10}
    )

    return jsonify(safe_dict(get_genai_evidence_bundle(allocation)))


@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'modules': ['ML', 'DL', 'NLP', 'SLM', 'GenAI', 'AgenticAI'],
        'available_routes': [
            '/',
            '/predict',
            '/market-insights',
            '/trend-forecast',
            '/summarize',
            '/simulate',
            '/agent/run',
            '/ask',
            '/ml-evidence',
            '/nlp-evidence',
            '/slm-evidence',
            '/genai-evidence',
            '/health'
        ]
    })


if __name__ == '__main__':
    app.run(debug=True)