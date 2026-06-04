# Stage 7 多验证者实验边界

本目录冻结阶段 0 的实验边界与环境基线，后续阶段应以这里的资源预算、环境快照和清单校验为入口。

## 证据边界

- 主证据来自真实 `N=7` 多验证者部署实验，容错设定为 `f=2`。
- 内部 swarm 或 test-cluster 只用于预校准、配置排障和复现实验前的烟测。
- 内部 swarm 或 test-cluster 的结果不能替代真实 `N=7` 多验证者数据，也不能作为最终论文的主要实验结论。
- 每次正式采集前应运行 `scripts/check_docker_budget.ps1`，并保留生成的 `data/manifests/environment_snapshot.json`。

## 本机资源预算

资源预算固定在 `config/resource_budget.yaml`：

- 主机内存：16 GB
- Docker Desktop 内存：12 GB
- 验证者数量：7
- 单个验证者内存上限：1 GB
- 支撑服务内存上限：2 GB
- 推荐并行场景数：1

为了保证稳定性和测量质量，一次只运行一个实验场景。运行期间应尽量关闭浏览器、IDE 扩展、同步工具等后台负载。

## 环境快照与校验

```powershell
.\stage7_deployment\multivalidator\scripts\check_docker_budget.ps1
python .\stage7_deployment\multivalidator\tools\validate_manifest.py --environment .\stage7_deployment\multivalidator\data\manifests\environment_snapshot.json
```

当 Docker 不可用时，脚本仍会生成环境快照；不可采集的 Docker 字段会保留为空字符串或 `null`，原因记录在 `warnings`。

## 论文级多验证者实验入口

中文执行计划见 `reports/论文级多验证者共识实验计划.md`。

计划矩阵：

```powershell
powershell -ExecutionPolicy Bypass -File .\stage7_deployment\multivalidator\scripts\run_experiment_matrix.ps1 -MaxRuns 0
```

单次正式链路试跑：

```powershell
powershell -ExecutionPolicy Bypass -File .\stage7_deployment\multivalidator\scripts\run_experiment_matrix.ps1 -MaxRuns 1 -StartCompose -WorkloadDurationSeconds 60
```

完整矩阵运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\stage7_deployment\multivalidator\scripts\run_experiment_matrix.ps1 -MaxRuns 60 -StartCompose -WorkloadDurationSeconds 60 -ContinueOnFailure
```
