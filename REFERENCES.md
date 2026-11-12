# V1.1.0 上游核验与取舍

核对日期：2026-11-13。读取了下列固定提交中的实际文件；不是仅凭 README/星数推荐。没有安装或实测完整上游框架，没有复制上游源文件。

| 来源 | 核对文件 | 补充的机制 | 不采用的部分 |
|---|---|---|---|
| Superpowers | [verification-before-completion](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/verification-before-completion/SKILL.md) | 按声明类型选择证明，检查真实输出 | 不把全部小改动强制变成整套开发流程 |
| GSD | [resume-project](https://github.com/gsd-build/get-shit-done/blob/bdcaab2c752d9a33a1a1ca9acf3a3c81fb991815/get-shit-done/workflows/resume-project.md) | 恢复时读需求、状态、未完成工作和真实工作区 | 不默认创建新的状态体系或删除原有交接文件 |
| OpenSpec | [getting-started](https://github.com/Fission-AI/OpenSpec/blob/d12c2817776779e06891d68230773b3bb673b106/docs/getting-started.md) | 分清当前基线与待定变更，记录确认后再同步 | 不为每次变更保存重复源码，不同步维护第二套规格 |
| Ralph | [circuit_breaker.sh](https://github.com/frankbria/ralph-claude-code/blob/11f9df5becc8093ff2265542107e8e53a42e9970/lib/circuit_breaker.sh) | 停滞识别及停止盲目重试的思路 | 其部分进展判断依赖完成信号、自报或文件变化，不能作为产品验收；不安装循环器 |

补充方式为自写规则与本地脚本，不包含或自动安装上游 Skills。REA 仍是可选调查工具；仓库内的 rea.md 记录其边界。

验证：本套件 19 项自动化测试加独立文档行为审查。审查场景包括已有 OpenSpec、尚待决定的需求、旧成功/新失败及缺失历史设计记录。修复了映射布局与原生验收脚本的冲突。该审查不是模型稳定服从率评估，也不是业务功能测试。
