# Bundled artwork and optional replacements

Original MIT SVG characters ship with this archive. Local custom artwork keeps priority. Reactions use Unicode.

本归档采用原创 MIT SVG 人物图，优先使用本地自定义图片。回应采用 Unicode 表情。

Every bundled SVG below is an original geometric illustration created for this project, licensed under MIT.

| File | Source | License |
| --- | --- | --- |
| board/art/avatar-claude.svg | Original project SVG | MIT |
| board/art/avatar-gpt.svg | Original project SVG | MIT |
| board/art/avatar-user.svg | Original project SVG | MIT |
| board/art/claude-calm.svg | Original project SVG | MIT |
| board/art/claude-shy.svg | Original project SVG | MIT |
| board/art/claude-smile.svg | Original project SVG | MIT |
| board/art/claude-surprised.svg | Original project SVG | MIT |
| board/art/claude-teary.svg | Original project SVG | MIT |
| board/art/claude-wink.svg | Original project SVG | MIT |
| board/art/gpt-calm.svg | Original project SVG | MIT |
| board/art/gpt-shy.svg | Original project SVG | MIT |
| board/art/gpt-smile.svg | Original project SVG | MIT |
| board/art/gpt-surprised.svg | Original project SVG | MIT |
| board/art/gpt-teary.svg | Original project SVG | MIT |
| board/art/gpt-wink.svg | Original project SVG | MIT |
| board/art/user-calm.svg | Original project SVG | MIT |
| board/art/user-shy.svg | Original project SVG | MIT |
| board/art/user-smile.svg | Original project SVG | MIT |
| board/art/user-surprised.svg | Original project SVG | MIT |
| board/art/user-teary.svg | Original project SVG | MIT |
| board/art/user-wink.svg | Original project SVG | MIT |
| board/reactions/care.svg | Original project SVG | MIT |
| board/reactions/celebrate.svg | Original project SVG | MIT |
| board/reactions/done.svg | Original project SVG | MIT |
| board/reactions/idea.svg | Original project SVG | MIT |
| board/reactions/review.svg | Original project SVG | MIT |
| board/reactions/smile.svg | Original project SVG | MIT |

The persona JSON files contain prompts for the avatar and six expressions. When the user asks to replace the bundled images, a deployment may use an image-capable assistant to generate a consistent original set, then save validated PNG or original SVG files under data/attachments/generated/Claude/ or GPT/. Generated replacements stay in runtime data; the original placeholders remain available. The six reaction illustrations are original project SVGs.

用户提出换图需求后，助手可按人设 JSON 中的头像与六种表情提示词生成替换图，存入 `data/attachments/generated/Claude/` 或 `GPT/`，同时保留原有图片。生成格式采用 PNG 或原创 SVG。

## Additional mood placeholders

| File | Source | License |
| --- | --- | --- |
| board/art/claude-cheer.svg | Original project SVG | MIT |
| board/art/claude-confused.svg | Original project SVG | MIT |
| board/art/claude-happy.svg | Original project SVG | MIT |
| board/art/claude-heart.svg | Original project SVG | MIT |
| board/art/claude-panic.svg | Original project SVG | MIT |
| board/art/claude-pout.svg | Original project SVG | MIT |
| board/art/claude-proud.svg | Original project SVG | MIT |
| board/art/claude-reading.svg | Original project SVG | MIT |
| board/art/claude-sleepy.svg | Original project SVG | MIT |
| board/art/claude-thinking.svg | Original project SVG | MIT |


## Runtime artwork creation record

For each optionally generated set, append its role, actual creator or tool, original prompt, file basenames, format and license or usage basis to local `data/attachments/generated/artwork-record.jsonl`. Keep deployment-specific provenance in that runtime record. A compact view may use this shape:

| Role | Creator / capability | Prompt | Files | Format | Usage basis |
| --- | --- | --- | --- | --- | --- |
| Example assistant | Actual generator or SVG author | Original deployment prompt | avatar plus six expressions | PNG or SVG | Original creation / deployment's chosen terms |

Runtime file selection accepts `.png` and `.svg` for the same basename and chooses the latest modification time (PNG wins an exact tie). Mood aliases map the extended header expressions to related basic generated expressions. Original source SVG placeholders retain their MIT license.

## Bundled character artwork

The release includes original MIT SVG character drawings. Historical image reactions display as 🙂.

发行包内含原创 MIT SVG 人物图。历史图片表情显示为 🙂。
