# 角色图片与可选表情

[English](README.md) · [项目介绍](../README.zh-CN.md)

看板打开就能使用随包的你、Claude、GPT头像，以及贴纸和心情图。原创 SVG 提供备用图片；部署中配置好的个人生成图会优先显示。

## 选择回应表情

安装后可直接使用 Unicode 表情。助手会询问一次是否下载可选的 225 个 Bilibili 表情；你明确选择后才下载到这台电脑。下载期间或下载失败时，Unicode 表情继续可用。

## 图片使用范围

角色 PNG 属于二创，权利归原作者与角色权利人，标明的用途是个人非商业使用；其他用途按权利人许可处理。权利人提出要求时，维护者删除对应素材。

项目的 MIT 许可覆盖代码和原创 SVG。字体及其他随包材料的许可见[第三方声明](../docs/third-party-notices.md)。

<details>
<summary>给开发者：随包图片和本机文件</summary>

`board/art/` 包含头像、橘发角色贴纸、三人图集、十五张趴桌心情图和补全边缘的贴纸。`public-emotes.json` 列出表情名字及公开下载地址。

用户明确同意后，助手执行 `python scripts/install_emotes.py`，把图片保存在已忽略的本机目录 `data/emotes/`。获准后再次执行可接续下载，运行时图片随这份本机部署保存。

</details>
