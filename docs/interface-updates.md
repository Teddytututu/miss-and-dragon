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

## Free paper wall / 自由贴墙

Notes size themselves to their content and fill the available wall with staggered positions and alternating angles. Adjacent papers use contrasting theme colours. Positions are deterministic across refreshes, and resizing recomputes the layout.

## Notes in Today / 便利贴放进今天

Drag the note handle into Today, click the handle, or choose Today from the touch menu. Unassigned notes show Pending. Checked tasks remain in place for the whole day and support undo through their checkbox. The next day, completed notes enter the archive and unfinished notes return in their original order. Dates follow the host workspace timezone.

## Result tree

Tree nodes show a one-sentence summary, direct report links and cause/effect jumps. Read markers follow summary and file versions. Filter unread results or highlight one causal chain. Detail views retain counts and full results.

## Resizable detail drawer

Drag the detail drawer edge or focus its separator and use arrow keys. Double-click restores 460px. Desktop widths stay between 320px and 80% of the window, and phones use the full width. The browser remembers the desktop preference and returns focus when closed.

## Notebook member menu

The composer shows the project owner in a compact member menu. Open it to view assistant profiles and enlarge their avatars. Pink mode uses a tape-and-dashed-paper treatment. Browser messages continue to use the authenticated owner identity.
