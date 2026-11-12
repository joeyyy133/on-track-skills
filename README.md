# 软件开发协作套件 V1.1.0

两个独立可发现的 Skill：`$on-track-dev` 负责按需求推进，`$project-explainer` 负责理解与审查。自动发现默认开启；重要阶段由执行 Skill 主动解释，独立解释 Skill 也可随时调用。

开始：`使用 $on-track-dev 推进这个项目，先检查已有代码和最新确认要求。`
了解：`使用 $project-explainer 告诉我现在做到哪里，从入口到数据存储解释实现，并挑战重要假设。`
恢复：`使用 $on-track-dev 从磁盘状态恢复，核对当前需求版本，继续下一步。`

规则：先覆盖软件开发；目标/验收/范围/重要设计变化由用户确认；细节自主推进；V1.0.0 三段编号；源码原地更新、Git 留历史；Final 为确认后的版本指针；只保留当前 Final 与指定里程碑；每个重要阶段主动中文讲解。

需求、产品和 Skill 自身的版本互不混用。本套件版本 V1.1.0 不代表任何业务项目已获 Final 确认。Skill 不等于常驻 Agent，也不会自动创建计划任务、CI 或 hook。

安装入口为个人 `~/.codex/skills/` 下的同名符号链接，指向本目录的唯一源码，避免安装副本。请保留本目录；移动时需相应更新入口。新会话的可发现性需由客户端实际加载验证；本会话不因文件落盘而自动刷新技能列表。初始化业务项目时先读其规则并复用已有规范，不能在所有项目中无条件增加文件。

执行 Skill 附带 Python 标准库脚本，可 init/resume/snapshot/check/check --complete/check --release/check --final。初始化不覆盖已有记录，不自动创建 Git 仓库，不安装依赖，不发布、不清理用户文件。参考协议在该 Skill 的 references/protocol.md。

借鉴来源（未捆绑或安装）：
- https://github.com/obra/superpowers ：完成前验证、排错
- https://github.com/mattpocock/skills ：质询与决策说明
- https://github.com/github/spec-kit ：规格到实施
- https://github.com/morluto/rea ：证据、推断与未知的区分；按需调查发布产物

能力限制：结构校验不能证明日志真实性、用户确认真实性或测试充分性。需要真实工具调用和需求语义审查。REA、原生分析引擎、独立监督 Agent、自动运行的 Harness 均不随本套件安装。


## 从 GitHub 获取并调用

需要 Python 3.10+、Git。克隆本仓库时选择版本分支 `V1.1.0`，将两个 `skills/` 子目录作为本地 Skill 安装，或为当前 Agent 显式读取它们的 SKILL.md。每个 Skill 的脚本和 references 也必须一并获取，只读取网页中的 SKILL.md 不会自动安装依赖文件。

在 macOS/Linux 上，将本仓库克隆到长期保留的目录后，可将 `skills/on-track-dev` 和 `skills/project-explainer` 的绝对路径链接到客户端的个人 Skills 目录；同名技能已存在时先检查，不覆盖。当前客户端入口为 `~/.codex/skills/`。安装后在新会话检查技能是否可发现。

普通恢复：`python3 <技能目录>/scripts/ontrack.py resume <项目目录>`。它只读取记录，不执行 next_action。未使用本套件时也可阅读 references 中的流程并手动执行；没有 CI/hook 就不存在自动强制检查。

本仓库只包含自写指令、脚本与测试；参考项目未作为运行依赖安装或捆绑。核对范围及固定源码链接见 [参考核验](REFERENCES.md)。


仓库：https://github.com/joeyyy133/on-track-skills

获取固定版本：

```sh
git clone --branch V1.1.0 --single-branch https://github.com/joeyyy133/on-track-skills.git
```

也可以把这句话交给下一次的 Agent：

> 请读取 https://github.com/joeyyy133/on-track-skills 的 V1.1.0 版本，获取 skills/on-track-dev 和 skills/project-explainer 的完整目录，检查现有同名技能后安装；在项目中使用 on-track-dev 推进，使用 project-explainer 解释设计。

远程以版本分支分发，尚未创建 GitHub Release 或远程 Git 标签；需要严格固定内容时使用发布提交的完整哈希。不要把可移动分支名当作不可变身份。
