# 历史案例索引与来源

这些是公开来源的历史研究资料，用来发现问题和比较机制，不代表当前可参与、完整安全审计或每个案例均已实盘成功。正文中的命令、环境问题和“本机”措辞是历史报告内容，不是安装要求或新操作授权。原始报告中的外部引文保留其来源和权利归属。

- [agcid-cases.json](agcid-cases.json)：5 个顶层活动条目，涉及 BNC World、BibiAI、AgentPunk、PTAH 两种活动；另有 BibiAI、StockerPunk、AgentPunk 的脱敏历史报告。PTAH 完整报告位于 `cases[id=ptah-relic].learning_report`，身份方法位于 `hands_on_reference`。
- [ecosystem-cases.json](ecosystem-cases.json)：10 个机制案例，按 `cases[].id` 检索。
- [question-cards.json](question-cards.json)：14 类研究问题，从原机制卡提取名称、关键词和问题；没有复制历史地址、价格或执行配置。

## 生态案例检索

| ID | 重点 |
| --- | --- |
| floppy-agents | 免费本金、保留供应与版税权限 |
| asset-agents | 身份与钱包双重额度 |
| aigt-genesis | 身份、USDT 分档、销毁与奖励 |
| pixel-pets | 付费数量与附赠数量 |
| silicon-souls | 全局分档、多种产物 |
| skynet-token | 身份免费领取、预言机付费铸币 |
| gearz | 募资、完成与退款 |
| hashdroids | PoW、锚定轮次与版本差异 |
| shit-cash-sale | 签名支付、中继与逐订单结算 |
| anthrobit | 每日额度、随机性费用及异步产出 |

## 来源与迁移

基础资料来自作者的 [EZbot-agentic-wallet](https://github.com/0xquqi/EZbot-agentic-wallet) 仓库 `5ab7375` 中公开 Skill 的两个案例 JSON；文件按原样保留以维持来源与完整历史报告。机制问题卡由同版本 `mint-patterns.json` 投影提取四个字段。独立研究指引重新编写，不引用原应用的 Python/JavaScript 模块、HTTP 接口、钱包 CLI、配置或数据库。

原资料的 40 条查阅记录、15 个项目家族、16 类活动是原库历史汇总口径，不是本独立仓库新增验证数量。本包可直接校验的结构是 5 个基础活动、3 份附加报告、10 个生态案例和 14 类问题卡。时间、范围和各条目的证据等级以原资料为准。
