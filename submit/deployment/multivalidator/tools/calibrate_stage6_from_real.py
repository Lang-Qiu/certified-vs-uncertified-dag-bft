#!/usr/bin/env python
import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


CALIBRATION_FIELDS = [
    "rpc_latency_ms_p50",
    "rpc_latency_ms_p95",
    "recovery_time_ms",
    "availability_ratio",
]


def _read_json(path):
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _median(values):
    """Median via nearest-rank percentile (C=1), matching summarize_runs.py.

    rank = ceil(0.5 * n); returns sorted[rank-1]. For even n this gives the
    lower of the two middle values (n=10 -> sorted[4]). Previously this
    function used sorted[n//2] (upper median), which produced calibration
    patches off by one rank from the formal summary on even sample sizes.
    """
    values = sorted(value for value in values if isinstance(value, (int, float)))
    if not values:
        return None
    rank = int(0.5 * len(values) + 0.999999999)
    rank = min(max(rank, 1), len(values))
    return values[rank - 1]


def build_calibration_patch(metrics):
    grouped = defaultdict(list)
    for metric in metrics:
        grouped[metric.get("scenario") or "unknown"].append(metric)

    parameters = []
    for scenario, items in sorted(grouped.items()):
        for field in CALIBRATION_FIELDS:
            values = [item.get(field) for item in items]
            measured = _median(values)
            confidence = "measured_distribution_p50_p95" if measured is not None else "missing_real_measurement"
            parameters.append(
                {
                    "parameter": f"{scenario}.{field}",
                    "before": None,
                    "after": measured,
                    "source": f"independent_containers.{scenario}.{field}",
                    "confidence": confidence,
                    "notes": (
                        "Derived from N=7 Docker experiment metrics."
                        if measured is not None
                        else "No supported real measurement was available; do not use this field for simulation claims."
                    ),
                }
            )
    return {
        "source": "stage7_multivalidator_real_calibration",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "parameters": parameters,
        "claim_boundary": "Patch records measured inputs for Stage 6 calibration; it is not itself a simulation result.",
    }


def write_patch(patch, path):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(patch, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(patch, path):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage 6 校准报告",
        "",
        "本报告区分真实测量参数与缺失参数。`confidence=missing_real_measurement` 的项目不能用于论文中的定量外推。",
        "",
        "| parameter | before | after | confidence | source |",
        "|---|---:|---:|---|---|",
    ]
    for item in patch["parameters"]:
        lines.append(
            f"| {item['parameter']} | {item['before']} | {item['after']} | {item['confidence']} | {item['source']} |"
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Build a Stage 6 calibration patch from real N=7 metrics.")
    parser.add_argument("--metrics", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    patch = build_calibration_patch([_read_json(path) for path in args.metrics])
    write_patch(patch, args.output)
    write_report(patch, args.report)
    print(f"wrote calibration patch with {len(patch['parameters'])} parameters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
