#!/usr/bin/env python3
"""Auto A/B battery for ShopPilot policy experiments.

Runs full public-200 eval for each experiment env, ranks by TechnicalScore,
optionally applies the best config that beats the floor.

  PYTHONPATH=. python3 scripts/run_policy_battery.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLOOR = 0.907753  # current ship baseline
OUT = ROOT / "docs" / "policy_battery_results.json"
PY = sys.executable

# Baseline env (ship defaults) — always first.
BASE_ENV = {
    "SHOPPILOT_DENSE": "hash",
    "SHOPPILOT_PRECISION_TURNS": "2",
    "SHOPPILOT_OTHER_TWICE": "1",
    "SHOPPILOT_CATEGORY_TAIL": "1",
    "SHOPPILOT_EVIDENCE_RANK": "1",
    "SHOPPILOT_PRECISION_GAP": "0",
    "SHOPPILOT_FULL_MATCH": "0",
    "SHOPPILOT_SOFT_MISS": "0",
    "SHOPPILOT_OTHER_THRICE": "0",
    "SHOPPILOT_STOP_ASK_TURN": "9",
    "SHOPPILOT_SKIP_BRAND_ASK": "0",
    "SHOPPILOT_DISC_MULT": "1.0",
    "SHOPPILOT_TITLE_EXACT": "0",
    "SHOPPILOT_EXACT_COMBO": "0",
}

# Creative / innovative experiments (at least 5 + baseline).
EXPERIMENTS: list[tuple[str, dict[str, str]]] = [
    ("baseline", {}),
    # 1. Score-gap Top-1 (adaptive precision)
    ("gap3", {"SHOPPILOT_PRECISION_GAP": "3.0"}),
    ("gap5", {"SHOPPILOT_PRECISION_GAP": "5.0"}),
    ("gap8", {"SHOPPILOT_PRECISION_GAP": "8.0"}),
    # 2. Full-match jackpot
    ("fullmatch4", {"SHOPPILOT_FULL_MATCH": "4.0"}),
    ("fullmatch8", {"SHOPPILOT_FULL_MATCH": "8.0"}),
    # 3. Soft disclosed miss demote
    ("softmiss1", {"SHOPPILOT_SOFT_MISS": "1.0"}),
    ("softmiss2", {"SHOPPILOT_SOFT_MISS": "2.0"}),
    # 4. Third other when empty
    ("other3", {"SHOPPILOT_OTHER_THRICE": "1"}),
    # 5. Early stop-ask
    ("stopask7", {"SHOPPILOT_STOP_ASK_TURN": "7"}),
    # 6. Skip brand asks
    ("skipbrand", {"SHOPPILOT_SKIP_BRAND_ASK": "1"}),
    # 7. Combos of best-looking single levers
    ("gap5_full4", {"SHOPPILOT_PRECISION_GAP": "5.0", "SHOPPILOT_FULL_MATCH": "4.0"}),
    ("gap5_soft1", {"SHOPPILOT_PRECISION_GAP": "5.0", "SHOPPILOT_SOFT_MISS": "1.0"}),
    ("full4_soft1", {"SHOPPILOT_FULL_MATCH": "4.0", "SHOPPILOT_SOFT_MISS": "1.0"}),
    ("gap3_other3", {"SHOPPILOT_PRECISION_GAP": "3.0", "SHOPPILOT_OTHER_THRICE": "1"}),
    ("gap5_full4_soft1", {
        "SHOPPILOT_PRECISION_GAP": "5.0",
        "SHOPPILOT_FULL_MATCH": "4.0",
        "SHOPPILOT_SOFT_MISS": "1.0",
    }),
    # 8. Mild disc mult (failed at 2.0; retry 1.2)
    ("disc12", {"SHOPPILOT_DISC_MULT": "1.2"}),
    ("gap5_disc12", {"SHOPPILOT_PRECISION_GAP": "5.0", "SHOPPILOT_DISC_MULT": "1.2"}),
]


def run_one(name: str, overrides: dict[str, str]) -> dict:
    env = os.environ.copy()
    # clear LLM
    for k in list(env):
        if k.startswith("SHOPPILOT_LLM"):
            env.pop(k, None)
    env.update(BASE_ENV)
    env.update(overrides)
    # ensure no stale overrides from shell
    t0 = time.time()
    proc = subprocess.run(
        [PY, "-m", "evaluator.local_evaluator"],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )
    elapsed = time.time() - t0
    results_path = ROOT / "results.json"
    if proc.returncode != 0 or not results_path.exists():
        return {
            "name": name,
            "ok": False,
            "error": (proc.stderr or proc.stdout)[-500:],
            "elapsed_s": round(elapsed, 1),
            "env": overrides,
        }
    data = json.loads(results_path.read_text())
    row = {
        "name": name,
        "ok": True,
        "tech": data.get("recommended_technical_score"),
        "hit": data.get("hit_rate_at_10"),
        "mrr": data.get("mrr"),
        "mttc": data.get("mttc"),
        "efficiency": data.get("efficiency"),
        "elapsed_s": round(elapsed, 1),
        "env": overrides,
        "delta_vs_floor": round((data.get("recommended_technical_score") or 0) - FLOOR, 5),
        "beats_floor": (data.get("recommended_technical_score") or 0) + 1e-9 >= FLOOR,
    }
    # save per-run snapshot
    snap = ROOT / "docs" / "battery_runs" / f"{name}.json"
    snap.parent.mkdir(parents=True, exist_ok=True)
    snap.write_text(json.dumps(data, indent=2))
    return row


def main() -> int:
    print(f"FLOOR Tech={FLOOR}")
    print(f"Experiments: {len(EXPERIMENTS)}")
    rows: list[dict] = []
    for name, overrides in EXPERIMENTS:
        print(f"\n=== RUN {name} {overrides} ===", flush=True)
        row = run_one(name, overrides)
        rows.append(row)
        if row.get("ok"):
            print(
                f"  Tech={row['tech']:.6f} Hit={row['hit']} MRR={row['mrr']:.6f} "
                f"MTTC={row['mttc']:.3f} Δ={row['delta_vs_floor']:+.5f} "
                f"({'PASS' if row['beats_floor'] else 'FAIL'}) {row['elapsed_s']}s",
                flush=True,
            )
        else:
            print(f"  FAIL {row.get('error', '')[:200]}", flush=True)

    ok_rows = [r for r in rows if r.get("ok")]
    ok_rows.sort(key=lambda r: r["tech"], reverse=True)
    best = ok_rows[0] if ok_rows else None
    winners = [r for r in ok_rows if r["beats_floor"] and r["tech"] > FLOOR + 1e-6]

    report = {
        "floor": FLOOR,
        "n_experiments": len(rows),
        "ranked": ok_rows,
        "all": rows,
        "best": best,
        "winners_above_floor": winners,
    }
    OUT.write_text(json.dumps(report, indent=2))
    print("\n======== RANKED (ok only) ========")
    for i, r in enumerate(ok_rows, 1):
        mark = " *** BEST" if best and r["name"] == best["name"] else ""
        win = " WIN" if r in winners else ""
        print(
            f"{i:2d}. {r['name']:20s} Tech={r['tech']:.6f} Hit={r['hit']} "
            f"MRR={r['mrr']:.6f} MTTC={r['mttc']:.3f}{win}{mark}"
        )
    print(f"\nWrote {OUT}")
    if best:
        print(f"BEST: {best['name']} Tech={best['tech']}")
        if winners:
            print(f"Winners above floor: {[w['name'] for w in winners]}")
        else:
            print("No experiment beat the floor; keep baseline defaults.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
