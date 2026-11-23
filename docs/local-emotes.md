# Optional local Bilibili reactions / 可选本机 B 站表情

Unicode is the default. When the installer asks whether to add Bilibili reactions, choose the default to continue with Unicode, or use `--download-emotes` to get this guide and the selected data directory. For an existing project:

```sh
python scripts/onboarding.py emotes --download-emotes --data-dir data
python scripts/onboarding.py emotes --unicode-emotes --data-dir data
```

The first command enables local images when they are ready. The second uses Unicode and keeps your local files. The board reads only project files. Historical image reactions without a local image display as 🙂.

## Prompt for your installer AI

> I chose to add local Bilibili reactions. Use the exact data directory printed by bootstrap or passed to onboarding. Start with GET `https://api.bilibili.com/x/emote/package?business=reply&ids=1,2`. Read `data.packages[].emote[]` from a successful response (`code: 0`), using each item's numeric `id`, `text`, and `url`. Fetch only the HTTPS images offered for the packages I chose and only if my use is permitted. Keep this selection small. Use the public response as returned. If the interface denies access, requires login, or returns no images, keep Unicode. Save images and plain labels using the layout below. Leave generated materials in the selected data directory and report the count. Refresh the board and verify the picker shows the local images.

默认使用 Unicode。选择加入 B 站表情后，把上面的提示词交给安装者 AI，并提供安装器显示的本机数据目录。AI 从公开接口的 `data.packages[].emote[]` 读取数字 ID、文字和图片地址，只取你选定且获准使用的图片。接口受限、要求登录或没有可用图片时继续使用 Unicode。完成后刷新讨论室，在表情面板里查看本机图片。

## Local layout / 本机文件结构

- Save each verified PNG as `<data-dir>/emotes/<id>.png`. If a supported image arrives in another format, decode it and save it as PNG with Pillow. Limit each PNG to 512 KiB and at most 256 pixels per side.
- Write `<data-dir>/emotes/manifest.json` as a UTF-8 JSON array. Each entry has a positive integer `id` from the API and a plain text `label` of at most 80 characters. Save images first and write the manifest last. Example using a fictional ID:

```json
[{"id":12345,"label":"Example reaction"}]
```

- The manifest stores IDs and labels. Image addresses are used only during retrieval. Keep the images and manifest in local project data, outside source control or release archives.
- 自备角色 PNG 放在 `<data-dir>/attachments/generated/{owner,Claude,GPT}/`，头像用 `avatar.png`，表情文件名见[素材说明](assets.md)。公开版随包提供原创 SVG。

