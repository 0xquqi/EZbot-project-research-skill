# EZbot Project Research Skill

独立的加密项目研究 Skill：给 AI 一个项目网址、帖子或合约地址，让它沿官方网页、活动入口、公开源码与链上只读信息，解释项目是什么、怎么参与、当前有哪些条件，以及哪些结论还缺证据。

它包含研究指引、自动网页采集与合约只读核验工具、机制问题卡和公开历史案例。加载它的 AI 负责确定目标、理解规则并交付研究结果；辅助程序自动取得公开材料与部署证据。动态页面使用宿主浏览器，缺少工具或证据时会交代具体未核实部分。

## 能做什么

- 从项目首页寻找 Mint、Claim、文档及活动入口，区分页面外壳、动态路由和实际参与路径。
- 分析 NFT 铸造、代币领取、购买、身份额度、签名白名单、合成、随机性、PoW、退款和多阶段活动。
- 区分已铸数量与剩余供应、单价与总价、NFT 收件人与费用收款人，避免把网络错误误报为未开放。
- 产出带来源、时间、费用、资格、当前阶段及未知项的研究报告。

研究结束不会连接钱包、签名、授权或发送交易；这个仓库也不提供钱包网站或交易后端。历史案例用于提出问题，旧地址、价格和资格不能直接用于新项目。

## 安装与使用

```bash
git clone https://github.com/0xquqi/EZbot-project-research-skill.git
cd EZbot-project-research-skill
```

将 `skills/ezbot-project-research` **整个目录**放入你的 AI 工具支持的 Skill 搜索目录，具体位置遵循该工具的说明。保持 `SKILL.md`、`agents`、`references` 和 `scripts` 的相对目录不变。也可直接让 AI 读取克隆目录内的 `skills/ezbot-project-research/SKILL.md`，随后按其中的相对链接读取资料。

支持 Skill 调用的环境中可使用：

> 使用 $ezbot-project-research 研究这个项目网址：〈项目官网〉。找到当前活动和铸造路径，核对资格、数量、费用与开放状态，列出来源和未知项。

更多例子：

> 分析这条公告和合约地址，判断这是 NFT 铸造还是代币领取，前后分别需要做什么。

> 这个项目先购买再合成，帮我分开核对每一步的消耗、产物和退款条件。

> 页面显示未开放，但 RPC 查询失败了。区分已经验证的关闭条件与读取失败，不要替我发交易。

宿主需要网页阅读能力；动态站点可能需要浏览器；实时资格与合约状态可能需要公开区块浏览器或只读 RPC。无需安装原工作台，也不需要钱包登录、私钥、应用数据库或原工作台的配置。

## 文件说明

| 文件 | 用途 |
| --- | --- |
| `skills/ezbot-project-research/SKILL.md` | Skill 入口和研究流程 |
| `references/web-research.md` | 网页到活动及参与路径 |
| `references/contract-research.md` | 部署、源码、ABI 与实时状态 |
| `references/participation.md` | 铸造、领取、退款等多阶段机制 |
| `references/report-format.md` | 研究报告与证据结构 |
| `references/question-cards.json` | 14 类机制研究方法：步骤、实例、反例及限制 |
| `references/activity-studies.json` | 15个项目家族、16项活动的新原始资料研究及九个部署核验 |
| `references/ecology-review.json` | 40条本轮生态复核记录，包含未取得材料的情况 |
| `references/case-index.md` | 历史资料索引和迁移来源 |
| `references/*-cases.json` | 完整公开历史案例 |
| `references/source-catalog.json` | 本轮新读取的公开原始来源、时间与哈希 |
| `references/case-studies.md` | 网页、源码和只读链研究的实际样例 |
| `references/validation.md` | 功能验证范围与局限 |
| `scripts/inspect_material.py` | 离线解析 HTML、文本及 JSON ABI |
| `scripts/research.py` | 自动取网页、跟进指南、获取验证源码并核对部署/只读状态 |
| `references/automatic-research.md` | 网址、文本、合约三种输入的操作与交付步骤 |
| `tools/check.py` | 独立包完整性、来源及文件边界检查 |

表中 `references` 和 `scripts` 均位于 Skill 目录内。原历史档案仍含5个基础活动、3份附加报告和10个生态案例；本轮不将它们作为新方法学习或测试答案来源。原有15项目/16活动的去重映射见 `references/inventory.json`。

2026-10-28重新研究了15个项目家族、16项活动；另建40条生态复核记录，逐条记录来源、时间、哈希及观察，其中37条取得公开材料，3条读取失败。**旧汇总的40条原始索引仍未恢复，新记录不回填为历史证据。** 目录条目的身份/接口核对与深入活动研究是不同范围，也不相加成为实盘成功数。

本轮14类方法以重新读取的官方项目材料和技术规范为依据，每类有操作步骤、原始材料实例、反例、限制和未实操标记。它们可以重叠，不能理解为14种已完成实盘验证的独立铸造技巧。

## 独立性与验证

这是全新仓库，未继承应用仓库的 Git 历史。发布内容仅包含本 Skill、说明、许可证与校验文件；不包含前端页面、服务器、钱包适配器、登录状态、数据库、密钥或其他项目代码。来源见 [案例索引](skills/ezbot-project-research/references/case-index.md)。

本地与 CI 均可运行，无第三方 Python 依赖：

```bash
python3 tools/check.py
python3 -m unittest discover -s tests -v
```

校验检查发布文件白名单、完整性哈希、内部文档链接、JSON 结构、问题卡字段边界及明显凭证/本地依赖痕迹。它不证明所有网站可抓取，也不代替实时合约验证或模型行为评测。发布清单只覆盖文件内容，修改文件后应审核变更再更新 `release-manifest.json`。

## 自动研究怎么运行

用户直接把网址或铸造说明交给加载本 Skill 的 AI 即可；AI 按入口文档调用工具、读取材料、核对规则并交付参与路径。无需用户预先取得 ABI 或手工抓网页。

辅助入口也可手动调用（从 Skill 目录运行，使用新的输出目录）：

```bash
python3 scripts/research.py --url 'https://example.org/activity/#mint' --out /tmp/project-web-new
```

文本或合约模式及只读 RPC 参数见 [自动研究入口](skills/ezbot-project-research/references/automatic-research.md)。辅助工具需要 Python 3.10+、系统 curl 和网络；不需要模型密钥或钱包。它输出供 AI 阅读的材料包，最终规则解释仍由 AI 完成。

## 本轮实际验证

2026-10-28 使用公开官网、浏览器及只读 RPC 研究 BUILD-100，从首页找到指南、主网配置和精确 ABI，取得匹配服务记录并比较部署代码，读取当前报价。还研究了 Bibi 的结束条件、同站多系列、旧 ENS 入口、SeaDrop 证明入口、PoW 与退款/异步规则。细节见 [验证记录](evaluation/README.md)。

这是编写者参与的功能验证，没有使用用户钱包、没有交易、不是独立盲测或跨模型成功率评测。离线脚本整理材料，自动入口可采集网页并核对公开 EVM 部署；动态网页和复杂参数的链查询由宿主工具补齐。新项目需要重新核实，旧样例价格不能作为默认参数。

补充核验九个公开部署的代码匹配，并用AnthroBit实际首页检验自动探索；修复多语言规则页占满预算、遗漏官方指南的问题。按公开说明逐项核对的结果与具体研究交付见 [能力验证](evaluation/claim-acceptance-2026-10-28.md)，保留未找到的历史依据与每例缺口。

## 许可

原创说明、整理内容与校验代码使用 [MIT License](LICENSE)。历史资料中引用的第三方文字、代码片段和链接仍归原权利人，保留原来源；MIT 不替第三方授予额外权利。
