# React → Leptos Conversion Agent: Build Plan (STUB)

**Goal:** Batch pipeline that converts `.tsx` components to Leptos via Ollama, validates with `cargo check`, with up to 3 fix attempts per file.

---

## 1. Pipeline Overview

```
Scan TSX files → Convert via Ollama → Write to scratch crate → cargo check → Fix on errors (up to 3 attempts) → Record results
```

---

## 2. File Layout

```
AGENT-react-to-leptos/
├── todo.md                    # This file
├── models.toml               # Ollama model configs
├── prompts/
│   ├── react_to_leptos.md    # Conversion prompt
│   └── fix_leptos.md         # Fix prompt
├── agent.py                  # convert(), fix(), run_agent(), run_batch()
├── tools.py                  # filesystem + cargo utilities
├── scratch_crate/            # Template Leptos project
│   ├── Cargo.toml
│   └── src/
│       └── component.rs      # Overwritten per attempt
└── runs/
    └── run_<timestamp>/
        ├── manifest.json      # Source → output mapping + status
        ├── outputs/           # Final .rs files
        └── transcripts/       # Full attempt history per file
```

---

## 3. Core Components

### 3.1 Tools (tools.py)
- [x] `scan_tsx()` - Find .tsx files, exclude tests/stories/index
- [x] `read()` / `write_component()` - File I/O
- [x] `seed_scratch_crate()` - Copy template
- [x] `run_cargo_check()` - Run cargo check, return raw JSON
- [x] `parse_errors()` - Extract actionable errors from component.rs

**Gate:** ✅ Verify scratch crate compiles empty; verify error parsing on broken component.

### 3.2 LLM Functions (agent.py)
- [x] `load_model_config()` - Load from models.toml
- [x] `load_config()` - Load full TOML config
- [x] `chat()` - Ollama API wrapper (stubbed)
- [x] `convert()` - TSX → Leptos (first attempt, stubbed)
- [x] `fix()` - Iterative fix with error history (stubbed)
- [x] `run_agent()` - Single file loop (max 3 tries, stubbed)

**Gate:** ⏳ Hand-test on one leaf component, verify fix uses error history.

### 3.3 Batch Runner
- [ ] `run_batch()` - Process all files, track manifest (stubbed)
- [ ] Resume support (skip already-processed files)

**Gate:** ⏳ Run on 3 files, verify resume works on re-run.

---

## 4. Schemas

### manifest.json
```json
[{
  "source": "src/components/Button.tsx",
  "status": "done",
  "verdict": "passed|failed|stalled|blocked",
  "tries_used": 1,
  "output": "outputs/components/button.rs"
}]
```

### transcripts/<file>.json
Full `run_agent()` return: every attempt's code + errors.

---

## 5. Edge Cases

| Case | Handling |
|------|----------|
| Errors outside component.rs | `verdict: blocked`, no fix tries |
| Markdown fences in output | Strip before writing |
| Fix repeats code | `verdict: stalled`, stop early |
| Crash mid-batch | Manifest written after each file; resume on re-run |
| Non-component .tsx | Excluded by `scan_tsx()` |
| Cargo timeout | Counts as failed try |

---

## 6. Checkpoints

- [x] Scratch crate compiles empty
- [x] Error parsing works
- [x] CLI `scan` command works - pulls all TSX files from a folder
- [x] TOML config loading works (models from TOML without flags)
- [ ] `convert()` output is clean
- [ ] Single file `run_agent()` transcript reviewed
- [ ] 3-file batch + resume verified
- [ ] Notebook UI wraps `run_batch()`

---

## 7. Decisions Needed

- [ ] Path mapping strategy: `Button.tsx` → `outputs/components/button.rs` (snake_case) - confirm?
- [ ] Scratch crate: minimal Leptos skeleton - verify `cargo check` passes
- [ ] Scope: one component per file, leaf-first - confirm cross-file deps out of scope for v1?
- [ ] Model config: which Ollama model? Temperature? Context size?
- [ ] Prompt versions: v1 draft needed for react_to_leptos and fix_leptos
