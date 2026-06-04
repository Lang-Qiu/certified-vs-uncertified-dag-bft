#!/usr/bin/env python
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


NUMERIC_FIELDS = [
    "rpc_latency_ms_p50",
    "rpc_latency_ms_p95",
    "checkpoint_count",
    "checkpoint_interval_ms_p50",
    "checkpoint_interval_ms_p95",
    "recovery_time_ms",
    "availability_ratio",
]


def _read_json(path):
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _nearest_rank(values, percentile):
    """Nearest-rank percentile (C=1): rank = ceil(p * n), return sorted[rank-1].

    For median on even n this returns the lower of the two middle values
    (e.g. n=10 -> sorted[4]), NOT the average sorted[4]+sorted[5])/2 used by
    R median() and numpy default linear interpolation. The aggregate summary
    written by this script (formal_matrix_summary_*.{json,csv}) follows this
    convention; downstream comparators using different median definitions
    will see off-by-one-rank differences on even sample sizes.
    """
    values = sorted(value for value in values if isinstance(value, (int, float)))
    if not values:
        return None
    rank = int((percentile / 100) * len(values) + 0.999999999)
    rank = min(max(rank, 1), len(values))
    return values[rank - 1]


def _iqr(values):
    q1 = _nearest_rank(values, 25)
    q3 = _nearest_rank(values, 75)
    if q1 is None or q3 is None:
        return None
    return q3 - q1


def summarize_metrics(metrics):
    grouped = defaultdict(list)
    for metric in metrics:
        scenario = metric.get("scenario") or "unknown"
        grouped[scenario].append(metric)

    rows = []
    for scenario, items in sorted(grouped.items()):
        row = {
            "scenario": scenario,
            "n": len(items),
            "failed_runs": sum(1 for item in items if item.get("failed_transactions", 0)),
            "null_fields": {},
            "unsupported_fields": {},
        }
        for field in NUMERIC_FIELDS:
            values = [item.get(field) for item in items]
            numeric = [value for value in values if isinstance(value, (int, float))]
            row[f"{field}_median"] = _nearest_rank(numeric, 50)
            row[f"{field}_p95"] = _nearest_rank(numeric, 95)
            row[f"{field}_iqr"] = _iqr(numeric)
            row[f"{field}_min"] = min(numeric) if numeric else None
            row[f"{field}_max"] = max(numeric) if numeric else None
            null_count = sum(1 for value in values if value is None)
            if null_count:
                row["null_fields"][field] = null_count

        unsupported = set()
        for item in items:
            fields = item.get("unsupported_fields", {})
            if isinstance(fields, dict):
                unsupported.update(fields)
        row["unsupported_fields"] = sorted(unsupported)
        rows.append(row)
    return rows


def load_metrics(paths):
    return [_read_json(path) for path in paths]


def write_json(rows, path):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(rows, path):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            encoded = dict(row)
            for key in ("null_fields", "unsupported_fields"):
                encoded[key] = json.dumps(encoded.get(key), ensure_ascii=False, sort_keys=True)
            writer.writerow(encoded)


def write_report(rows, path):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# N=7/f=2 多验证者实验发现",
        "",
        "## 实验设置",
        "本报告只汇总已登记的多验证者运行指标；未完成的场景不会被描述为实验结论。",
        "",
        "## 原始证据与可复现性",
        "每条结论应追溯到 run manifest、metrics JSON 和原始 evidence 文件。",
        "",
        "## 场景汇总",
    ]
    for row in rows:
        lines.append(f"- {row['scenario']}: n={row['n']}, failed_runs={row['failed_runs']}, null_fields={json.dumps(row['null_fields'], ensure_ascii=False, sort_keys=True)}")
    lines.extend(
        [
            "",
            "## Stage 6 校准影响",
            "见 `calibration_report.md` 和 `stage6_calibration_patch.json`。",
            "",
            "## 有效性威胁",
            "单机 Docker、资源竞争、容器网络、样本量和工作负载代表性必须在论文中保留边界说明。",
            "",
            "## 可进入论文的结论",
            "仅限有原始证据和 manifest 哈希支持的真实部署观察。",
            "",
            "## 不能进入论文的结论",
            "不能把计划事件、swarm 预校准或缺失字段推断成真实交易成功、最终性或共识延迟。",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Summarize Stage 7 multivalidator metrics.")
    parser.add_argument("--metrics", nargs="+", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--report", required=True)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    rows = summarize_metrics(load_metrics(args.metrics))
    write_json(rows, args.output_json)
    write_csv(rows, args.output_csv)
    write_report(rows, args.report)
    print(f"wrote summaries for {len(rows)} scenarios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
