"""Pure host quota admission with explicit policy and observed usage."""
import math
from datetime import datetime,timezone,timedelta

def decide(state, sample, policy, now, direct=False):
    def number(value,minimum=0,maximum=float('inf')):
        return type(value) in (int,float) and math.isfinite(value) and minimum<=value<=maximum
    if (not isinstance(sample.get('account'),str) or not sample['account'].strip()
            or not number(sample.get('used'),0,100) or not number(sample.get('reset'))):
        raise ValueError('valid_account_usage_reset_required')
    if (not number(policy.get('daily_percent'),0,100) or not number(policy.get('reserve_percent'),0,policy['daily_percent'])
            or type(policy.get('max_daily_turns')) is not int or policy['max_daily_turns']<0
            or not number(policy.get('interval_seconds')) or not number(policy.get('timezone_offset_hours',8),-12,14)):
        raise ValueError('valid_budget_policy_required')
    if now.tzinfo is None:raise ValueError('timezone_aware_clock_required')
    day = now.astimezone(timezone(timedelta(hours=policy.get('timezone_offset_hours',8)))).date().isoformat()
    old = state.get('sample')
    same_day = state.get('day') == day
    # A first observation charges usage conservatively; midnight crossings
    # include the entire interval since the preceding observation.
    if old and old['account'] != sample['account']:
        return dict(allow=False, status='account_changed')
    delta = max(0, sample['used'] - old['used']) if old and old['reset'] == sample['reset'] else sample['used']
    state.update(day=day, spent=(state.get('spent', 0) if same_day else 0) + delta,
                 turns=state.get('turns', 0) if same_day else 0,
                 sample=sample, observed_at=now.isoformat())
    remaining = policy['daily_percent'] - state['spent']
    
    if direct:
        return dict(allow=True, status='direct_ready' if remaining > policy['reserve_percent'] else 'direct_over_reference',
                    remaining=remaining)
    if remaining <= policy['reserve_percent']:
        return dict(allow=False, status='daily_budget_hold', remaining=remaining)
    if state['turns'] >= policy['max_daily_turns']:
        return dict(allow=False, status='daily_turn_hold', remaining=remaining)
    last = state.get('last_dispatch')
    if last and (now - datetime.fromisoformat(last)).total_seconds() < policy['interval_seconds']:
        return dict(allow=False, status='economy_coalescing', remaining=remaining)
    return dict(allow=True, status='budget_ready', remaining=remaining)

