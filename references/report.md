# 审校记录与交付

默认格式为：**第 x 页｜原文｜标量/矢量等类别｜正确格式**。补充印刷页码，不假定固定偏移。原文用原页清晰截图及可检索的定位文字；正确格式实际显示目标字形并写明修改方式。

MD 使用 `$...$`、`\boldsymbol{A}`、`\boldsymbol{\alpha}`、`a_{ij}`、`\mathrm{...}`。大写希腊斜体需要显式 `\mathit{\Delta}`。不用 Markdown 粗体星号替代数学粗斜体。

截图包含完整目标符号、上下标和必要上下文；裁边不截断目标。优先保持公式完整，不能缩小到无法辨认。PDF 可将四个字段分块排列，避免窄表压缩截图。

## 导出 JSON

correct_latex 不含美元定界符。PDF 使用 correct_runs 显式字体片段。两种表示必须表达同一修改，由审校者核对。

```json
{
  "title": "公式审校错误清单",
  "scope": "PDF 第1页（书内第111页）",
  "basis": "用户指南第16页：矩阵使用粗斜体。",
  "coverage_complete": true,
  "scope_pages": [1],
  "coverage": [{"page": 1, "status": "complete", "unresolved": [], "visual_reviewed": true, "regions": {"text": "complete", "formulas": "complete", "figures": "not_applicable"}}],
  "notes": ["仅替换所列主字母；原稿未修改。"],
  "errors": [{
    "id": "p1-01", "page": 1, "reading_order": 1, "printed_page": "111",
    "image": "evidence/p1-01.png",
    "original": "矩阵 A 的定义处", "category": "矩阵",
    "correct_latex": "\\boldsymbol{A}",
    "correct_runs": [{"text": "A", "style": "bold-italic"}],
    "reason": "普通斜体改为粗斜体。", "count": 1
  }]
}
```

correct_runs 支持 style 为 upright / italic / bold-italic，position 为 normal / sub / super（默认 normal）。标点通常 upright。轻量导出器不处理任意 LaTeX；复杂公式另用可验证的数学排版器。

scope_pages 来自用户指定范围及实际 PDF 页数，不能仅填写已经看过的页。coverage_complete 必须为布尔值；完成台账须包含 visual_reviewed、unresolved 和正文/公式/图示 regions，无相应内容用 not_applicable。机器校验不证明实际视觉核查已经发生。

errors 按页和 reading_order 严格递增提供。reading_order 是审校者确认的页内阅读顺序，不用坐标自动排序代替语义顺序。同条按左到右列目标，同一处不重复计数。count 是错误符号位置数，不是截图总字母数。零条报告也须如实说明覆盖状态。

## 验证

- 错误可由页码、图片、定位文字找到，依据明确；待查图像、编码和未读页不能写 complete。
- MD/PDF 条目 ID、页码、类别、数量与结论一致，无缺图、重复 ID。
- PDF 嵌入字体，验证希腊字母、粗斜体和上下标；数学缺字报错不能忽略。
- 渲染检查各布局类型及全部页面缩略图，疑点放大；检查长行、图像、分页和页脚。
- PDF 不依赖外链图片；MD 与 assets 目录一起移交。最终提供链接。
- Obsidian 库若要求完整 YAML，应补 created、updated、confidence、sources 等；脚本仅给最小草稿元数据。
