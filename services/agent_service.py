from datetime import datetime


def assess_action_priority(ml_result, nlp_result, scenario_results):
    risk = ml_result.get('risk', 'Moderate')
    health = ml_result.get('financial_health', 50)
    sentiment = nlp_result.get('sentiment', 'Neutral') if nlp_result else 'Neutral'

    severe_scenarios = [
        s for s in scenario_results
        if s.get('stress_result', {}).get('projected_return_pct', 0) < -8
    ]
 
    if risk == 'Conservative' and sentiment == 'Negative' and severe_scenarios:
        return 'High'
    if health < 45 or len(severe_scenarios) >= 2:
        return 'High'
    if sentiment == 'Negative' or risk == 'Moderate':
        return 'Medium'
    return 'Low'


def choose_agent_action(ml_result, nlp_result, scenario_results):
    priority = assess_action_priority(ml_result, nlp_result, scenario_results)
    risk = ml_result.get('risk', 'Moderate')
    sentiment = nlp_result.get('sentiment', 'Neutral') if nlp_result else 'Neutral'

    if priority == 'High':
        if sentiment == 'Negative':
            return 'Rebalance defensively and reduce equity exposure.'
        return 'Trigger portfolio risk review and shift part of allocation to safer assets.'

    if priority == 'Medium':
        if risk == 'Aggressive':
            return 'Maintain growth allocation but rebalance gradually with caution.'
        return 'Monitor market conditions and continue disciplined investing.'

    return 'Continue current plan with periodic review.'


def build_reasoning_trace(profile, ml_result, nlp_result, scenario_results):
    reasons = []

    reasons.append(f"Risk profile predicted as {ml_result.get('risk', 'Moderate')}.")
    reasons.append(f"Financial health score is {ml_result.get('financial_health', 0)}/100.")

    if nlp_result:
        reasons.append(f"Detected market sentiment is {nlp_result.get('sentiment', 'Neutral')}.")

    keywords = nlp_result.get('keywords', []) if nlp_result else []
    if keywords:
        reasons.append("Relevant text signals: " + ', '.join(keywords[:5]) + ".")

    worst_case = min(
        scenario_results,
        key=lambda x: x.get('stress_result', {}).get('projected_return_pct', 0)
    ) if scenario_results else None

    if worst_case:
        scenario_name = worst_case.get('scenario_name', 'Unknown Scenario')
        projected_return = worst_case.get('stress_result', {}).get('projected_return_pct', 0)
        reasons.append(
            f"Worst simulated case is {scenario_name} with projected return {projected_return}%."
        )

    reasons.append(f"Investment goal remains {profile.get('goal', 'Wealth Creation')}.")

    return reasons


def safety_check(action, ml_result, nlp_result=None):
    risk = ml_result.get('risk', 'Moderate')
    sentiment = nlp_result.get('sentiment', 'Neutral') if nlp_result else 'Neutral'

    if risk == 'Conservative' and 'growth allocation' in action.lower():
        return {
            'approved': False,
            'reason': 'Action conflicts with conservative risk profile.',
            'human_in_loop': True
        }

    if sentiment == 'Negative' and 'continue current plan' in action.lower():
        return {
            'approved': False,
            'reason': 'Market sentiment is negative; passive continuation requires human review.',
            'human_in_loop': True
        }

    return {
        'approved': True,
        'reason': 'Action passed guardrail checks.',
        'human_in_loop': False
    }


def generate_adaptive_adjustment(ml_result, scenario_results):
    allocation = ml_result.get('allocation', {})
    equity = allocation.get('Equity', 0)
    debt = allocation.get('Debt', 0)
    cash = allocation.get('Cash', 0)
    gold = allocation.get('Gold', 0)

    severe_count = sum(
        1 for s in scenario_results
        if s.get('stress_result', {}).get('projected_return_pct', 0) < -8
    )

    if severe_count >= 2:
        updated = {
            'Equity': max(0, equity - 10),
            'Debt': debt + 5,
            'Gold': gold + 3,
            'Cash': cash + 2
        }
        note = 'Adaptive defensive adjustment suggested due to multiple severe simulated scenarios.'
    else:
        updated = {
            'Equity': equity,
            'Debt': debt,
            'Gold': gold,
            'Cash': cash
        }
        note = 'No major adaptive adjustment required from current scenario set.'

    return {
        'suggested_allocation': updated,
        'adjustment_note': note
    }


def build_agent_architecture():
    return {
        'perception': 'Collects ML prediction, NLP sentiment, and scenario simulation outputs.',
        'reasoning': 'Evaluates financial health, risk profile, sentiment, and stress scenarios.',
        'planning': 'Chooses an action priority and suggested portfolio strategy.',
        'action': 'Returns recommended agent action or escalates to a human advisor.',
        'safety': 'Applies guardrails and blocks actions that conflict with user risk profile.'
    }


def run_agent(profile, ml_result, nlp_result, scenario_results):
    priority = assess_action_priority(ml_result, nlp_result, scenario_results)
    proposed_action = choose_agent_action(ml_result, nlp_result, scenario_results)
    reasoning = build_reasoning_trace(profile, ml_result, nlp_result, scenario_results)
    safety = safety_check(proposed_action, ml_result, nlp_result)
    adaptive_adjustment = generate_adaptive_adjustment(ml_result, scenario_results)

    final_action = proposed_action if safety['approved'] else 'Escalate to human advisor for approval.'

    decision_log = {
        'timestamp': datetime.utcnow().isoformat(),
        'client_goal': profile.get('goal', 'Wealth Creation'),
        'predicted_risk': ml_result.get('risk', 'Moderate'),
        'priority': priority,
        'proposed_action': proposed_action,
        'final_action': final_action,
        'reasoning_trace': reasoning,
        'adaptive_adjustment': adaptive_adjustment,
        'safety': safety
    }

    return {
        'agent_priority': priority,
        'agent_action': final_action,
        'reasoning_trace': reasoning,
        'adaptive_adjustment': adaptive_adjustment,
        'safety': safety,
        'agent_architecture': build_agent_architecture(),
        'decision_log': decision_log
    }