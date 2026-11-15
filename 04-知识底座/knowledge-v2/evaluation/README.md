# RAG 评测数据集说明

当前 `question-template.jsonl` 只有两条格式示例，不属于正式评测集，不计入任何指标。当前目录尚未包含已人工标注并冻结版本的正式训练集或独立保留集。

正式数据集至少分为：
- `positive-train.jsonl`：可用于开发与调参的正向集；
- `negative-train.jsonl`：可用于开发与调参的负向集；
- `adversarial.jsonl`：相近干扰、过期、冲突和跨域题；
- `holdout-positive.jsonl`：独立保留正向集；
- `holdout-negative.jsonl`：独立保留负向集。

每条题目必须有人工审核的 gold 来源和定位；不能用检索系统自己返回的结果反向标注 gold。保留集由非调参流程维护，评测前冻结版本。
