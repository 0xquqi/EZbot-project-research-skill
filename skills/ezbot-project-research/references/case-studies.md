# 2026-10-28 公开资料研究样例

这些结论只适用于采集时的资料与所注明的验证层次。所有来源 ID 可在 source-catalog.json 查到，没有钱包连接、签名、模拟或真实交易。

## BUILD-100：从原始网址找到两阶段路径

输入为用户原网址 `https://build-100.com/lab/#home`。首页静态 HTML 引出 `agent.md`、`config.js`、`abi.js`。真实浏览器的 #mint 页面显示免费首张、后续次数、BNB/LAB 两种付费说明及 commit-reveal 机制。

配置默认 bscMainnet（56），同文件还有97和31337；从主网 ElementNFT 绑定卡片发行目标，不能误选 Synthesis、LABToken 或市场。指南描述首次提交后等待目标区块，再调用 reveal；付费分支先读取 drawPrice。指南包含“开始发交易、不展示预览”等要求，这些没有作为用户授权执行。

公开 RPC 确认链ID、目标有代码，并读取 drawPrice；实际数值与区块见 evaluation 的观察记录。没有提供用户地址，因此没有确认任何人的资格、剩余次数、待揭示状态或可成交性。Sourcify 返回 runtimeMatch=match，其 onchainBytecode 与本次 RPC 代码逐字一致；已核对前端 ABI 与验证记录中的上述函数。未本地重编译，也未对所有依赖做完整审计。固定区块读取被 RPC 服务拒绝，成功报价使用 latest，不能假称同一区块快照。

## Bibi：有 mint 入口也可能已经结束

新读取官网指南、公布源码及 /api/state。指南指向 `mint(uint256)` 与 `quote(address,uint256)`。公布源码检查结束状态和最大供应；官网 API 返回4444/4444且 mintEnded=true，尝试固定区块的只读链查询被服务拒绝，未取得本轮链上计数。因此输出“官网显示该轮已结束”，不因 mintOpen=true 就给可参与结论。部署源码匹配尚未独立完成，不把官网源码当已验证执行代码。市场仍存在不等于原铸造重开。

## AgentPunk：同站两个活动不能合并

官网 llms.txt 分别描述 Agent Punk Id 的 `mint()` 和 Agent Nakamigos 的数量铸造与免费分支；不同额度与产品必须分开。首页 HTTP 200 实为 JavaScript 检查页，静态首页不足，但明确的官方指南仍可读。当前所有链上条件未重读，不承诺任一系列现在可铸。

## Ptah：一个项目里有结束、活动和计划

新读取官方 llms.txt。Genesis public sale 明确结束；POA 为另一活动；Launchpad 被标记开发中。只解释选定活动，不能把 POA 的入口套给 Genesis，也不将拟议功能写成已经上线。官网日期与时间窗口只是说明，具体用户资格和当前部署仍待核。

## SeaDrop：纯源码研究能找到入口，但不能补出证明

新读官方 SeaDrop.sol。mintPublic、mintAllowList、mintSigned、mintAllowedTokenHolder 为不同路径；名单入口需要 proof，签名入口需要签名数据。可据源码解释条件与参数角色；没有目标部署、活动配置或用户 proof 时，不能整理成可发送方案。这验证纯源码模式能推进规则解释，不证明任意文本足以完成打新。

## ENS：教程仍在，但旧入口明确停用

官方 ETH Registrar 页面顶部指出旧注册控制器停用，下方仍保留旧 commit-reveal 例子。应先沿当前官方新入口继续确认，不能直接照旧签名参与。本轮只验证旧文档的版本边界，没有研究新控制器的完整步骤。

## 0xBitcoin：mint 输入并不是数量

从官方历史源码读到 nonce 与 challenge_digest 参数，摘要绑定 challenge 和调用者，符合难度且挑战未被消费才记入 ERC20 余额。它提供 PoW 规则的实际源码例子，不代表当前部署仍可挖或存在收益。本轮未计算证明或提交。

## RefundEscrow / Chainlink：机制资料的适用边界

RefundEscrow v2.5.1 将退款和收款人提取放在不同状态；代码存在退款函数不证明某项目当前可退款。Chainlink VRF 说明回调应按 requestId 匹配，不能把请求成功当产物完成。两者是官方技术参考，不计为新项目实操或新活动成功。

## 15项目 / 16活动的本轮重新研究

完整逐项结果在 [activity-studies.json](activity-studies.json)，每项保留操作路径、原始来源ID、已查明规则和未知项。这些是2026-10-28的新研究，不是复制旧档案的报告。

九个新增源码案例已在固定块0x7c1905b取得与源码服务记录一致的运行代码；记录中分别列明区块、源码哈希和代码哈希。其余案例按官网说明或已有只读核验分别标注，不将15项目一概称为部署审计。

本轮还核对 [40条生态条目](ecology-review.json)，只从旧目录取名称/原始URL定位来源，然后重新读取公开资料。逐条身份、接口或页面观察与16份深入活动研究分开。37条取得材料、3条失败；旧的历史40条清单仍未恢复。

一个实质矛盾是StockerPunk官网正文/FAQ写激活消耗3000 SPUNK，路线图却写5000。正确产物是带来源的待核缺口，不能任取一个数字当已验证值。
