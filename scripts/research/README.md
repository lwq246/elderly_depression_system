# Skill research pipeline

Automated web research for `screening-conversation` and `elderly-depression-detection` skills.

## Layout

| Path | Purpose |
|------|---------|
| `scripts/research/topics.json` | 30 research topics (one per round) |
| `scripts/research/run_research_round.py` | Runs one DuckDuckGo search round |
| `scripts/research/run_research_round.ps1` | Scheduler entry point |
| `research/rounds/round-NN.md` | Per-round search logs |
| `research/RESEARCH-SYNTHESIS.md` | Consolidated findings |
| `research/state.json` | Progress tracker |

## Manual run

```powershell
# One round (what the scheduler runs every 30 minutes)
C:/Python314/python.exe scripts/research/run_research_round.py

# Batch all remaining — only for catch-up, not normal schedule
C:/Python314/python.exe scripts/research/run_research_round.py --all

# Re-run after target reached
C:/Python314/python.exe scripts/research/run_research_round.py --force
```

**Intended workflow:** Windows Task Scheduler runs **one round every 30 minutes** until `completed_rounds` reaches 30 (~15 hours). Do not use `--all` for the scheduled job.

Requires: `pip install ddgs`

## Windows scheduled task

Task name: **CursorDepression-SkillResearch**  
Interval: every **30 minutes**  
Action: `powershell.exe -ExecutionPolicy Bypass -File scripts\research\run_research_round.ps1`

Register:

```powershell
schtasks /Create /TN "CursorDepression-SkillResearch" /TR "powershell.exe -ExecutionPolicy Bypass -File \"C:\Users\leewe\Documents\CursorDepression\scripts\research\run_research_round.ps1\"" /SC MINUTE /MO 30 /F
```

Unregister:

```powershell
schtasks /Delete /TN "CursorDepression-SkillResearch" /F
```

After 30 rounds, the script exits cleanly on each scheduler tick (no-op). Reset `research/state.json` `completed_rounds` to `0` or use `--force` to start a new cycle.
