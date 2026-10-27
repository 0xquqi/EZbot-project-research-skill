# EZbot Project Research Skill

独立的加密项目研究 Skill：给 AI 一个项目网址、帖子或合约地址，让它沿官方网页、活动入口、公开源码与链上只读信息，解释项目是什么、怎么参与、当前有哪些条件，以及哪些结论还缺证据。

它包含研究指引、机制问题卡和公开历史案例。它不是训练后的模型，也没有内置网页抓取服务；实际阅读动态网页和查询链上状态，使用运行它的 AI 工具环境。没有这些能力时，报告会明确指出未核实部分。

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

将 `skills/ezbot-project-research` **整个目录**放入你的 AI 工具支持的 Skill 搜索目录，具体位置遵循该工具的说明。保持 `SKILL.md`、`agents` 和 `references` 的相对目录不变。也可直接让 AI 读取克隆目录内的 `skills/ezbot-project-research/SKILL.md`，随后按其中的相对链接读取资料。

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
| `references/question-cards.json` | 14 类机制问题 |
| `references/case-index.md` | 历史资料索引和迁移来源 |
| `references/*-cases.json` | 完整公开历史案例 |
| `references/source-catalog.json` | 本轮新读取的公开原始来源、时间与哈希 |
| `references/case-studies.md` | 网页、源码和只读链研究的实际样例 |
| `references/validation.md` | 功能验证范围与局限 |
| `scripts/inspect_material.py` | 离线解析 HTML、文本及 JSON ABI |
| `tools/check.py` | 独立包完整性、来源及文件边界检查 |

表中 `references` 和 `scripts` 均位于 Skill 目录内。原历史档案仍含5个基础活动、3份附加报告和10个生态案例；本轮不将它们作为新方法学习或测试答案来源。原有15项目/16活动的去重映射见 `references/inventory.json`；40条查阅记录缺逐项清单，尚未独立核验。

本轮14张问题卡以重新读取的官方项目材料和技术规范为依据，每张保留来源、支持点、限制和未实操标记。它们可以重叠，不能理解为14种已完成实盘验证的独立铸造技巧。

## 独立性与验证

这是全新仓库，未继承应用仓库的 Git 历史。发布内容仅包含本 Skill、说明、许可证与校验文件；不包含前端页面、服务器、钱包适配器、登录状态、数据库、密钥或其他项目代码。来源见 [案例索引](skills/ezbot-project-research/references/case-index.md)。

本地与 CI 均可运行，无第三方 Python 依赖：

```bash
python3 tools/check.py
python3 -m unittest discover -s tests -v
```

校验检查发布文件白名单、完整性哈希、内部文档链接、JSON 结构、问题卡字段边界及明显凭证/本地依赖痕迹。它不证明所有网站可抓取，也不代替实时合约验证或模型行为评测。发布清单只覆盖文件内容，修改文件后应审核变更再更新 `release-manifest.json`。

## 本轮实际验证

2026-10-28 使用公开官网、浏览器及只读 RPC 研究 BUILD-100，从首页找到指南、主网配置和精确 ABI，取得匹配服务记录并比较部署代码，读取当前报价。还研究了 Bibi 的结束条件、同站多系列、旧 ENS 入口、SeaDrop 证明入口、PoW 与退款/异步规则。细节见 [验证记录](evaluation/README.md)。

这是编写者参与的功能验证，没有使用用户钱包、没有交易、不是独立盲测或跨模型成功率评测。脚本仅整理已取得的材料，网页渲染和链查询仍依赖宿主工具。新项目需要重新核实，旧样例价格不能作为默认参数。

## 许可

原创说明、整理内容与校验代码使用 [MIT License](LICENSE)。历史资料中引用的第三方文字、代码片段和链接仍归原权利人，保留原来源；MIT 不替第三方授予额外权利。
