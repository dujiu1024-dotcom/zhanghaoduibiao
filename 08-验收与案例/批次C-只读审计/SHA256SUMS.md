# Batch C1 Read-Only Evidence SHA256SUMS

采集时间：2026-11-16 UTC 12:36:52  
批次：批次 C / C1 只读采集补遗  
基线 commit：`af3a891ea6b8b5b242fd4641f84fd5d0464c08fa`  
采集类型：严格只读（stat/shasum/lsof/ps/find；**未打开 SQLite 数据库**）  

## 新修订文件

```
7368a750a9220f3c4f6cfe4aec074ce594408b9919e6c4b1b46cd75105413bc6  08-验收与案例/批次C-只读审计/04-C1-只读采集补遗-20261116.md
```

## 数据库相关文件 SHA-256（文件系统级，NOT opened）

```
51d120b5ccb788a5db43dad50072772434ef2e1c980c5313e67078881feed17b  99-归档/个人IP工作区-2026-11-16/配置层/kbase.db
41a00793a1f6abbf6a78df58373346a18780e3840298416839b957989a09719b  99-归档/个人IP工作区-2026-11-16/配置层/kbase.db.bak-20261114-2338
906eb847893a0541a9607521d11230793f5f53544a8623781c2e1627f7607bd2  99-归档/个人IP工作区-2026-11-16/配置层/kbase.db.bak-20261115-0045
fd4c9fda9cd3f9ae7c962b0ddf37232294d55580e1aa165aa06129b8549389eb  99-归档/个人IP工作区-2026-11-16/配置层/kbase.db.bak-20261115-0045-shm
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  99-归档/个人IP工作区-2026-11-16/配置层/kbase.db.bak-20261115-0045-wal
```

## WAL/SHM 状态（当前时刻）

- `kbase.db-wal`: **NOT_EXISTS**
- `kbase.db-shm`: **NOT_EXISTS**
- `kbase.db.lock`: 0 bytes, empty file
- `kbase.lock`: 0 bytes, empty file

## 与 2026-11-16 17:40 采集的差异

| 项 | 17:40 采集 | 本次采集（20:36 CST） |
|----|-----------|----------------------|
| main SHA-256 | `40744a5fefedad80a...` | `51d120b5ccb788a5...` |
| main mtime | 2026-11-15 22:02:36 | 2026-11-16 17:41:11 |
| WAL | 存在（0 bytes） | NOT_EXISTS |
| SHM | 存在（32 KB） | NOT_EXISTS |

**差异原因**：NOT_AVAILABLE（只读采集无法审计 SQLite 内部操作历史）。
