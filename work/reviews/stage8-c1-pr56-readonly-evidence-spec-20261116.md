# C1 只读取证补证规范（PR #56 独立复核后）

- 对应证据 PR：#56
- 对应 Issue：#28
- 目标：补足采集时间、进程/句柄采集方法、文件清单完整性、时区口径
- 严格边界：只读；不打开 SQLite 数据库、不复制数据库、不执行 checkpoint、不备份/恢复、不切换路径、不运行 rebuild/ingest/retag
- 本文件不授权任何生产数据操作

## 1. 必须先声明采集范围

在报告开头写明：

1. 采集日期时间（UTC，ISO 8601，带 Z）及本机时区名称/偏移。
2. 操作系统、版本、主机标识（可脱敏，不写个人账户信息）。
3. 仓库根目录的实际路径。
4. 文件扫描范围：明确列出实际扫描的目录；至少覆盖 `04-知识底座` 和 `99-归档` 下与 kbase.db 相关的文件。
5. 进程检查范围：本机当前可见进程；若权限不足、容器隔离或远程进程不可见，必须明确列为限制。
6. 文件句柄检查范围：本机当前可见句柄；若没有可用工具或权限不足，写 `NOT_OBSERVABLE`，不得写“全机无句柄”。

不要再把 `$(date ...)` 等命令模板原样写入结果。必须把命令实际输出的时间值写入报告。

## 2. 时间戳采集要求

每次采集开始和结束分别记录 UTC 时间，示例格式：

```text
capture_started_utc: 2026-11-16T12:00:00Z
capture_finished_utc: 2026-11-16T12:03:00Z
host_timezone: Asia/Shanghai
host_utc_offset_at_capture: +08:00
```

以上仅为格式示例，不是本次真实采集时间。请写入真实命令输出。

文件 mtime 必须同时记录：
- 原始本地时间及其时区/偏移；
- UTC 转换值；
- 文件大小（字节）；
- 文件类型（main/WAL/SHM/backup/other）。

若系统只能提供无时区的本地 mtime，必须注明无法可靠转换 UTC，不得自行猜测时区。

## 3. 文件清单必须做到一一对应

扫描结果中每一个实体文件都单独一行，包括：
- `kbase.db`
- `kbase.db-wal`
- `kbase.db-shm`
- 所有带日期/后缀的备份文件及其 WAL/SHM sidecar（如存在）

对每个实际存在的文件记录：

| 字段 | 要求 |
|---|---|
| 相对路径 | 相对仓库根目录，保留完整文件名 |
| 类型 | main / WAL / SHM / backup / other |
| 大小 | 精确字节数，0 字节也要记录 |
| mtime | 本地时间、时区/偏移、UTC（可转换时） |
| SHA-256 | 对该文件本身计算；不能用主库哈希代表 sidecar |
| 文件属性 | 权限/只读属性；无法获取则写明 |
| 采集结果 | SUCCESS / ERROR / NOT_OBSERVABLE |

00 清单、02 元数据、SHA256SUMS 必须使用完全相同的文件集合。若文件在采集过程中新增/消失/变化，记录差异并停止对该批次作静止快照判断。

## 4. 进程与文件句柄证据

### 4.1 进程

报告实际执行的命令、执行时间、退出码、匹配规则和匹配结果摘要。匹配规则至少覆盖：
- 进程名/命令行包含 rag、kbase、sqlite、python、trae 等相关关键词；
- 进程命令行中引用候选数据库路径；
- 相关服务/容器进程（若本机环境存在）。

不能只写“无相关进程”。应写“在本次可见范围、按上述匹配规则，结果为 X；检查权限/范围限制为 Y”。

### 4.2 文件句柄

优先使用本机可用的句柄检查工具，检查候选主库、WAL、SHM 的打开句柄。必须记录工具名称/版本、命令、退出码和输出摘要。

如果 Windows 环境没有可用的句柄检查工具，或当前权限不足：
- 将句柄状态标记为 `NOT_OBSERVABLE`；
- 写明缺失工具/权限限制；
- 不得将“未查到”写成“没有占用”。

Linux/macOS 同理：若 lsof 等工具不可用或权限不足，标记 `NOT_OBSERVABLE`。

## 5. 推荐的只读命令参考

以下命令仅作采集参考，必须按实际操作系统选择。执行前确认当前目录是仓库根目录。不要运行任何写入、数据库维护或修复命令。

### Windows PowerShell

```powershell
Get-Date -Format o
(Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
Get-TimeZone | Format-List Id,DisplayName,BaseUtcOffset
Get-CimInstance Win32_Process |
  Where-Object { $_.Name -match 'rag|kbase|sqlite|python|trae' -or $_.CommandLine -match 'kbase\.db|知识底座' } |
  Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine
Get-ChildItem -LiteralPath .\04-知识底座, .\99-归档 -Recurse -Force -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match 'kbase\.db($|-|\.)' } |
  Select-Object FullName,Length,LastWriteTime,LastWriteTimeUtc,Attributes
```

对清单中每个文件分别执行 SHA-256：

```powershell
Get-FileHash -LiteralPath '<实际文件路径>' -Algorithm SHA256
```

句柄检查：若已有经批准/可用的 Sysinternals Handle 工具，可按其帮助文档只读查询候选文件；若无工具，不要临时下载或安装，直接记为 `NOT_OBSERVABLE`。

### Linux/macOS

```bash
date --iso-8601=seconds
date -u +%Y-%m-%dT%H:%M:%SZ
ps -eo pid,ppid,comm,args
find ./04-知识底座 ./99-归档 -type f \( -name 'kbase.db' -o -name 'kbase.db-*' -o -name 'kbase.db.*' \) -print
```

对清单中每个文件分别执行：

```bash
stat --printf='%n|%s|%y|%a\n' '<实际文件路径>' 2>/dev/null || stat '<实际文件路径>'
sha256sum '<实际文件路径>'
```

句柄检查（若工具已存在且权限允许）：

```bash
lsof -- '<候选文件完整路径>'
```

若 macOS 的 stat 参数与示例不同，使用系统自带 stat 对应选项并保留原始输出。不要为了统一格式而更改文件。

## 6. 结果解释与禁止性结论

即使本次检查没有发现相关进程/句柄，也只能得出：

> 在采集时间、主机、权限和工具可见范围内，按记录的匹配规则未观察到相关进程/句柄。

不能据此确认：
- 该 4.04GB 文件就是当前生产数据库；
- 该数据库处于静止状态或不存在其他主机/进程访问；
- 该数据库可安全复制、备份、恢复或切换；
- 备份文件与主库属于同一一致性时间点。

生产库身份需要独立的配置/运行链路证据；静止状态需要覆盖实际使用主机、服务和句柄的证据。C1 只读取证本身不能替代 C2 的授权与恢复验证。

## 7. 提交文件结构

请在 PR #56 原始目录之外新增补证目录，例如：

```text
work/cases/stage8-c1-readonly-followup-20261116/rerun-v1.1/
  00-采集范围与时间.md
  01-候选文件完整清单.md
  02-进程检查命令与输出.md
  03-文件句柄检查命令与输出.md
  04-元数据与逐文件SHA256.md
  05-SHA256SUMS.txt
  06-限制与结论.md
```

文件名可按仓库既有规范调整，但必须保留上述信息。原 PR #56 的 4 个文件不覆盖、不删除；新证据应有独立 run_id。

## 8. 复核门槛

- [ ] 所有时间均为实际值，不含未展开的命令模板。
- [ ] 扫描范围与系统/权限限制明确。
- [ ] 00/01/04/SHA256SUMS 文件集合完全一致。
- [ ] 所有 main/WAL/SHM/backup 文件分别记录元数据和 SHA-256。
- [ ] 进程检查有命令、范围、匹配规则、退出码和结果摘要。
- [ ] 句柄检查有命令、工具版本、权限说明；不可见时明确 NOT_OBSERVABLE。
- [ ] mtime 的本地时区与 UTC 口径明确。
- [ ] 结论仅限于本次观察范围，不宣称生产库身份或静止状态。
- [ ] 明确未执行复制、SQLite 打开/检查、checkpoint、备份、恢复、路径切换、rebuild、ingest、retag。

**状态规则：以上项目未全部满足时，C1 保持待补证；C2/C3/C4 继续 BLOCKED。此规范不构成生产数据库操作授权。**
