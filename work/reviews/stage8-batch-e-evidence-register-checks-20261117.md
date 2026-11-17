# 批次 E｜Run Manifest 证据登记自动检查

- 日期：2026-11-17
- 对应 Issue：[#30](https://github.com/dujiu1024-dotcom/zhanghaoduibiao/issues/30)
- 状态：自动检查脚本与 CI 已新增；等待本 PR CI 结果
- 范围：仅检查仓库内已提交的 Run Manifest 及其声明的归档产物，不读取用户本机目录，不执行任何业务动作。

## 检查内容

新增 `scripts/validate-stage8-evidence-register.mjs` 和 GitHub Actions workflow：

1. 递归发现 `08-验收与案例/` 下含 `run_id` 的 manifest JSON；
2. 使用 Draft 2020-12 schema 校验字段、状态与证据结构；
3. 检查 `run_id` 全仓库登记唯一，防止不同文件复用同一运行标识；
4. 对 `run_type=case` 强制核对 `case_id` 与 `run_id` 的 CASE 编号，并要求输入证据有 SHA-256 和 `artifact_type`；
5. 检查 manifest 的 `artifacts` 路径是仓库内相对路径，拒绝绝对路径/路径穿越，并确认引用文件确实存在；
6. 对标记为 `tracked_in_main` 的案例输入证据执行同样的文件存在性检查。

## 不检查/不能证明的事项

- 不读取或验证 `local_only` 输入材料的实际内容和哈希；
- 不证明 Trae 运行真实性、会话独立性、Skill 加载或专家调用；
- 不验证某份输出的业务正确性，也不自动将任何批次升级为 PASS；
- 不执行生产数据库、知识库、支付、发布或签约操作。

## 证据边界

自动检查通过仅表示仓库内 manifest 的结构、标识唯一性和归档路径引用满足静态规则。运行真实性与批次验收仍须依赖对应的原始运行证据和独立复核。
