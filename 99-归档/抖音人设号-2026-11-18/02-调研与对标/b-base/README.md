# B 库：对标视频元素库

一句话：把已经采过的对标视频拆成 9 个可筛选的元素，用来决定**下一条拍什么**。
服务对象是账号本人，不是给分析报告用的。这里不输出结论，只提供能筛的样本。

数据只来自 2026-11-14 之前已经采到的页面文本，**没有重新抓取，没有补拍，没有凭记忆填画面或台词**。

---

## 一、文件

| 文件 | 用途 |
| --- | --- |
| `bbase.db` | SQLite 库，两张主表 + 一张关联表 + 4 个视图 |
| `build_bbase.py` | 建库脚本，可重跑；所有手工判断都写在脚本里，改完重跑即可 |
| `video-review-24.json` | **24 条元素样本的人工判读 + 机器转写结果**，key = `source_ref`。建库脚本读它回填，缺了它就退回空表 |
| `completeness-report.md` | 9 列各自的填充率、6 列以上可用条数、缺口原因 |
| `example-query.md` | 指定示例查询的实际结果（含为什么是 0 条） |
| `work/` | 流水线产物：抽帧图、转写原文、抓流清单、产物对照表（`02-产物清单.md`） |

重跑：

```bash
cd "02-调研与对标/b-base"
python3 build_bbase.py              # 重建 bbase.db（会读 video-review-24.json 回填）
BBASE_DB=/tmp/t.db python3 build_bbase.py   # 建到别处，用于对比验证
```

---

## 二、表结构

### `samples`：61 条样本

61 = 24 条元素样本 + 40 条对标视频 − 3 条重复（同一视频 id 合并，元素样本优先）。

**9 个分析列**（缺就是 NULL，不填空字符串，不猜）：

| # | 列名 | 含义 | NULL 表示 |
| ---: | --- | --- | --- |
| 1 | `duration_sec` | 时长（秒） | 页面没显示时长 |
| 2 | `first3_visual` | 前三秒画面（人/物/字幕/动作） | 没有逐帧看过，不填 |
| 3 | `first_line` | 第一句话原话 | 没有逐帧/逐字稿，不填 |
| 4 | `turn_sec` | 转折或冲突出现在第几秒 | 没有可核时间点 |
| 5 | `result_sec` | 结果或结论出现在第几秒 | 没有可核时间点 |
| 6 | `ending_action` | 结尾动作（引导关注/私信/留问题/纯结束） | 没看到结尾，不填 |
| 7 | `subtitle_style` | 字幕样式（有无/位置/字号/描边） | 没有画面证据，不填 |
| 8 | `top_comment` + `top_comment_likes` | 最高赞评论及赞数 | 评论区未采集或无有效评论 |
| 9 | `demand_level` | 需求信号：求定制/求代做、求教程/求方法、技术讨论/同行提问、纯情绪 | 无评论，或评论全是广告/刷单，无法判定 |

**3 个后补的分析列**（2026-11-14 补，只对 24 条元素样本有值，其余 37 条为 NULL）：

| 列名 | 含义 | NULL 表示 |
| --- | --- | --- |
| `first_line_proofread` | 人工校对后的第一句话，与 `first_line`（原始识别）并存 | 无原始识别可校对，或无法校对 |
| `has_subtitle` | 前三秒画面是否有成行字幕/文字条：1 有 / 0 无 | 未判读 |
| `actual_duration_sec` | 实际下载文件测得的时长（区别于页面口径 `duration_sec`） | 未下载成功 |

**4 个溯源列**：`account` 账号名、`url` 链接、`collected_on` 采集日期、`evidence_type` 证据类型。

**辅助列**（不属于 9 列，方便筛选用）：
`category` 类型、`structure_tag` 结构标签（结果前置/冲突开场/判断型）、`migration_note` 对标菜单里的迁移判断、`evidence_note` 每条缺失的具体原因、`raw_title` 原标题、`source_file` 来源文件。

`evidence_type` 分三档，按「证据够到哪一步」划，不按「花了多少力气」划：

| 值 | 判定标准（满足其一即算） | 当前条数 | 能支撑什么结论 | 不能支撑什么 |
| --- | --- | ---: | --- | --- |
| `实看` | ① 全片从头看到尾；或 ② 关键帧全覆盖（每个叙事节点都有帧）**且**有完整口播逐字稿 | 0 | 一切元素级判断，含节奏、转折点、留存结构、结尾引导效果 | — |
| `抽帧看过` | 只看过有限帧（如 0/1/2/3 秒 + 末 3 秒 + 末 1 秒共 6 帧），没看全片；口播可能有转写，但不保证完整 | 24 | 前三秒有什么（人/物/字幕/构图）、有无字幕条及其位置样式、结尾最后一帧画面与文字 | 「整条节奏好不好」「转折在第几秒最有效」「中间怎么推进的」——这些必须全片 |
| `仅标题推断` | 没看过任何画面，只有标题/时长/点赞/评论 | 37 | 时长分布、需求信号、评论区反应、标题类型 | 任何画面、台词、字幕、结尾动作的判断 |

判定与落库规则：

- 一档之内**不允许降级混用**。比如 `抽帧看过` 的样本，其 `turn_sec`（转折在第几秒）仍然是 NULL——6 帧看不出转折点，这一列要等 `实看` 才能填。
- 24 条元素样本统一记 `抽帧看过`，这不是"放宽"，是给它的证据强度一个准确名字。
- 历史口径变更：旧版的 `仅二手描述`(17) 与 `仅标题可读`(44) 合并为 `仅标题推断`(37) + `抽帧看过`(24)。旧版"有章节摘要"这一层细微差别不再单独成档，原文仍保存在 `demand-signal/work/fs.json` 与对标菜单里。
- 每条样本具体缺了哪几列、为什么缺，写在 `evidence_note` 里，不塞进 `evidence_type`。

### `topics`：15 条已排期选题

字段：`topic_name` 选题名、`target_audience` 目标人群、`persona_point` 要证明的人设点、`own_material_path` 自有素材路径、`status` 状态、`note` 备注。

状态只有两种：

- `立项`：按结构挂到 ≥2 条样本；
- `未立项`：挂不到 2 条样本，按规则标未立项。

当前 10 条立项、5 条未立项。未立项的 5 条是：自嘲 3 条、旁人视角 2 条——B 库里没有这两类结构的样本，不是选题本身不好，是**没有对标证据可挂**。

### `sample_topics`：多对多关联表

只挂有文档依据的结构标签的 24 条元素样本。40 条对标视频的开头 3 秒基本是标题推断，不作为选题的结构支撑。

### 视图

| 视图 | 用途 |
| --- | --- |
| `v_samples_cn` | 中文列名，直接看全表 |
| `v_sample_completeness` | 每条样本填了几列、是否达到 6 列 |
| `v_topic_sample_count` | 每条选题挂了几条样本 |
| `v_unfiled_topics` | 未立项清单（状态为未立项或样本 <2 条） |

---

## 三、怎么查

### 1. 看全部样本（中文列）

```sql
SELECT 编号, 账号名, 标题, 时长秒, 证据类型, 需求信号, 结构标签, 类型
FROM v_samples_cn
ORDER BY 时长秒;
```

### 2. 按需求信号筛（只留真正有需求的）

```sql
SELECT 账号名, 标题, 时长秒, 需求信号, 最高赞评论, 最高赞数
FROM v_samples_cn
WHERE 需求信号 IN ('求定制/求代做', '求教程/求方法')
ORDER BY 最高赞数 DESC;
```

### 3. 查某条选题挂了哪些样本

```sql
SELECT t.topic_name, s.account, s.raw_title, s.duration_sec, s.structure_tag
FROM topics t
JOIN sample_topics st ON st.topic_id = t.id
JOIN samples s ON s.id = st.sample_id
WHERE t.topic_name LIKE '%满分%';
```

### 4. 未立项清单

```sql
SELECT * FROM v_unfiled_topics;
```

### 5. 完整度分布

```sql
SELECT filled_cols, COUNT(*) AS 条数
FROM v_sample_completeness
GROUP BY filled_cols ORDER BY filled_cols;
```

---

## 四、怎么加样本

加一条样本（9 列能填几列填几列，填不了写 NULL）：

```sql
INSERT INTO samples (
  source_ref, account, url, collected_on, evidence_type, evidence_note,
  duration_sec, first3_visual, first_line, turn_sec, result_sec,
  ending_action, subtitle_style, top_comment, top_comment_likes,
  demand_level, category, structure_tag, migration_note, raw_title, source_file
) VALUES (
  '视频id或自定义唯一值',
  '账号名',
  'https://www.douyin.com/video/...',
  '2026-11-15',
  '实看',                       -- 实看 / 仅二手描述 / 仅标题可读
  '逐帧看过；评论区首屏可读',
  22.4,                        -- 时长秒；不知道写 NULL
  '真人半身出镜，桌上摆着两台手机，无字幕',  -- 没看画面写 NULL
  '这个功能我用了三个月，今天必须说清楚',      -- 没逐字稿写 NULL
  8,                           -- 转折秒；不知道写 NULL
  18,                          -- 结果秒；不知道写 NULL
  '留问题',                    -- 引导关注/私信/留问题/纯结束；没看到写 NULL
  '底部白字黑边，字号偏大',      -- 没看画面写 NULL
  '这条讲得比官方清楚',          -- 无评论写 NULL
  1200,
  '求教程/求方法',              -- 四级之一；判不了写 NULL
  '口播观点',
  '判断型',
  '能借结构，不能借题材',
  '视频标题',
  '手动录入'
);
```

挂到选题：

```sql
INSERT INTO sample_topics (sample_id, topic_id)
SELECT s.id, t.id
FROM samples s, topics t
WHERE s.source_ref = '视频id或自定义唯一值'
  AND t.topic_name = '选题名';
```

加完重跑一次统计视图即可：

```sql
SELECT * FROM v_topic_sample_count WHERE sample_count < 2;
```

---

## 五、290 条爆款池与 40 条对标视频怎么处理

**290 条爆款池没有导入 `samples`。** 原因：原始池 `demand-signal/work/vs_pool*.json` 只有四个字段——`id`、`dur`、`likes`、`txt`（标题），清洗后的 290 条是「时长 + 万级点赞 + 标题」三类都齐的条目。**没有一条有评论、画面、台词、字幕、结尾动作。** 如果整池导入，会多出 290 行只填了 1 列的记录，把完整度统计冲淡，也筛不出任何元素级信息。它仍然保留在原文件里，需要时可当标题池用。

**40 条对标视频已导入**，但只填了能核的列：37 条有页面时长，3 条时长未获取；3 条与 24 条元素样本重叠，因此带上了评论与需求信号；其余 37 条没有任何画面/台词/字幕数据。另有 2 条链接指向账号主页而不是具体视频页（第 29、40 条），已在 `evidence_note` 标注。

---

## 六、边界

- 本库不含 A 库（`04-知识底座/`）的任何内容，也不引用其中的结论。
- 本库不做「哪类内容更容易爆」的判断；点赞数只在原始池里，未进样本表，且抖音网页版只显示万级数字。
- 需求信号是**读评论的规则判断**，不是平台指标；规则写在 `build_bbase.py` 的 `FS_DEMAND` 里，可逐条复核。
- 24 条元素样本已于 2026-11-14 抽帧 + 转写补齐前四列，**当前 61 条中 19 条达到 6 列以上可用**（全部来自这 24 条）；其余 37 条对标视频仍停在「标题 + 时长 + 部分评论」这一层。剩下的缺口是取样缺口，不是库结构缺口。

---

## 七、已知陷阱（抓视频时必查）

这一节记的是 2026-11-14 跑 24 条时真实踩到、并会造成**静默错数据**的坑。每一条都给了可执行的检查步骤，不要靠"看起来没问题"判断。

### 陷阱 1：连续切页面时，网络事件会串到下一条

**现象**：连续 `goto` 不同视频页，`page.events()` 会把上一条页面的媒体请求也吐出来。抓到的 `dash_video` 实际是上一条视频的流。本轮 52、53、60 三条中招，其中 52 合并后容器时长 445 秒（音轨是它自己的），视频轨却是 51 的 121 秒。

**检查步骤**：

1. 抓流时维护一个**全局已用 URL 集合**，每条新样本只接受不在集合里的地址；接不到就回首页再进一次，最多重试 3 次。
2. 每条下载完**立刻比对**：`|actual_duration_sec - 页面 video.duration| > 2` 判为可疑，重抓。
3. 更要紧的是下面第 2 条——只比容器时长会漏。

### 陷阱 2：容器时长相等 ≠ 视频没被截断

**现象**：`ffprobe -show_entries format=duration` 返回的是**最长那条流**的时长。52 的 mp4 容器报 445.65 秒（音轨完整 445.65），视频轨只有 121.47 秒，`format.duration` 完全看不出来。表现是抽末帧时 `ffmpeg` 报 `Output file is empty, nothing was encoded`，退出码却是 0。

**检查步骤**（每条必跑）：

```bash
ffprobe -v error -show_entries stream=codec_type,duration -of csv=p=0 <file>.mp4
# 要求 video 与 audio 两行时长之差 ≤ 2 秒，否则判为截断，重下
```

批量检查：

```bash
for f in dl/*.mp4; do
  ffprobe -v error -show_entries stream=codec_type,duration -of csv=p=0 "$f" | \
  awk -F, -v n="$(basename "$f")" '{d[$1]=$2} END{if (d["audio"]-d["video"]>2 || d["video"]-d["audio"]>2) print n, d["video"], d["audio"]}'
done
```

### 陷阱 3：系统语音识别单次调用有约 1 分钟上限

直接喂 4 分钟音频，只回几十个字（缺了约 250 秒的内容，且不报错）。**必须按 45 秒切片**再拼接，切片后 0.076× 稳定。切片用：

```bash
ffmpeg -i in.wav -f segment -segment_time 45 -reset_timestamps 1 -c copy chunk_%03d.wav
```

### 陷阱 4：`SFSpeechRecognizer` 回调在主队列

用 `DispatchSemaphore` 阻塞主线程等结果 → 永远收不到回调，无结果、无报错、静默挂死。必须改成跑 `RunLoop.main`。

### 陷阱 5：`LIKE '%字幕%'` 判不出有无字幕

它会命中「**无**字幕」「没有字幕条」这类描述。判有无字幕一律用 `has_subtitle` 列（1/0），不要再用字符串匹配。

### 陷阱 6：重建会冲掉回填

`build_bbase.py` 会 `DROP TABLE IF EXISTS samples` 重建。所以 24 条的判读结果必须存在 `video-review-24.json` 里由脚本读入，**不能只存在 db 里**。改完判读结果，改 JSON 再重跑，不要直接 `UPDATE`。
