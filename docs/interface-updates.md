# Interface updates

## Discussion history / 讨论室历史

Discussion opens with the latest 18 messages. Load older messages explicitly. The first unread jump automatically expands to at most 120 messages. Manual source jumps load the target with nearby context. New messages at the bottom restore the compact view.

## Private image cache / 图片私有缓存

Avatars and reaction art use a private one-minute browser cache. Content-based ETags revalidate unchanged files and refresh replaced artwork after expiry. SVG restrictions continue to apply. Discussion records and document downloads use their existing response policies.

## Message actions / 消息操作

Use the visible Reply control beneath a message. The overflow menu contains the permitted withdrawal or administrator deletion action. It appears when the server grants deletion permission and supports keyboard navigation and touch hold.

## Unread entry / 入口未读提示

The discussion entry lights up for newer messages from other authors while closed. Timestamp offsets are compared as instants. Deleted entries and the current author are excluded.

## Phone discussion / 手机讨论室

On phones the discussion fills the visible screen and tracks the software keyboard. Drag the input handle or use its arrow keys to change input height. The preference survives reloads. Tablet drawers retain their height stops. Long filenames wrap inside the composer.

## Sticky-note replies / 便利贴回一句

Hover over a note to reveal Reply. Enter on a focused card or a long press on touch opens the same composer. Replies accept 40 characters, with a counter, Send and Cancel. Each reply also reaches the assigning assistant in the discussion. Retried requests keep a single message.
