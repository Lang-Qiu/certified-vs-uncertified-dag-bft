from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def first_present(data: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return None


def summarize_stage6_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    output_files = first_present(manifest, ["产出文件", "output_files", "outputs"])
    entries = manifest.get("entries")
    return {
        "top_level_keys": list(manifest.keys()),
        "generated_at_or_stamp": first_present(
            manifest, ["生成时间", "generated_at", "timestamp"]
        ),
        "generated_by": first_present(manifest, ["生成脚本", "generated_by", "script"]),
        "data_nature": first_present(manifest, ["数据性质", "data_nature", "source"]),
        "simulator": first_present(manifest, ["仿真器", "simulator"]),
        "baseline_config": first_present(
            manifest, ["共享基线配置", "随机种子与配置", "baseline_config", "config"]
        ),
        "sweep_variable": first_present(
            manifest, ["扫参自变量", "sweep_variable", "independent_variable"]
        ),
        "measures": first_present(manifest, ["实测量", "measures", "metrics"]),
        "paper_mapping": first_present(
            manifest, ["回填对应", "paper_mapping", "paper_map"]
        ),
        "output_files": output_files,
        "entries_count": len(entries) if isinstance(entries, list) else None,
        "manifest_shape": "entries-list" if isinstance(entries, list) else "metadata-object",
    }


def build_calibration(
    stage2_summary_path: Path,
    stage6_manifest_path: Path,
    stage2_summary: dict[str, Any],
    stage6_manifest: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source": "stage1-stage2-calibration",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stage2_summary_path": str(stage2_summary_path),
        "stage6_manifest_path": str(stage6_manifest_path),
        "stage2": {
            "source": stage2_summary.get("source"),
            "event_count": stage2_summary.get("event_count"),
            "kind_counts": stage2_summary.get("kind_counts"),
            "observed_consensus_events": stage2_summary.get(
                "observed_consensus_events"
            ),
            "observed_checkpoint_events": stage2_summary.get(
                "observed_checkpoint_events"
            ),
            "observed_transaction_events": stage2_summary.get(
                "observed_transaction_events"
            ),
            "transaction_token_events": stage2_summary.get(
                "transaction_token_events"
            ),
            "transaction_token_counts": stage2_summary.get(
                "transaction_token_counts"
            ),
            "classification_warnings": stage2_summary.get(
                "classification_warnings"
            ),
            "latency_ms": stage2_summary.get("latency_ms"),
        },
        "stage6_manifest": summarize_stage6_manifest(stage6_manifest),
        "interpretation": [
            "Stage 2 currently provides real-protocol log coverage and baseline run evidence from a local Sui smoke deployment.",
            "The current Stage 2 evidence is useful for anchoring the data pipeline and checking observed consensus/checkpoint/transaction log surfaces.",
            "Precise latency calibration requires upstream timestamp or duration instrumentation before mean, median, or p95 latency can be computed.",
            "Stage 2 alone cannot claim certification-variable isolation; controlled isolation remains the responsibility of Stage 1/Stage 6 simulation evidence.",
            "The current Sui smoke run is a single-container local validator/fullnode/faucet path and must not be reported as a multi-validator consensus conclusion.",
        ],
        "limits": {
            "latency_calibration_ready": False,
            "reason": "stage2_summary.latency_ms.samples is empty because reliable per-event commit/checkpoint duration fields are not present.",
            "claim_boundary": "real-deployment baseline evidence only; not certification-variable isolation and not a multi-validator result.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare Stage 2 real-deployment evidence with Stage 6 simulation metadata."
    )
    parser.add_argument("--stage2-summary", required=True)
    parser.add_argument("--stage6-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    stage2_summary_path = Path(args.stage2_summary)
    stage6_manifest_path = Path(args.stage6_manifest)
    output_path = Path(args.output)

    stage2_summary = read_json(stage2_summary_path)
    stage6_manifest = read_json(stage6_manifest_path)
    calibration = build_calibration(
        stage2_summary_path,
        stage6_manifest_path,
        stage2_summary,
        stage6_manifest,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(calibration, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {output_path}")
    print(
        "stage2_events="
        f"{calibration['stage2']['event_count']} "
        f"stage6_manifest_shape={calibration['stage6_manifest']['manifest_shape']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
