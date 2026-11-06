# Interface updates

## Discussion history / 讨论室历史

Discussion opens with the latest 18 messages. Load older messages explicitly. The first unread jump automatically expands to at most 120 messages. Manual source jumps load the target with nearby context. New messages at the bottom restore the compact view.

## Private image cache / 图片私有缓存

Avatars and reaction art use a private one-minute browser cache. Content-based ETags revalidate unchanged files and refresh replaced artwork after expiry. SVG restrictions continue to apply. Discussion records and document downloads use their existing response policies.

## Message actions / 消息操作

Use the visible Reply control beneath a message. The overflow menu contains the permitted withdrawal or administrator deletion action. It appears when the server grants deletion permission and supports keyboard navigation and touch hold.

## Unread entry / 入口未读提示

The discussion entry lights up for newer messages from other authors while closed. Timestamp offsets are compared as instants. Deleted entries and the current author are excluded.
