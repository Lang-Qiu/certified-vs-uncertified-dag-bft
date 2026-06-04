# Root cause: `two_validator_pressure` checkpoint_interval_ms_p95 instability

- 生成日期 (UTC)：2026-05-25
- 触发：`variance_table_20260525104240.md` 报告 `two_validator_pressure` 的 ckpt p95 跨 rep CV ≈ **63.23%**，是 60 次正式跑里唯一 CV > 20% 的指标
- 数据范围：6 场景 × 10 rep = 60 次正式跑（`data/runs/<scenario>_<seed>_rep01..10`）；无外部新跑
- 数据生成脚本：`tools/ckpt_root_cause.py`；原始明细：`reports/ckpt_p95_root_cause_20260525043728.md`

---

## 1. 现象（已观察）

`two_validator_pressure` 的 `checkpoint_interval_ms_p95` 跨 10 rep 不服从单峰：

| rep | ckpt_p95 (ms) | ckpt_count | wall_clock (s) |
| ---: | ---: | ---: | ---: |
| 01 | 226 | 680 | 178.6 |
| 02 | 226 | 676 | — |
| 03 | 250 | 675 | — |
| 04 | 334 | 682 | — |
| 05 | 291 | 681 | — |
| 06 | 254 | 716 | — |
| 07 | 290 | 723 | — |
| 08 | **674** | 810 | — |
| 09 | **669** | 787 | — |
| 10 | **1004** | 817 | 223.2 |

- 前 7 rep 的 p95 落在 226–334 ms（与 `crash_one_validator` 的 290 ms 中位数同级）。
- 后 3 rep（08/09/10）跳到 **669–1004 ms**，是中位数的 2.3–3.5 倍。
- 同一组 rep 的 `checkpoint_count` 也最大（787–817 vs 中位数 682）。
- rep10 wall-clock 比 rep01 长 26%（224s vs 179s）。

对照场景：

| scenario | ckpt_p95 中位数 | min | max | CV |
| --- | ---: | ---: | ---: | ---: |
| baseline | 226 | 225 | 253 | 5.82% |
| delay_low | 226 | 225 | 253 | 3.72% |
| delay_high | 254 | 250 | 256 | 0.69% |
| loss_low | 288 | 225 | 339 | 12.53% |
| crash_one_validator | 290 | 253 | 338 | 8.97% |
| **two_validator_pressure** | **290** | 226 | **1004** | **63.23%** |

—— 其他场景 CV 均 ≤ 13%，max/median 比值 ≤ 1.17；`two_validator_pressure` max/median = 3.46。

## 2. 隔离测试（已观察）

| 检验项 | 结果 |
| --- | --- |
| `ckpt_interval_ms_p50` 跨 rep | **稳定**，CV 0.21–2.78%（所有场景）。p50 不随 p95 变化。 |
| `rpc_latency_ms_p50/p95` 跨 rep | 稳定，p50 ∈ [3, 11]，p95 ∈ [20, 28]。10 个 rep 之间无明显趋势。 |
| `availability_ratio` | 全部 = 1.000（10/10） |
| `successful_transactions` | 全部 = 60（10/10），工作负载完成 |
| `failed_transactions` | 全部 = 0（10/10） |
| `fault_timeline.jsonl` (rep 01/08/09/10) | 完全一致：`netem delay=150ms jitter=30ms` 注入 validator-1；`netem loss=2%` 注入 validator-2；两动作均 `status=applied`，无 inject 失败 |
| `controller_record.json.faults` | 10 个 rep 字段完全一致（同 delay、同 jitter、同 loss%） |

—— 故障**配方**完全相同；唯一的随机源是 (a) 故障注入到协议运行的相对时点，(b) netem jitter 和 loss 的伪随机选择。

## 3. 假设（尚未直接验证，但与数据一致）

**H：rare-tail event hypothesis** — 高 p95 源于"工作负载窗口内**某一轮**检查点恰好被 validator-1 的 150±30 ms 延迟与 validator-2 的 2% 丢包**双重命中**"产生的稀有长间隔事件；该事件在每个 rep 内最多发生 1–2 次，但被 p95（10 rep × ~70 ckpt = ~700 间隔样本里的第 95 百分位）放大。

支持证据：
- p50 极稳（CV < 3%）说明协议**主流推进节奏**未受影响；只有少数间隔被拉长。
- `ckpt_count` 在尾部三 rep 同向上升（787–817 vs 中位 682）：发生长间隔事件 → 工作负载完成时间被拖长 → 在拖长的时窗内继续产出检查点 → count 累计上升。
- 工作负载固定 60 tx（非时长固定），故 "stall → catch-up → 更多 ckpt" 的因果链与数据吻合。
- 故障注入完全一致 → 唯一可解释的差异源是**事件时点的随机性**，与 H 一致。

不支持 / 不可断言的方向：
- 不是 RPC 层问题（rpc_latency 稳定）。
- 不是可用性事件（availability = 1.0 ，failed_tx = 0）。
- 不是 systematic shift（p50 不变）。
- **不能**断言"两个故障互相加剧"——本数据只有 `two_validator_pressure` 一个双故障场景，没有 `delay_only_validator_1` + `loss_only_validator_2` 的解耦对照来验证乘性 / 加性效应。

## 4. 与 `loss_low` 场景的对照（次级观察）

`loss_low`（单 validator 2% 丢包）也有较高 CV（12.53%）和 max 339 ms。但分布**单峰右偏**：中位 288，max 339，没有 600+ 跳跃。这与 H 一致——单故障 rare-tail 事件较少且较弱。

## 5. 不能由本数据回答的问题

1. 长间隔事件具体在协议哪一层产生（mempool flush?  consensus round wait?  fullnode RPC?）—— 需要在 sui-node 容器里打开 `RUST_LOG=info` 级别的 mysticeti / consensus 日志，逐 round 跟踪 vote 提交时点。本批运行未开启详细日志。
2. 若把 `delay_validator_1` 和 `loss_validator_2` 解耦做对照（"互不命中"），p95 尾部是否消失—— 需新增 2 个场景（`delay_only_v1`、`loss_only_v2`）各 10 rep，超出当前已完成 60 次的范围。
3. 长间隔事件是否在每个 rep 内随时间均匀分布—— 需要 per-checkpoint 时间戳明细，当前 `consensus_metrics.json` 仅保留聚合 p50/p95/count，未保留原始 interval 序列。

## 6. 论文写作建议（仅作建议，**不擅自回填**）

如要把本观察写入论文，建议：

- 把 `two_validator_pressure` 的 ckpt p95 报为**双峰**而非"中位数 ± 标准差"（后者隐藏了真实形态）。
- 在 §7.4 / §7.6 讨论拥塞反馈与条件性优势时，引用"60 次工作负载受限运行中 3/10 个 `two_validator_pressure` rep 出现 p95 ≥ 600 ms 的稀有长间隔事件，主流节奏（p50）保持 223 ms"作为**条件性优势随机性**的工程实证。
- 注明 `recovery_time` 字段对该场景未触发（无 fault_timeline.recovery 事件），故无 recovery 维度的数值证据。
- 显式声明：本数据**不能**支撑"双故障产生乘性效应"的断言；如需该断言，需补做解耦对照实验。

—— 是否回填、回填到哪个 §、是否补做解耦对照实验，均**待用户决定**（受 `[[paper-integration-approval-gate]]` 拦截）。

---

## 7. 产物清单

| 路径 | 用途 |
| --- | --- |
| `tools/ckpt_root_cause.py` | 数据收集脚本（可复跑） |
| `reports/ckpt_p95_root_cause_20260525043728.md` | 60 rep × 9 字段全量明细 + 6 场景分布 + Tukey 外点表 |
| `reports/ckpt_p95_root_cause_report_20260525.md`（本文件） | 现象→隔离→假设→局限的综合分析 |
