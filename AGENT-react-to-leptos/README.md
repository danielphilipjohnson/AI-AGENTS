# React → Leptos Conversion Agent

A CLI tool that automatically converts React (TSX) components to Leptos Rust using Ollama LLM, with automatic compilation checking and LLM-powered error fixing (up to 3 attempts per component).

## Quick Start

### One-Shot Batch (Easiest)

```bash
cd AGENT-react-to-leptos

# Scan directory + convert + check + fix, all in one command
python3 cli.py batch /path/to/your/components --output ./leptos-output --max-tries 3
```

That's it! It will:
1. Find all `.tsx` files in the directory
2. Convert each to Leptos via Ollama
3. Run `cargo check` on each
4. If errors, use LLM to fix (up to 3 tries)
5. Save results to `./leptos-output/` + `batch_summary.json`

### With Manifest Tracking (Resume Support)

```bash
# Step 1: Scan and create manifest
python3 cli.py scan /path/to/components --output manifest.json

# Step 2: Run full agent loop (convert → check → fix → verify)
python3 cli.py run manifest.json --output ./leptos-output --max-tries 3

# Check the manifest for results
cat manifest.json
```

---

## All CLI Commands

| Command | Description | Example |
|---------|-------------|---------|
| `scan` | Find TSX files, create manifest | `python3 cli.py scan ./src --output manifest.json` |
| `batch` | Scan + full loop on directory | `python3 cli.py batch ./src --output ./out --max-tries 3` |
| `run` | Full loop on existing manifest | `python3 cli.py run manifest.json --output ./out` |
| `convert-manifest` | Convert only (no check/fix) | `python3 cli.py convert-manifest manifest.json --output ./out` |
| `check-compile` | Run cargo check on converted files | `python3 cli.py check-compile manifest.json` |
| `fix-compile` | LLM fix failed compilations | `python3 cli.py fix-compile manifest.json --max-tries 3` |
| `convert` | Convert single file | `python3 cli.py convert Button.tsx --output button.rs` |

### Help

```bash
python3 cli.py --help
python3 cli.py batch --help
python3 cli.py run --help
```

---

## Configuration

Edit `models.toml` to set your Ollama model:

```toml
[ollama]
url = "http://localhost:11434"

[ollama.models]
convert = "gpt-oss-20b-32k:latest"  # Model for conversion
fix = "gpt-oss-20b-32k:latest"      # Model for fixing

[ollama.settings]
temperature = 0.1
num_ctx = 8192
num_predict = 16384

[ollama.timeouts]
request_timeout = 600  # 10 minutes
```

Override with CLI flags:
```bash
python3 cli.py batch ./src --output ./out --model qwen2.5-coder:7b --temperature 0.2
```

---

## How It Works

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   scan      │────▶│   convert   │────▶│cargo check  │────▶│    fix      │
│  (find tsx) │     │  (via LLM)  │     │             │     │  (via LLM)  │
└─────────────┘     └─────────────┘     └──────┬──────┘     └──────┬──────┘
                                                  │                   │
                                           ✅ no errors          ❌ errors
                                                  │                   │
                                                  ▼                   │
                                            ┌─────────────┐           │
                                            │   passed    │◀──────────┘
                                            └─────────────┘
                                                  │
                                           (up to 3 tries)
                                                  ▼
                                            ┌─────────────┐
                                            │ failed/stalled│
                                            └─────────────┘
```

### The Loop (per component)

1. **Convert**: TSX → Leptos via Ollama
2. **Check**: Write to scratch crate, run `cargo check`
3. **If passed**: Done ✅
4. **If failed**: Send code + errors to LLM, get fixed code
5. **Repeat** up to `--max-tries` (default 3)
6. **Stall detection**: If fix returns identical code, stop early

---

## Output Structure

```
leptos-output/
├── batch_summary.json          # Overall results
├── packages/ui/src/layout/
│   ├── Container/container.rs  # Converted components
│   ├── Section/section.rs
│   └── ...

manifest.json                   # Per-file tracking (if using scan/run)
```

### manifest.json Format

```json
[
  {
    "source": "Container/Container.tsx",
    "absolute": "/full/path/to/Container.tsx",
    "status": "passed",           // pending|converted|compiled|failed|fixed|stalled|blocked
    "verdict": "passed",
    "tries_used": 2,
    "output": "packages/ui/src/layout/Container/container.rs",
    "model": "gpt-oss-20b-32k:latest",
    "attempts": [
      {"try": 1, "code": "...", "errors": [...], "error_count": 3},
      {"try": 2, "code": "...", "errors": [], "error_count": 0}
    ]
  }
]
```

---

## Project Structure

```
AGENT-react-to-leptos/
├── cli.py              # CLI entry point (all commands)
├── agent.py            # run_agent(), run_batch(), convert(), fix()
├── tools.py            # scan_tsx(), cargo check, file I/O
├── ollama_client.py    # Ollama API client (/v1 endpoint)
├── models.toml         # Ollama configuration
├── prompts/
│   ├── react_to_leptos.md   # Conversion prompt
│   └── fix_leptos.md        # Fix prompt
├── scratch_crate/      # Template Rust crate for cargo check
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs
│       └── component.rs     # Overwritten per check
├── README.md           # This file
└── todo.md             # Build plan
```

---

## Troubleshooting

### Timeout errors
Large models take time to load. Warm up first:
```bash
curl -X POST http://localhost:11434/api/chat \
  -d '{"model":"gpt-oss-20b-32k:latest","messages":[{"role":"user","content":"hi"}],"stream":false}'
```

### Model not found
```bash
ollama pull gpt-oss-20b-32k
# Or use a smaller model
python3 cli.py batch ./src --output ./out --model mistral:latest
```

### Check Ollama is running
```bash
curl http://localhost:11434/api/tags
```

---

## License

MIT
