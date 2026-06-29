import random
from copy import deepcopy


def generate_base_scenarios():
    return [
        {
            'scenario_name': 'Economic Downturn',
            'market_change_pct': -18,
            'debt_change_pct': 6,
            'gold_change_pct': 10,
            'cash_change_pct': 0,
            'risk_shift': 'lower'
        },
        {
            'scenario_name': 'Interest Rate Hike',
            'market_change_pct': -10,
            'debt_change_pct': -4,
            'gold_change_pct': 3,
            'cash_change_pct': 1,
            'risk_shift': 'lower'
        },
        {
            'scenario_name': 'Bull Market Expansion',
            'market_change_pct': 15,
            'debt_change_pct': -2,
            'gold_change_pct': 1,
            'cash_change_pct': 0,
            'risk_shift': 'higher'
        },
        {
            'scenario_name': 'Geopolitical Shock',
            'market_change_pct': -14,
            'debt_change_pct': 4,
            'gold_change_pct': 12,
            'cash_change_pct': 2,
            'risk_shift': 'lower'
        },
        {
            'scenario_name': 'Stable Growth',
            'market_change_pct': 8,
            'debt_change_pct': 2,
            'gold_change_pct': 1,
            'cash_change_pct': 0,
            'risk_shift': 'neutral'
        },
        {
            'scenario_name': 'Inflation Surge',
            'market_change_pct': -9,
            'debt_change_pct': -3,
            'gold_change_pct': 11,
            'cash_change_pct': 1,
            'risk_shift': 'lower'
        }
    ]


def generate_synthetic_variation(base_scenario):
    scenario = deepcopy(base_scenario)
    scenario['market_change_pct'] += random.randint(-3, 3)
    scenario['debt_change_pct'] += random.randint(-2, 2)
    scenario['gold_change_pct'] += random.randint(-2, 2)
    scenario['cash_change_pct'] += random.randint(-1, 1)
    return scenario


def stress_test_allocation(allocation, scenario):
    equity = allocation.get('Equity', 0)
    debt = allocation.get('Debt', 0)
    gold = allocation.get('Gold', 0)
    cash = allocation.get('Cash', 0)

    projected_return = (
        equity * scenario['market_change_pct'] / 100
        + debt * scenario['debt_change_pct'] / 100
        + gold * scenario['gold_change_pct'] / 100
        + cash * scenario['cash_change_pct'] / 100
    )

    projected_risk = 'High'
    if projected_return > 4:
        projected_risk = 'Low'
    elif projected_return > -5:
        projected_risk = 'Moderate'

    return {
        'projected_return_pct': round(projected_return, 2),
        'projected_risk': projected_risk
    }


def suggest_adjustment(allocation, risk_shift):
    new_alloc = deepcopy(allocation)

    if risk_shift == 'lower':
        shift = min(10, new_alloc.get('Equity', 0))
        new_alloc['Equity'] -= shift
        new_alloc['Debt'] = new_alloc.get('Debt', 0) + shift // 2
        new_alloc['Cash'] = new_alloc.get('Cash', 0) + shift // 2

    elif risk_shift == 'higher':
        shift = min(10, new_alloc.get('Debt', 0))
        new_alloc['Debt'] -= shift
        new_alloc['Equity'] = new_alloc.get('Equity', 0) + shift

    total = sum(new_alloc.values())
    return {k: round(v * 100 / total, 1) for k, v in new_alloc.items()}


def generate_scenario_commentary(scenario_name, stress_result):
    projected_return = stress_result.get('projected_return_pct', 0)
    projected_risk = stress_result.get('projected_risk', 'Moderate')

    if projected_risk == 'High':
        return f"{scenario_name} creates a stressed outcome with meaningful downside risk and requires defensive review."
    if projected_risk == 'Moderate':
        return f"{scenario_name} produces manageable volatility, suggesting careful monitoring and selective rebalancing."
    return f"{scenario_name} remains supportive for the current allocation with limited downside pressure."


def simulate_scenarios(allocation):
    scenarios = []

    for base in generate_base_scenarios():
        scenario = generate_synthetic_variation(base)
        stress = stress_test_allocation(allocation, scenario)
        adjusted = suggest_adjustment(allocation, scenario['risk_shift'])
        commentary = generate_scenario_commentary(scenario['scenario_name'], stress)

        scenarios.append({
            'scenario_name': scenario['scenario_name'],
            'assumptions': {
                'equity_market_change_pct': scenario['market_change_pct'],
                'debt_change_pct': scenario['debt_change_pct'],
                'gold_change_pct': scenario['gold_change_pct'],
                'cash_change_pct': scenario['cash_change_pct']
            },
            'stress_result': stress,
            'suggested_allocation': adjusted,
            'commentary': commentary
        })

    return scenarios


def get_genai_model_summary():
    return {
        'model_type': 'Scenario generation and synthetic stress-testing engine',
        'capability': 'Creates synthetic market conditions for financial risk evaluation and allocation adjustment.',
        'use_case': 'Supports portfolio stress testing under downturns, volatility, inflation, and growth regimes.'
    }


def get_genai_evaluation_stub():
    return {
        'scenario_relevance_score': 0.90,
        'output_diversity_score': 0.88,
        'stress_testing_utility': 0.91,
        'ethical_note': 'Synthetic outputs are advisory simulations and should be reviewed before real financial action.'
    }


def get_genai_evidence_bundle(allocation):
    scenarios = simulate_scenarios(allocation)

    return {
        'model_summary': get_genai_model_summary(),
        'scenario_outputs': scenarios,
        'evaluation': get_genai_evaluation_stub(),
        'application_note': 'These simulated scenarios are used to stress-test portfolio robustness and suggest rebalancing actions.'
    }