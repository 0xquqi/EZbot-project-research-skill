# 本地验证记录 · 2026-10-28

本轮根据用户明确需求，重新读取公开项目官网、官方源码与技术规范。两套被禁止的研究 Skill 及其衍生研究资料没有用于本轮设计或答案。不能据此声称历史版本从未受过参考影响。

## 自动入口补充验证

新增自动网址/文本/合约入口，真实执行结果见 [自动研究记录](automatic-research-2026-10-28.md) 与 [结构化观察](automatic-research-2026-10-28.json)。这次由程序自动取页面、指南、源码、ABI并比较部署，宿主AI继续读函数实现后给出参与路径；不把材料采集当成研究完成。

## 可核对材料

- [原始来源目录](../skills/ezbot-project-research/references/source-catalog.json)：新读取的公开 URL、读取时间、原文件 SHA256 或明确的网页工具读取标记。
- [案例研究](../skills/ezbot-project-research/references/case-studies.md)：按本次原始资料写的研究结果与局限。
- [实际观察](observations-2026-10-28.json)：BUILD-100 页面、ABI、RPC 和源码验证服务的对照结果。
- [历史数量映射](../skills/ezbot-project-research/references/inventory.json)：只核对档案条目身份和去重，不以旧正文制定测试答案。

完整网页、前端配置与源码临时副本没有放入发布包，以免复制无关内容或公开网页中偶然出现的接口凭证。哈希是内容识别，不是独立采集证明；可按 URL 重新读取，动态网页可能改变。

## 执行过的检查

```bash
python3 -m unittest discover -s tests -v
python3 tools/check.py
```

实际离线工具调用：

```bash
python3 skills/ezbot-project-research/scripts/inspect_material.py page.html --url https://build-100.com/lab/#home --format html --abi element-abi.json
```

page.html 和 element-abi.json 来自本轮官网读取，未运行网页脚本来提取 ABI。真实浏览器另打开 #mint 查看渲染后的页面，没有输入钱包地址或执行交易。

公开 RPC 使用 eth_chainId、eth_getBlockByNumber、eth_getCode 与无钱包参数的 eth_call。请求链ID为56，代码与 Sourcify 返回的 onchainBytecode 相同。成功的 drawPrice 使用 latest；后续固定旧区块的尝试被 RPC 拒绝，错误原样保留，不作为未开放或售罄。

## 限制

工具测试验证离线解析，不证明语言模型语义准确率。案例由同一编写者研究，没有独立执行者或盲审，也没有实盘、用户资格、proof签名和跨模型测试。第三方网页与源码核验不等于安全审计。40条历史查阅记录的逐项依据仍缺失。

## 按公开说明补齐的方法与案例

[本轮能力核对](claim-acceptance-2026-10-28.md)记录新40条生态复核、15家族/16活动、14类带步骤的方法、九个固定块部署匹配，以及AnthroBit指南采集回归。新记录有真实日期，不替代缺失的旧40条索引。
