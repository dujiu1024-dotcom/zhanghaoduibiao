# RAG 评测与知识迁移执行记录模板

## RAG 评测

| 字段 | 记录 |
|---|---|
| Git commit / rag.py SHA | |
| 模型/嵌入版本 | |
| SIM_FLOOR | |
| ANSWER_MIN_COVERAGE | |
| SHORT_RELAX | |
| ENTITY_GATE | |
| 知识库快照 | |
| 题集版本与哈希 | |
| 正向集规模 | |
| 负向集规模 | |
| 对抗集规模 | |
| 独立保留集规模 | |

| 指标 | 调参集 | 独立保留集 |
|---|---:|---:|
| Recall@k | | |
| Precision@k | | |
| MRR/nDCG | | |
| Answerability precision/recall | | |
| Answer faithfulness | | |
| Negative abstention rate | | |
| Citation accuracy | | |
| Stale-hit rate | | |
| Sensitive leakage | | |

逐题错误记录路径：

## 知识迁移抽样

| knowledge_id | 原路径/SHA | 目标层/领域 | 权限核验 | 元数据完整 | 切段质量 | 检索验证 | 处理结论 |
|---|---|---|---|---|---|---|---|

抽样原则：至少覆盖 A/B/C/D/E 五层；个人 IP/账号资料必须单独抽样并验证不会进入通用检索；原件 SHA 保持不变；未核授权或敏感级别不明的条目不得标 active。

## 结论

- RAG 当前基线是否可建立：
- 独立保留集是否通过：
- 是否发现过期/冲突/敏感泄露：
- 抽样迁移是否通过：
- 未执行项与原因：