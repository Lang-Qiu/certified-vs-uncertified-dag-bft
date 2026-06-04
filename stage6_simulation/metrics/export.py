"""
export.py
=========
成本台账与扫参结果的留存导出(实施计划 §4.6 步骤 1.6、§4.7 步骤 1.7
+ §2.5 留存规范)。

按 §2.5 留存规范导出"三件套"——原始数据、图表、溯源元数据:
  - cost_ledger_<时间戳>.csv   —— 成本台账(原始数据,UTF-8-BOM 便于 Excel)
  - cost_ledger_<时间戳>.json  —— 成本台账(结构化)
  - sweep_<时间戳>.csv / .json —— 扫参结果(步骤 1.7,含逐 trial 原始量)
  - figures/figure*.png/.pdf   —— 图 1/2 实测版(步骤 1.7,figures.py 产出)
  - manifest_<时间戳>.json     —— 溯源元数据(配置、种子、性质、回填对应)
  - 留存清单.md                —— 汇总索引(每次运行追加,不覆盖)
"""
from __future__ import annotations
import csv
import json
from datetime import datetime
from pathlib import Path

from .ledger import DATA_KIND


def export_ledger(ledger, configs: dict, out_dir: str = "data"):
    """把成本台账与溯源元数据写入 out_dir。返回产出文件路径列表。"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    csv_path = out / f"cost_ledger_{ts}.csv"
    json_path = out / f"cost_ledger_{ts}.json"
    manifest_path = out / f"manifest_{ts}.json"

    # --- 成本台账 CSV(utf-8-sig:Excel 正确识别中文) ---
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        for row in ledger.to_csv_rows():
            writer.writerow(row)

    # --- 成本台账 JSON ---
    json_path.write_text(
        json.dumps({"label": ledger.label, "columns": ledger.COLUMNS,
                    "rows": ledger.rows}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    # --- 溯源元数据 manifest(§2.5) ---
    manifest = {
        "生成时间": ts,
        "生成脚本": "run_measure.py",
        "仿真器": "stage6_simulation(实施计划阶段一)",
        "数据性质": DATA_KIND,
        "随机种子与配置": configs,
        "回填对应": "实施计划 §2.4 映射表;成本台账每行 paper_ref 列标注具体落点",
        "产出文件": {
            "成本台账_CSV": csv_path.name,
            "成本台账_JSON": json_path.name,
        },
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- 留存清单(汇总索引,追加不覆盖) ---
    _append_inventory(out, ts, ledger.label,
                      [csv_path.name, json_path.name, manifest_path.name])

    return [csv_path, json_path, manifest_path]


def export_sweep(points, base_config: dict,
                 figure_files: list, out_dir: str = "data"):
    """把步骤 1.7 的扫参结果与溯源元数据写入 out_dir。

    points      —— sigma 扫参的 SweepPoint 列表(图 1、图 2 共用数据源);
    base_config —— 共享基线配置(SimConfig.as_dict());
    figure_files —— 已产出的图表文件路径列表(供 manifest 与清单记录)。

    返回产出的数据文件路径列表(不含图表 —— 图表由 figures.py 直接落地,
    此处仅在 manifest / 留存清单中登记)。
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    csv_path = out / f"sweep_{ts}.csv"
    json_path = out / f"sweep_{ts}.json"
    manifest_path = out / f"manifest_sweep_{ts}.json"

    rows = [p.as_row() for p in points]
    columns = list(rows[0].keys()) if rows else []

    # --- 扫参结果 CSV(utf-8-sig 便于 Excel 识别中文) ---
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(["# 步骤 1.7 sigma 扫参结果(图 1/2 实测版数据源)"])
        writer.writerow(columns)
        for r in rows:
            writer.writerow([r[c] for c in columns])

    # --- 扫参结果 JSON(含逐 trial 原始量,便于复算) ---
    def _full(p):
        d = p.as_row()
        d["trials"] = p.trials
        return d

    json_path.write_text(
        json.dumps({
            "label": "DAG-BFT sigma 扫参结果(图 1/2 实测版数据源)",
            "columns": columns,
            "sweep": [_full(p) for p in points],
        }, ensure_ascii=False, indent=2),
        encoding="utf-8")

    # --- 溯源元数据 manifest(§2.5) ---
    manifest = {
        "生成时间": ts,
        "生成脚本": "run_sweep.py",
        "仿真器": "stage6_simulation(实施计划阶段一 步骤 1.7)",
        "数据性质": DATA_KIND,
        "共享基线配置": base_config,
        "扫参自变量": "延迟分布 sigma(对数正态尺度/离散度,固定 mean,"
                       "单调驱动 ρ;ρ 与 Δ_recover 在本模型中天然耦合);"
                       "建模论文 §7.4–§7.5 网络退化",
        "实测量": "ρ、Δ_recover、Δ_save、净优势 —— 均来自运行测量,非假定",
        "回填对应": "实施计划 §2.4 映射表 'Figure 1/2 实测版' 行;"
                     "论文 §7.2 图 1、§7.6 图 2",
        "产出文件": {
            "扫参结果_CSV": csv_path.name,
            "扫参结果_JSON": json_path.name,
            "图表": [Path(f).name for f in figure_files],
        },
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- 留存清单(汇总索引,追加不覆盖) ---
    listed = [csv_path.name, json_path.name, manifest_path.name] + \
             [Path(f).name for f in figure_files]
    _append_inventory(out, ts, "步骤 1.7 扫参与出图(图 1/2 实测版)", listed)

    return [csv_path, json_path, manifest_path]


def export_verification(report: dict, base_config: dict,
                        out_dir: str = "data"):
    """把步骤 1.8 验证与回归报告写入 out_dir(§2.5 留存规范)。

    report —— run_verify.py 构建的报告字典,含 checks(逐项检查)、
              coupling_sweep(耦合扫参原始数据)、all_passed。
    base_config —— 共享基线配置(SimConfig.as_dict())。

    写出 verification_<ts>.json(结构化)与 .md(人读),并追加留存清单。
    返回产出文件路径列表。
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = out / f"verification_{ts}.json"
    md_path = out / f"verification_{ts}.md"

    # --- 结构化 JSON ---
    json_path.write_text(
        json.dumps({
            "生成时间": ts,
            "生成脚本": "run_verify.py",
            "仿真器": "stage6_simulation(实施计划阶段一 步骤 1.8)",
            "数据性质": DATA_KIND,
            "共享基线配置": base_config,
            "report": report,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8")

    # --- 人读 Markdown ---
    lines = [f"# 步骤 1.8 验证与回归报告 — {ts}", "",
             f"- 生成脚本:`run_verify.py`",
             f"- 数据性质:{DATA_KIND}",
             f"- 总判定:**{'全部通过 ✓' if report.get('all_passed') else '未通过 ✗'}**",
             "", "## 逐项检查", ""]
    for c in report.get("checks", []):
        mark = "✓ 通过" if c["passed"] else "✗ 失败"
        lines += [f"### {c['name']} — {mark}",
                  f"- 判据:{c['criterion']}",
                  f"- 实测:{c['observed']}",
                  f"- 论文锚点:{c.get('paper_ref', '—')}", ""]
    sweep = report.get("coupling_sweep", [])
    if sweep:
        lines += ["## 耦合检验扫参原始数据", "",
                  "| recovery_load | ρ | Δ_recover | Δ_save | 净优势 | tx 排队等待 |",
                  "|---|---|---|---|---|---|"]
        for r in sweep:
            lines.append(
                f"| {r['recovery_load']} | {r['rho']:.4f} | "
                f"{r['delta_recover']:.3f} | {r['delta_save']:.3f} | "
                f"{r['net_adv']:.3f} | {r['tx_queue_wait_mean']:.3f} |")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    _append_inventory(out, ts, "步骤 1.8 验证与回归报告",
                      [json_path.name, md_path.name])
    return [json_path, md_path]


def _append_inventory(out: Path, ts: str, label: str, files: list) -> None:
    """在 留存清单.md 追加一条记录(§2.5:即时留存、不覆盖)。"""
    inv = out / "留存清单.md"
    line = (f"- **{ts}** — {label}\n"
            f"  - 文件:{', '.join(files)}\n"
            f"  - 性质:{DATA_KIND}\n")
    if inv.exists():
        content = inv.read_text(encoding="utf-8") + line
    else:
        header = (
            "# stage6_simulation 数据留存清单\n\n"
            "按实施计划 §2.5 留存规范。每次测量运行(`run_measure.py`)"
            "追加一条,旧记录不覆盖。\n\n"
            "回填论文时凭此清单溯源;每个成本台账文件每行的 `paper_ref` 列"
            "对应 §2.4 映射表的具体落点。\n\n"
            "## 记录\n\n")
        content = header + line
    inv.write_text(content, encoding="utf-8")
