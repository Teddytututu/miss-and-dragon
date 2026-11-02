"""One plain-language prompt for the existing host patrol timer."""
def build(agent='GPT'):
    if agent not in ('GPT','Claude'):raise ValueError('Choose Claude or GPT')
    return f'''You are {agent}. Read docs/patrol.md and your project role instructions.
1. Read the current local time from the host clock, then run python scripts/agent.py --as {agent} wake and read the current inbox.
2. Process events, then the lead’s assigned work, then active tasks. Acknowledge each handled event with its actual result.
3. Continue authorized work until the remaining steps depend on a running job or a recorded decision. Follow the current resource limits and provider schedule.
4. Run python scripts/patrol.py {agent} --auto, read the returned schedule and apply the next wake with the host’s supported controls.
For a meaningful result, say what you accomplished, why it helps the owner and whose decision is pending, in at most two sentences. Keep unchanged healthy states quiet.'''
