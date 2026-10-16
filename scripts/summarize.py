#!/usr/bin/env python3
"""Recalculate means, ranges, sample counts, and relative changes from packaged measurements."""
from pathlib import Path
import json
import math
from statistics import mean
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "measurements"
def read(name): return json.loads((DATA / name).read_text(encoding="utf-8"))
def stats(values): return {"n":len(values),"mean":mean(values),"min":min(values),"max":max(values)}
def fmt(v): return f"{v:.6f}"

def same(actual, recorded):
 if not math.isclose(actual,recorded,rel_tol=1e-8,abs_tol=1e-5):
  raise ValueError(f"Inconsistent exported components: {actual} != {recorded}")

def validate_components(study):
 for s in study["samples"]:
  if study["id"]=="P2_matched_flags":
   same(s["server_user_cpu_ms"]+s["server_system_cpu_ms"],s["server_lifetime_cpu_ms"])
  elif study["id"]=="P3_precise_allowed_phases":
   same(sum(p["server_cpu_ms"] for p in s["allowed_phase_server_cpu"]),s["allowed_phase_server_cpu_ms"])
   same(s["server_lifetime_user_cpu_ms"]+s["server_lifetime_system_cpu_ms"],s["server_lifetime_cpu_ms"])
  elif study["id"]=="P5_four_mode_allowed_phases":
   for p in s["allowed_phase_cpu"]:
    same(p["core_cpu_ms"]+p["controller_cpu_ms"],p["core_plus_controller_cpu_ms"])
   same(sum(p["core_cpu_ms"]+p["controller_cpu_ms"] for p in s["allowed_phase_cpu"]),s["sum_allowed_phase_cpu_ms"])
   same(s["core_hwm_mib"]+s["controller_hwm_mib"],s["core_plus_controller_hwm_sum_mib"])
def main():
 doc=read("cpu-samples.json"); rows=[]
 specs={"P2_matched_flags":[("server_lifetime_cpu_ms","server_lifetime_cpu_ms","ms")],"P3_precise_allowed_phases":[("allowed_phase_server_cpu_ms","allowed_phase_server_cpu_ms","ms"),("server_lifetime_cpu_ms","server_lifetime_cpu_ms","ms")],"P5_four_mode_allowed_phases":[("sum_allowed_phase_cpu_ms","sum_allowed_phase_cpu_ms","ms"),("core_plus_controller_hwm_sum_mib","core_plus_controller_hwm_sum_mib","MiB")]}
 for study in doc["studies"]:
  validate_components(study)
  sid=study["id"]
  for field,label,unit in specs[sid]:
   grouped={m:stats([float(s[field]) for s in study["samples"] if s["mode"]==m]) for m in study["modes"]}; base=grouped.get("stock",{}).get("mean")
   for mode in study["modes"]:
    q=grouped[mode]; pct=None if mode=="stock" or not base else (q["mean"]/base-1)*100
    rows.append((sid,label,mode,q["n"],q["mean"],q["min"],q["max"],pct,unit))
 print("| Study | Metric | Mode | n | Mean | Min | Max | Change vs stock | Unit |")
 print("|---|---|---:|---:|---:|---:|---:|---:|---|")
 for sid,label,mode,n,avg,lo,hi,pct,unit in rows:
  change="baseline" if pct is None else f"{pct:+.3f}%"
  print(f"| {sid} | {label} | {mode} | {n} | {fmt(avg)} | {fmt(lo)} | {fmt(hi)} | {change} | {unit} |")
 lookup={(r[0],r[1],r[2]):r[4] for r in rows}
 print("\nAdditional contrasts within the same study and accounting scope:")
 for sid,metric,num,den in [
  ("P2_matched_flags","server_lifetime_cpu_ms","candidate_on","candidate_off"),
  ("P3_precise_allowed_phases","allowed_phase_server_cpu_ms","candidate_on","candidate_off"),
  ("P5_four_mode_allowed_phases","sum_allowed_phase_cpu_ms","lua_controller","native")]:
  a,b=lookup[(sid,metric,num)],lookup[(sid,metric,den)]
  print(f"{sid}: {num} vs {den}: {(a/b-1)*100:+.6f}%, difference {a-b:.6f} ms")
if __name__=="__main__": main()
