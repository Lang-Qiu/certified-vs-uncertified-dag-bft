# 实验镜像构建 + Phase A 冒烟（stage9 cert-gate / Δ_recover）

宿主缺 clang/cmake/MSVC → 所有构建在 `rust:1.92-bookworm` 容器内，经 Clash 代理 `host.docker.internal:7897`（需 Docker Desktop 运行 + Clash「Allow LAN」）。cargo 缓存持久化于 Docker 卷 `stage9_cargo_registry`、`stage9_target`。

## 0. 已验证（2026-05-30，全绿）
- `cargo check -p consensus-core` ✅（8m13s）—— cert_gate toggle + Δ_recover 旋钮 + parameters.rs 编译通过。
- release 构建 ✅（`-j1`，61m29s）—— `sui` 207MB / `sui-node` 124MB，版本 `1.74.0-62ee6ada958c-dirty`（pinned commit + 本地编辑）。
- 运行时镜像 `stage9-sui-certgate:local` ✅（427MB，`docker/Dockerfile.runtime` COPY 预编译二进制）。
- **boot 冒烟** ✅：单容器 `--force-regenesis`，checkpoint 0→141→173→205 稳定推进 → 镜像是 stage7-sui:local 的合格 drop-in。
- **旋钮 plumbing 冒烟** ✅：`SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS=120` + `SUI_CONSENSUS_CERTIFICATE_GATE=1` 启动，推进到 ckpt 96，**无 panic/fatal**；单容器无 fetch → Δ_recover 正确地无副作用（符合设计）。
- **OOM 教训**：`-j2` 全 release 编译峰值 >12GB 撑爆 WSL2 引擎；改 `CARGO_BUILD_JOBS=1` 后稳。

## 1. release 构建（reuse cache，后台进行中）
```bash
MSYS_NO_PATHCONV=1 docker run --rm \
  -v "E:/LQiu/lab_folder/Blockchain_final_pipeline/stage9_cross_protocol_calibration/sui-src:/src" \
  -v stage9_cargo_registry:/usr/local/cargo/registry -v stage9_target:/src/target \
  -e http_proxy=http://host.docker.internal:7897 -e https_proxy=http://host.docker.internal:7897 \
  -e CARGO_NET_GIT_FETCH_WITH_CLI=true rust:1.92-bookworm \
  bash -c "export PATH=/usr/local/cargo/bin:\$PATH && apt-get update >/dev/null 2>&1 && apt-get install -y --no-install-recommends clang cmake protobuf-compiler libssl-dev pkg-config llvm git >/dev/null 2>&1 && git config --global http.proxy http://host.docker.internal:7897 && cd /src && cargo build --locked --release --bin sui --bin sui-node"
```
产物在 `stage9_target` 卷的 `/src/target/release/{sui,sui-node}`。

### ⚠️ OOM 教训（2026-05-30）
`-j 2` 的全 Sui release 编译峰值内存超过 Docker Desktop 12GB → **WSL2 引擎崩溃**（`unexpected EOF` + 之后 daemon 500）。host 仅 16GB。
**修复**：(1) 重启 Docker Desktop；(2) 重建用 **`CARGO_BUILD_JOBS=1`** 降峰值内存（慢但稳；缓存卷使其增量续编，不从零开始）；(3) 可在 Docker Desktop 设置里把内存调到 ~13–14GB（host 16GB 上限内）。

降内存版重建命令（其余同上，仅加 `-e CARGO_BUILD_JOBS=1`）：
```bash
MSYS_NO_PATHCONV=1 docker run --rm \
  -v "E:/LQiu/lab_folder/Blockchain_final_pipeline/stage9_cross_protocol_calibration/sui-src:/src" \
  -v stage9_cargo_registry:/usr/local/cargo/registry -v stage9_target:/src/target \
  -e http_proxy=http://host.docker.internal:7897 -e https_proxy=http://host.docker.internal:7897 \
  -e CARGO_NET_GIT_FETCH_WITH_CLI=true -e CARGO_BUILD_JOBS=1 rust:1.92-bookworm \
  bash -c "export PATH=/usr/local/cargo/bin:\$PATH && apt-get update >/dev/null 2>&1 && apt-get install -y --no-install-recommends clang cmake protobuf-compiler libssl-dev pkg-config llvm git >/dev/null 2>&1 && git config --global http.proxy http://host.docker.internal:7897 && cd /src && cargo build --locked --release --bin sui --bin sui-node"
```

## 2. 提取二进制 → 薄运行时镜像
```bash
# 2a. 从 target 卷提取到 docker/bin/
mkdir -p stage9_cross_protocol_calibration/docker/bin
MSYS_NO_PATHCONV=1 docker run --rm \
  -v stage9_target:/t \
  -v "E:/LQiu/lab_folder/Blockchain_final_pipeline/stage9_cross_protocol_calibration/docker/bin:/out" \
  debian:bookworm-slim sh -c "cp /t/release/sui /t/release/sui-node /out/ && chmod +x /out/sui /out/sui-node"

# 2b. 构建薄运行时镜像（Dockerfile.runtime，COPY 预编译二进制，无需代理）
MSYS_NO_PATHCONV=1 docker build \
  -f stage9_cross_protocol_calibration/docker/Dockerfile.runtime \
  -t stage9-sui-certgate:local \
  stage9_cross_protocol_calibration/docker
```
（替代方案：`Dockerfile.certgate` 一步式 `docker build`，但会在 build 内重编译且需 build-time 代理；上面的 run+extract 复用缓存更快。）

## 3. Phase A Δ_recover 冒烟（最小对照）
stage7 多验证者 compose 用 `SUI_IMAGE` 环境变量选镜像，故无需改 compose 文件本体：
```bash
# 基线（旋钮 off）：
$env:SUI_IMAGE = "stage9-sui-certgate:local"
# 跑一格 n=7 baseline（沿用 stage7 脚本）

# Δ_recover on：给验证者容器注入 env SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS=<ms>
# （需在 compose 的 validator service environment 加该 env，或用 compose override 片段）
```
**冒烟判据**：旋钮 off 时 cadence 应与 stage7 stage7-sui:local 基线一致（镜像等价自检）；on 时仅在发生 reconciliation fetch 的场景下 p95 抬升（无故障时无 fetch → 无效果，符合预期）。

## 待办（旋钮注入到 compose）
- 需要一个 compose override（`compose.multivalidator.certgate.yaml`），给每个 validator service 加 `environment: SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS=${RECOVER_MS:-0}`，并把 `SUI_IMAGE` 指向 `stage9-sui-certgate:local`。Phase A 矩阵脚本据此逐 cell 设 `RECOVER_MS`。
