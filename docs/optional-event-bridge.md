# Optional event bridge / 可选事件桥

A deployment adapter can wake the existing assistant session after a meaningful event. The core board records events locally; the adapter selects a provider-supported session tool. Session identifiers, credentials and host addresses belong in deployment configuration.

1. Read `attachments/night-watch/events.json` and keep a durable cursor per consumer.
2. Match task ownership and event category to a configured role. Research jobs and remote resources go to the experiment role; interface, learning and local maintenance go to the chores role; owner messages go to the front role.
3. Acquire a process-safe lease per target session. A live lease preserves the existing wake. Expired leases require checking the recorded process identity before recovery.
4. Wake the original session with the exact event IDs and a small summary. A fallback schedule follows the user's selected interval and notification policy.
5. After handling the condition, run `events --ack EXACT_ID --result "Concrete outcome"`. Acknowledgment stores the outcome and removes only matching IDs.

Keep a result checkpoint before acknowledgment. Retries reuse the same event identity and checkpoint, making recovery idempotent. Stable monitoring stays quiet; meaningful completion, failure and required owner action reach the owner.

事件桥由部署方选择宿主接口，复用已有会话。按角色独立收信游标与租约；处理结果保存后确认准确事件。真实会话编号、地址与凭据放在部署配置。
