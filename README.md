# 公式审校 · formula-proofread

供 Codex 使用的个人 skill：结合出版社规范、符号含义和页面实际字形，逐页核查正斜体、粗斜体和上下标，默认只输出确认错误，保留原稿，生成 Markdown 和 PDF。

## 在另一台电脑安装

私有仓库需要先登录有权限的 GitHub 账号。在 Windows PowerShell 中运行（目标目录须不存在）：

```powershell
gh auth login
gh repo clone ywt19981998/formula-proofread "$env:USERPROFILE/.codex/skills/formula-proofread"
```

若设置了自定义 `CODEX_HOME`，应安装到其 `skills/formula-proofread` 目录。也可下载 ZIP，将包含 `SKILL.md` 的整个目录放到该位置。

重新打开 Codex 或新建任务后，使用：

> 使用 $formula-proofread，按提供的指南逐页检查稿件，只列确认错误，生成 Markdown 和 PDF。

同时提供稿件和本次适用的指南。仓库不包含稿件、原文截图或个人审校结果。

## 辅助脚本

在运行脚本的 Python 环境中安装依赖：

```powershell
python -m pip install -r requirements.txt
python scripts/prepare_pdf.py manuscript.pdf work-evidence --scale 2
python scripts/export_review.py confirmed-review.json deliverable --formats both
```

准备脚本只提取证据，不会自动判错；审校者需要完成逐页视觉和语义检查。导出 JSON 格式见 [报告约定](references/report.md)。使用新的输出目录以保留旧成果。

PDF 导出默认使用 Windows 自带宋体和 Times New Roman，字体不随仓库分发；其他系统需要提供合适字体并适配脚本的字体映射。复杂公式需要其他可靠的数学排版器。

## 更新

```powershell
git -C "$env:USERPROFILE/.codex/skills/formula-proofread" pull --ff-only
```

有本地修改时先保留自己的改动，不强制覆盖。
