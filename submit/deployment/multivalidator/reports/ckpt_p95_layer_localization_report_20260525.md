# Checkpoint p95 layer localization — 重大澄清

- 生成 (UTC)：2026-05-25
- 任务：(c')-(ii)，在 `two_validator_pressure rep10` 定位"长 checkpoint 间隔"产生在哪一层
- 数据：既有 INFO 级 sui-node 日志（无需重跑），覆盖 7 个 validator + fullnode；fullnode 共 872 个 `execute_checkpoint{seq=N}` 事件，毫秒级时间戳
- 解析脚本：
  - `tools/ckpt_gap_localize.py` — 取 rep10 top-10 长间隔 + 各 validator 在 ±200ms 窗口的活动计数
  - `tools/ckpt_gap_compare.py` — 跨 4 个 rep (01/08/09/10) 比较真实间隔分布
- 详细产物：`reports/ckpt_p95_layer_localization_20260525044800.md`

---

## TL;DR — 结论顺位被颠覆

之前的根因报告（`ckpt_p95_root_cause_report_20260525.md`）说 `two_validator_pressure` 的 ckpt_p95 跨 rep CV ≈ 63% 是 "rare-tail 双故障命中事件" 造成的真实协议行为。

**(c')-(ii) 推翻该结论。** 真实情况：

1. **每个 rep 的实际逐 checkpoint 间隔分布几乎一致**（p50 215–218 ms, p95 270–293 ms）。真实跨 rep CV ≈ 4%。
2. **每个 rep 都有 2–4 个 ~2.5s 的极长间隔，定位在 epoch 边界**（每 60s 一次，与 `epoch_duration_ms=60000` 完全吻合，由 `sui_core::checkpoints::CheckpointBuilder` 重启造成，与 netem 故障无关）。
3. **`consensus_metrics.json` 报告的 `checkpoint_interval_ms_p95` 跨 rep 差异（226 vs 1004）是测量管线产生的失真**，不是协议行为差异。

故 `variance_table_20260525104240.md` 中 "two_validator_pressure ckpt_p95 CV ≈ 63%" 与基于此衍生的 figure / 讨论，需要重新口径化。

---

## 1. 现有日志即可定位（无需重跑）

D1 摸清：sui-node 容器输出由 `collect_container_state.ps1` 用 `docker logs --timestamps` 抓取，默认 INFO 级别（无 RUST_LOG 注入）。INFO 级别已含：

- `sui_core::checkpoints::CheckpointBuilder: Starting CheckpointBuilder` — epoch 切换标记
- `execute_checkpoint{seq=N}` — fullnode 端逐 checkpoint 执行时间戳（毫秒精度）

7 个 validator 容器日志总计 50 万行（每个 ~6.9 MB），fullnode 348 KB / 3561 行。**不重跑也能拿到逐 checkpoint 时间序列。** D2 跳过。

## 2. rep10 fullnode 实际间隔分布

| 统计量 | 值 |
| --- | ---: |
| 解析到的 checkpoint 数 | 872 |
| 连续 (seq, seq+1) 间隔数 | 871 |
| min | 1.4 ms |
| p50 | 217.9 ms |
| p95 | 285.5 ms |
| max | **2679.6 ms** |

### Top 4 长间隔（>2000 ms）的时间戳

| 长间隔 ID | from_seq → to_seq | gap (ms) | 时间戳 (UTC) |
| ---: | --- | ---: | --- |
| #1 | 789 → 790 | 2679.6 | 12:47:08.942 |
| #2 | 528 → 529 | 2639.9 | 12:46:08.911 |
| #3 | 266 → 267 | 2617.5 | 12:45:08.902 |
| #4 | 1 → 2 | 2510.1 | 12:44:09.064 |

**间隔均为 60s（59.84–60.04s）**，与 `prepare_multivalidator.ps1` 的 `EpochDurationMs=60000` 一致。这是 epoch 切换时 `CheckpointBuilder` 重新初始化造成的停顿，**所有场景所有 rep 都会出现**，与 netem 故障无关。

### 中间尾部（500–2000 ms）

| ID | gap | 时间戳 |
| ---: | ---: | --- |
| #5 | 770.1 | 12:45:11.629 |
| #6 | 687.0 | 12:44:08.377 |
| #7 | 646.8 | 12:45:27.530 |
| #8 | 536.3 | 12:47:11.733 |
| #9 | 534.0 | 12:46:23.800 |
| #10 | 508.0 | 12:45:17.598 |

这些可能与故障有关，但数量级远小于 epoch 停顿。

### 各 validator 在长间隔窗口的 consensus_round 计数

对 top-10 长间隔的 ±200ms 窗口扫 v1/v2/v3 日志（v1 被注 150±30ms 延迟，v2 被注 2% 丢包，v3 为对照）：

| 长间隔 | v1.consensus_round | v2.consensus_round | v3.consensus_round |
| ---: | ---: | ---: | ---: |
| #1 | 45 | 45 | 45 |
| #2 | 47 | 47 | 47 |
| #3 | 48 | 45 | 48 |
| #4 | 56 | 56 | 56 |

**三个 validator 的 consensus 推进几乎一致**（差 ≤ 4），说明共识层在 epoch 停顿期间**未被故障阻塞**。停顿不在共识层、也不在被故障注入的 v1/v2 上，而在 checkpoint 构建路径的 epoch 重启逻辑。

## 3. 跨 rep 实际分布对照（4 个 rep）

| rep | metric 报 p95 | 真实 n | 真实 p50 | 真实 p95 | 真实 max | n_gap>2000ms | n_gap∈(500,2000] | n_gap≤500 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rep01 | 226 | 711 | 215.7 | 270.5 | 2174 | 2 | 6 | 703 |
| rep08 | 674 | 887 | 218.3 | 293.2 | 2946 | 4 | 9 | 874 |
| rep09 | 669 | 832 | 216.9 | 277.9 | 3019 | 4 | 3 | 825 |
| rep10 | 1004 | 871 | 217.9 | 285.5 | 2680 | 4 | 8 | 859 |

**真实 p95 跨 4 rep 跨度 270–293 ms（CV ≈ 4%）。**

注意：rep09 的 metric p95 = 669，但其 mid-tail (500-2000ms) 只有 3 个，比 rep01 (6) 还少，metric 与真实尾部计数**不相关**。

## 4. metric 失真的机制

`extract_consensus_metrics.py` 的 `checkpoint_interval_ms_p95` 来源（L169–213）：

1. 每个 rep 取 `rpc_probe` 的 3 个阶段（warmup / fault_window / recovery），各 5 个样本 × 2 秒间隔 = **15 个时间锚**。
2. 对相邻两个锚 `(t_prev, seq_prev)` 与 `(t_cur, seq_cur)`，计算"平均间隔" = `(t_cur - t_prev) / (seq_cur - seq_prev)`。
3. 全 rep 产生 **~14 个桶平均值**，对这 14 个值取 nearest-rank C=1 的 p95。

失真链：
- 14 个样本的 p95 ≈ `sorted[13]`（即最大值或次大值）。
- 一个 2 秒探针桶若恰好跨越 epoch 边界 → 该桶包含 ~9 个正常间隔 (~220ms) + 1 个 ~2600ms 长间隔 → 桶平均 = (9×220 + 2600)/10 ≈ 458ms。**该桶的 seq_delta 越小（即 RPC 探到的桶里发生的 checkpoint 越少），平均拉高越多。**
- 是否跨边界 + 跨几个桶 + 边界的精确时点 共同决定 metric p95。这些都是探针时点与 epoch 切换时点的相对偏移决定的、与协议层行为弱相关。

因此 `consensus_metrics.json` 的 `checkpoint_interval_ms_p95` **既不是 p95 of true intervals，也不是 mean interval**，而是 "14 个二秒桶平均值的 p95"。

## 5. 工程含义

| 影响 | 说明 |
| --- | --- |
| 现有 `variance_table_20260525104240.md` 的 ckpt_p95 列 | 测量噪声 + 探针对齐偏置，不能解读为协议层不稳定 |
| 现有 `figures/checkpoint_count_boxplot_*.png` 中 p95 维度 | 同上 |
| `calibration_patch_20260525.json` 的 ckpt_p95 字段 | 同上（仿真校准用 rpc_latency_p50/p95，未使用 ckpt_p95，故 calibrate replay 不受影响） |
| 真实协议 ckpt 节奏在所有场景所有 rep | **极其稳定**（p50 CV < 3%，真实 p95 CV ≈ 4%） |
| 60s epoch 停顿事件 | 真实存在，但是 sui-node 的 epoch 管理开销，不是 BFT 共识本身 |

## 6. 论文写作建议（仍需用户批准）

如要把本观察写入论文：

- **不要**写"two_validator_pressure ckpt p95 CV 63%" — 这是测量伪影。
- 可以写："60 次工作负载固定的部署运行中，**真实**逐 checkpoint 间隔的 p50 在所有场景所有 rep 均稳定在 215–225 ms（跨 rep CV < 3%），p95 ≤ 295 ms（跨 rep CV ≈ 4%）。"
- 可以写："唯一不变的长间隔事件是 epoch 边界 CheckpointBuilder 重启（每 60s ≈ 2.6s 停顿），非共识层行为，与故障注入解耦。"
- 应在"测量层局限"小节补充：聚合 metric `checkpoint_interval_ms_p95` 因 rpc 探针窗口对齐 epoch 边界产生失真，建议未来直接从 fullnode 日志解析逐 checkpoint 时间序列。

## 7. (c')-(i) 双故障解耦对照 — 是否还要做

（用户原本同意 (iii) = 先 (ii) 后 (i) 串行。但 (ii) 的结论改变了 (i) 的必要性。）

(i) 原本目的是验证"双故障产生乘性效应"。基于本报告：

- 真实 p95 跨 rep 差异只有 ~10%，故障的影响远比 metric 暗示的小；
- 即便 (i) 跑了，预期能观察到的差异也只在 270–290 ms 区间内浮动，可能小于跨 rep 测量噪声；
- (i) 需要 1.5–2h Docker 时间和新建 2 个场景，**性价比已大幅下降**。

**建议**：(i) 可不跑。但若需要，必须先把 metric 提取改为"从日志直接解析"再跑，否则跑出来仍是失真的 metric。**待用户决定。**

---

## 产物清单

| 路径 | 用途 |
| --- | --- |
| `tools/ckpt_gap_localize.py` | rep10 top-10 长间隔 + 各 validator 活动计数 |
| `tools/ckpt_gap_compare.py` | 4 个 rep 真实间隔分布对照 |
| `reports/ckpt_p95_layer_localization_20260525044800.md` | 原始 long-gap 表 |
| 本文件 | 综合澄清 + 工程含义 + 论文建议 |
