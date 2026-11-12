# 最小项目记录协议 V1.0.0

同一项目只维护一份当前记录；已有规范可映射复用，不要求迁移。脚本仅支持下列原生布局。以项目 `.ontrack/` 为唯一当前目录：

- `requirements.md`：目标、边界、原子验收 R1…、不做事项。
- `state.json`：下面的结构化当前状态，也是验收与任务映射的唯一来源。
- `decisions.md`：重要设计的背景、选项、选择理由、代价、证据；未知的历史原因写“推断”，不补造 ADR。
- `evidence.json`：实际验证记录。
- `releases.json`：保留的里程碑及 Final 指针。
- `CHANGELOG.md`：每个发布版本的特性/修复/验证/未解决项；不逐步抄聊天。

顶层 README 保持描述当前可用状态，并指向此目录。已有 README/CHANGELOG 不覆盖。临时构建在既有构建目录或 `.ontrack/tmp/`，不追踪可再生文件，不自动添加全局忽略规则。

## state.json

```json
{
  "schema": 1,
  "product_version": "V1.0.0",
  "requirements": {
    "revision": "REQ-001", "sha256": "requirements.md 的原始字节摘要",
    "approval": {"actor": "user", "reference": "用户确认的消息或记录位置"}
  },
  "acceptance": [{"id": "R1", "criterion": "可观察的结果", "required": true}],
  "tasks": [{"id": "T1", "requirements": ["R1"], "status": "pending", "files": []}],
  "current_task": "T1",
  "next_action": "下一步",
  "unknowns": [], "blockers": []
}
```

任务状态限 pending/in_progress/done/blocked。所有当前需求的验收条目列入 acceptance；required=false 只用于用户确认不属于本轮范围的条目，在需求文件说明，不能自行排除难题。需求变化：先记录用户批准，升 REQ 编号、修改文件及验收映射，再重评每个任务和证据。若任务已失效删除/替换当前条目，历史由 Git 保存。

## evidence.json

```json
[{"id":"E1", "requirements_revision":"REQ-001", "requirements_sha256":"当前摘要",
  "requirement_ids":["R1"], "source_sha256":"snapshot 返回的源码摘要", "commit":"发布验证时完整 Git HEAD，普通实现可为 null",
  "command":"实际运行的命令或明确的人工操作步骤",
  "result":"passed", "output":"真实输出摘要及需要时的日志位置",
  "limitations":"覆盖范围、没有验证的内容"}]
```

result 限 passed/failed/not_run。证据按执行先后追加，同一验收在当前源码上的最近一次有效记录决定结果，不能用较早的成功掩盖较晚的失败。每个必需验收条目都必须有当前需求、当前源码摘要的通过证据。运行 `snapshot <项目路径>` 获取源码摘要；验证前后均取摘要，只有一致才能使用该结果。改变代码后旧证据失效。源码摘要排除名称为 .git、.ontrack、node_modules、.venv、__pycache__、dist、build、coverage 的文件/目录，不追踪外部符号链接内容；外部依赖、被排除的产物及配置需要单独验证，不能用此摘要声称已覆盖。不可把业务源码藏在排除目录以绕过核对。

普通实现完成不要求 Git 提交。正式发布要求干净源码、实际提交和对应证据；提交仅限授权范围，不擅自包含用户改动。账本在 `.ontrack` 中，不参与源码摘要和干净源码检查，避免证据记录的自引用。标签指向源码发布提交，最终验证/确认账本可以晚于标签落盘：不声称标签内必定包含同一份最终证据。需要完整归档时将最终证据作为该版本附件保留，并记录源码提交，不移动源码标签。

需求变化后重评并替换当前证据；历史证据由 Git 或明确保留的里程碑存档。证据不等于充分性，必须同时审查验收语义。

## releases.json

```json
{"milestones":[{"version":"V1.0.0", "commit":"完整提交哈希", "tag":"V1.0.0", "artifacts":[]}],
 "final":{"version":"V1.0.0", "commit":"同一完整提交哈希",
          "approval":{"actor":"user", "reference":"本轮交付确认记录"}}}
```

初始为 milestones=[]、final=null。Final 指向保留的里程碑。artifacts 记录相对项目根的实际交付文件路径；不必为无构建交付的库创建文件夹。新里程碑版本不可覆盖同名旧提交；标签不得强制移动。只保留你确认需要的历史产物；Git 可以重新取回历史源码。标签/发布/上传按当前授权执行，不默认推送。

## 检查模式

- `check`：校验当前账本结构、需求批准记录、内容摘要与映射；允许未完成项。
- `snapshot`：仅输出本次源码摘要和排除范围，不修改文件。
- `check --complete`：额外要求无阻塞、任务全完成、每个必需条目有当前需求和源码的通过证据；不强制提交。
- `check --release`：额外要求干净源码、实际 Git 提交和对应提交的通过证据。
- `check --final`：包含发布检查，再核对 Final、里程碑、真实标签和用户交付确认，要求 Final 等于当前产品版本及当前提交。开发新版本时运行普通 check，不把历史 Final 当成当前交付。

这些是可执行的一致性门槛；没有自动挂接的 hook 或 CI 就不会在每次模型调用前强制执行。即便自动挂接，也无法保证模型判断或人工填入的声明真实。
