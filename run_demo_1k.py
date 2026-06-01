"""Hardened incremental runner for the demo exhibit.

Reuses the existing engine (_run_prompt) + the 14 canonical prompts, but with
orchestration the CLI lacks:
  - breadth-first to a 30/prompt FLOOR, snapshotted the instant it's reached
    (this is the defensible-floor artifact — the thing that matters)
  - then continues each prompt toward 1000 (bonus depth)
  - EVERY result appended to runs.jsonl as it lands -> a crash loses nothing
  - light retry on failure so rate-limit blips don't decimate the run
  - clean, flushed progress to progress.txt (readable while running)

Run:  ANTHROPIC_API_KEY=... .venv/bin/python run_demo_1k.py
"""
import sys, asyncio, json, time
sys.path.insert(0, "src")
from pathlib import Path

from workflow_analyzer.runner import WorkflowAnalyzer, RunConfig
from workflow_analyzer.prompts import ALL_PROMPTS
from workflow_analyzer import corpus as corpus_mod

WF = Path("examples/feature-deploy/workflow.txt").read_text()
OUT = Path("demo-output/n1000"); OUT.mkdir(parents=True, exist_ok=True)
JSONL = OUT / "runs.jsonl"
PROG = OUT / "progress.txt"

CONC = 20
FLOOR = 30
TARGET = 1000
RETRIES = 2        # per-analysis retry on failure (rate-limit resilience)

cfg = RunConfig(workflow_data=WF, runs_per_prompt=TARGET, adaptive_stopping=False)
analyzer = WorkflowAnalyzer()

results = {p.id: [] for p in ALL_PROMPTS}   # prompt_id -> list[PromptRunResult]
counts = {p.id: 0 for p in ALL_PROMPTS}
state = {"done": 0, "fail": 0, "spent": 0.0, "floor_done": False, "start": time.time()}
jsonl_lock = asyncio.Lock()

# fresh run -> clear the JSONL
JSONL.write_text("")


def write_progress(msg=""):
    el = time.time() - state["start"]
    minc = min(counts.values()) if counts else 0
    line = (f"[{el/60:5.1f}m] done={state['done']} fail={state['fail']} "
            f"spent=${state['spent']:.2f} min/prompt={minc} "
            f"floor={'YES' if state['floor_done'] else 'no'} {msg}")
    PROG.write_text(line + "\n")
    print(line, flush=True)


async def one(prompt, run_num):
    """Run a single analysis with retry; persist + account for it."""
    for attempt in range(RETRIES + 1):
        r = await analyzer._run_prompt(prompt, run_num, cfg)
        state["spent"] += ((r.input_tokens) * 1.0 + (r.output_tokens) * 5.0) / 1e6
        if r.extraction_success:
            break
        if attempt < RETRIES:
            await asyncio.sleep(2 * (attempt + 1))  # backoff before retry
    async with jsonl_lock:
        with open(JSONL, "a") as f:
            f.write(json.dumps({
                "prompt_id": r.prompt_id, "run": run_num,
                "ok": r.extraction_success, "metrics": r.extracted_metrics,
                "in": r.input_tokens, "out": r.output_tokens,
            }) + "\n")
    results[prompt.id].append(r)
    counts[prompt.id] += 1
    state["done"] += 1
    if not r.extraction_success:
        state["fail"] += 1
    if state["done"] % 20 == 0:
        write_progress()
    return r


def all_results_flat():
    return [r for lst in results.values() for r in lst]


def snapshot(tag):
    flat = all_results_flat()
    csv_p, json_p = corpus_mod.export(flat, OUT, f"feature-deploy-{tag}")
    # corpus.export writes corpus.csv/json; copy to tagged names so they're not overwritten
    (OUT / f"corpus_{tag}.csv").write_text(Path(csv_p).read_text())
    (OUT / f"corpus_{tag}.json").write_text(Path(json_p).read_text())
    write_progress(f"-> snapshot corpus_{tag}.csv ({len(corpus_mod.build_rows(flat))} metrics)")


async def run_phase(target_per_prompt, sem):
    """Bring every prompt up to target_per_prompt, breadth-first, bounded concurrency."""
    async def bounded(p, rn):
        async with sem:
            await one(p, rn)
    tasks = []
    for rn in range(1, target_per_prompt + 1):       # round-robin by run number = breadth-first
        for p in ALL_PROMPTS:
            if counts[p.id] < rn:
                tasks.append(bounded(p, rn))
    await asyncio.gather(*tasks, return_exceptions=True)


async def main():
    sem = asyncio.Semaphore(CONC)
    write_progress("START")

    # PHASE 1 — the floor (what matters). Snapshot the instant it's complete.
    await run_phase(FLOOR, sem)
    state["floor_done"] = True
    snapshot("floor30")
    write_progress("FLOOR BANKED — corpus_floor30.csv is the defensible artifact")

    # PHASE 2 — bonus depth toward 1000. Periodic snapshots so a late crash still yields a big-N corpus.
    last_snap = state["done"]
    async def bounded(p, rn):
        async with sem:
            await one(p, rn)
            if state["done"] - last_snap >= 1000:
                pass  # snapshots handled below in chunks
    # continue each prompt FLOOR -> TARGET
    tasks = []
    for rn in range(FLOOR + 1, TARGET + 1):
        for p in ALL_PROMPTS:
            tasks.append(bounded(p, rn))
    # run in chunks so we can snapshot periodically
    CHUNK = 2000
    for i in range(0, len(tasks), CHUNK):
        await asyncio.gather(*tasks[i:i + CHUNK], return_exceptions=True)
        snapshot("full")
    snapshot("full")
    write_progress("FULL RUN COMPLETE")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted — writing final snapshot from what completed...", flush=True)
        snapshot("interrupted")
        write_progress("INTERRUPTED — snapshot written")
