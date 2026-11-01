# Character art and optional reactions

[简体中文](README.zh-CN.md) · [Project overview](../README.md)

The board starts with the bundled portraits of you, Claude and GPT, plus stickers and mood illustrations. Original SVGs provide fallback pictures. A deployment's generated personal artwork takes priority when configured.

## Choose your reactions

Unicode reactions are ready at installation. The assistant offers an optional pack of 225 Bilibili emotes once; your explicit choice starts the download to this computer. Unicode remains available while the pack downloads or when a download fails.

## Artwork rights

The character PNGs are fan art. Their rights remain with the original artists and character owners, and their stated use is personal and noncommercial. Other uses follow the rights holders' permission. Maintainers remove affected material upon a rights holder's request.

The project's MIT license covers code and original SVGs. Font and other bundled materials have their own [third-party notices](../docs/third-party-notices.md).

<details>
<summary>For developers: bundled and local files</summary>

`board/art/` contains portraits, orange-haired character stickers, three-character atlases, fifteen desk mood pictures and stickers with restored edges. `public-emotes.json` lists the emote names and public download URLs.

After explicit consent, the assistant runs `python scripts/install_emotes.py`; images remain in the ignored local `data/emotes/` directory. An authorized repeat resumes the download. The local runtime images stay with that installation.

</details>
