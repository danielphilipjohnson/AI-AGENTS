# React → Leptos Conversion Agent

A batch pipeline that automatically converts React (TSX) components to Leptos Rust components using Ollama LLM, with automatic error fixing via `cargo check`.

## Overview

This agent provides a complete pipeline for converting React component libraries to Leptos. It:

1. **Scans** a directory for `.tsx` files
2. **Converts** each component to Leptos using Ollama
3. **Validates** with `cargo check`
4. **Fixes** compilation errors automatically (up to 3 attempts)
5. **Records** full transcripts for review and grading

---

## Quick Start

### Using the CLI (Recommended)

The easiest way to use the agent is through the CLI tool:

```bash
cd AGENT-react-to-leptos

# Step 1: Scan a folder and save the manifest
python3 cli.py scan /path/to/your/react/components --output manifest.json

# Step 2: Convert all files in batch TEST
python3 cli.py batch /path/to/your/react/components --output ./leptos-output

# Step 3: Or convert a single file
python3 cli.py convert /path/to/Button.tsx --output button.rs
```

See all CLI options:
```bash
python3 cli.py --help
python3 cli.py scan --help
python3 cli.py convert --help
python3 cli.py batch --help
```

### Using Python Directly

If you prefer to use Python directly:

```bash
cd AGENT-react-to-leptos
python3 -c "
from tools import scan_tsx
from pathlib import Path

# Point to your React components folder
target = Path('/path/to/your/react/components')
files = scan_tsx(target)

print(f'Found {len(files)} TSX files:')
for f in files[:10]:  # Show first 10
    print(f'  - {f}')
"
```

This will recursively find all `.tsx` files, excluding:
- Test files (`*.test.tsx`)
- Story files (`*.stories.tsx`)
- Index/barrel files (`index.tsx`)
- Type declarations (`*.d.ts`)

Files are sorted **leaf-first** (deepest directories first) to ensure dependencies are processed after the components that use them.

### Step 2: Configure Ollama

Edit `models.toml` to set your Ollama endpoint and model preferences:

```toml
[ollama]
url = "http://localhost:11434"

[ollama.models]
convert = "llava:13b"    # Model for TSX → Leptos conversion
fix = "llava:13b"        # Model for fixing Rust errors

[ollama.settings]
temperature = 0.1
num_ctx = 8192
```

### Step 3: Run a Single File Conversion

```python
from agent import run_agent
from tools import read
from pathlib import Path

# Read a React component
react_code = read(Path('/path/to/Button.tsx'))

# Run the conversion agent
result = run_agent(react_code, max_tries=3)

print(f"Verdict: {result['verdict']}")
print(f"Tries used: {result['tries_used']}")
print(f"Final code:\n{result['final_code']}")
```

Possible verdicts:
- `passed` - Converted and compiles cleanly
- `failed` - Exhausted all attempts, still has errors
- `stalled` - Fix attempts stopped making progress
- `blocked` - Errors outside `component.rs` (missing dependencies)

### Step 4: Run Batch Conversion

```python
from agent import run_batch, ModelConfig
from pathlib import Path

# Configure
target = Path('/path/to/react/components')
output = Path('./outputs')
max_tries = 3

# Run batch (with optional file limit for testing)
summary = run_batch(
    target=target,
    output=output,
    max_tries=max_tries,
    file_limit=10,  # Process only 10 files for testing
)

print(f"Completed: {summary['files_processed']}")
print(f"Passed: {summary['passed']}")
print(f"Failed: {summary['failed']}")
print(f"Stalled: {summary['stalled']}")
print(f"Blocked: {summary['blocked']}")
```

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React → Leptos Agent                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐     ┌──────────┐     ┌──────────────────────────┐ │
│  │  scan    │────▶│ convert  │────▶│    cargo check + fix      │ │
│  │  tsx     │     │  via     │     │    (up to 3 attempts)     │ │
│  │  files   │     │ Ollama   │     │                          │ │
│  └──────────┘     └──────────┘     └─────────────┬─────────────┘ │
│                                                   │              │
│                                                   ▼              │
│                                         ┌─────────────────┐        │
│                                         │  Write to      │        │
│                                         │  outputs/      │        │
│                                         └─────────────────┘        │
│                                         ┌─────────────────┐        │
│                                         │  Save          │        │
│                                         │  transcripts/  │        │
│                                         └─────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### File Structure

```
AGENT-react-to-leptos/
├── todo.md                    # Build plan and progress
├── README.md                  # This file
├── .gitignore
├── models.toml               # Ollama configuration
├── prompts/
│   ├── react_to_leptos.md    # TSX → Leptos conversion prompt
│   └── fix_leptos.md         # Error fixing prompt
├── agent.py                  # Core conversion logic
│   ├── chat()                 # Ollama API wrapper
│   ├── convert()              # Single conversion attempt
│   ├── fix()                  # Fix compilation errors
│   ├── run_agent()            # Full loop for one file
│   └── run_batch()            # Batch processing
├── tools.py                  # Utility functions
│   ├── scan_tsx()             # Find TSX files
│   ├── read()/write()         # File I/O
│   ├── seed_scratch_crate()   # Create temp crate
│   ├── run_cargo_check()     # Run cargo check
│   └── parse_errors()         # Extract actionable errors
└── scratch_crate/            # Template Leptos project
    ├── Cargo.toml
    └── src/
        ├── lib.rs            # Module declaration (static)
        └── component.rs      # Overwritten per attempt
```

### The Conversion Loop (Single File)

```
1. Read React TSX source
   ↓
2. Call convert() → First Leptos attempt via Ollama
   ↓
3. Write to scratch_crate/src/component.rs
   ↓
4. Run cargo check --message-format=json
   ↓
5. Parse errors from component.rs only
   ↓
   ┌─────────────────────────────────┐
   │ No errors?                      │
   │ ↓                               │
   │ RETURN: verdict=passed          │
   └─────────────────────────────────┘
   
   ┌─────────────────────────────────┐
   │ Errors found?                   │
   │ ↓                               │
   │ Attempts < 3?                   │
   │ ↓                               │
   │ Call fix() with code + errors   │
   │ ↓                               │
   │ Loop back to step 3             │
   └─────────────────────────────────┘
   
   ┌─────────────────────────────────┐
   │ Attempts exhausted?             │
   │ ↓                               │
   │ RETURN: verdict=failed          │
   └─────────────────────────────────┘
   
   ┌─────────────────────────────────┐
   │ Code unchanged from             │
   │ previous attempt?                │
   │ ↓                               │
   │ RETURN: verdict=stalled         │
   └─────────────────────────────────┘
   
   ┌─────────────────────────────────┐
   │ Errors outside component.rs?    │
   │ (missing dependencies)           │
   │ ↓                               │
   │ RETURN: verdict=blocked        │
   └─────────────────────────────────┘
```

---

## CLI Reference

The CLI provides three main commands:

### scan - Find TSX files

```bash
# Basic scan
python3 cli.py scan /path/to/components

# Save manifest to file
python3 cli.py scan /path/to/components --output manifest.json

# Limit number of files
python3 cli.py scan /path/to/components --limit 10

# Exclude patterns
python3 cli.py scan /path/to/components --exclude .test.tsx .stories.tsx
```

**Output:** JSON manifest with file list and metadata

### convert - Convert single file

```bash
# Basic conversion
python3 cli.py convert Button.tsx --output button.rs

# With custom model
python3 cli.py convert Button.tsx --output button.rs --model codellama:13b

# Custom temperature
python3 cli.py convert Button.tsx --output button.rs --temperature 0.3

# More fix attempts
python3 cli.py convert Button.tsx --output button.rs --max-tries 5

# Save transcript
python3 cli.py convert Button.tsx --output button.rs --transcript transcript.json
```

**Output:** Converted Rust file + optional transcript JSON

### batch - Convert all files

```bash
# Convert all TSX files in a directory
python3 cli.py batch /path/to/components --output ./leptos-output

# With file limit (test mode)
python3 cli.py batch /path/to/components --output ./leptos-output --limit 5

# Custom model and settings
python3 cli.py batch /path/to/components --output ./leptos-output \
  --model codellama:13b \
  --temperature 0.1 \
  --max-tries 3
```

**Output:** Directory of Rust files + run artifacts in `runs/`

---

## Output Structure

After running a batch, you get:

```
outputs/                              # Converted Rust files
├── components/                        # Mirrors source structure
│   ├── button.rs                      # From Button.tsx
│   ├── card.rs                        # From Card.tsx
│   └── ...
└── ...

runs/run_<timestamp>/                 # Run artifacts
├── manifest.json                     # Summary of all files
│   [
│     {
│       "source": "src/components/Button.tsx",
│       "status": "done",
│       "verdict": "passed",
│       "tries_used": 2,
│       "output": "outputs/components/button.rs"
│     },
│     ...
│   ]
├── outputs/                          # Final .rs files (same as above)
└── transcripts/                      # Full attempt history
    ├── button.json                   # Every attempt for Button.tsx
    ├── card.json                     # Every attempt for Card.tsx
    └── ...
```

Each transcript file contains:
```json
{
  "verdict": "passed",
  "tries_used": 2,
  "attempts": [
    {
      "try": 1,
      "code": "...first leptos attempt...",
      "errors": [...],
      "error_count": 3
    },
    {
      "try": 2,
      "code": "...fixed leptos code...",
      "errors": [],
      "error_count": 0
    }
  ],
  "final_code": "..."
}
```

---

## Configuration

### models.toml

```toml
[ollama]
url = "http://localhost:11434"      # Your Ollama endpoint

[ollama.models]
convert = "llava:13b"                # Model for conversion
fix = "codellama:13b"                # Model for fixing (can be different)

[ollama.settings]
temperature = 0.1                    # Low for deterministic output
num_ctx = 8192                       # Context window size
num_predict = 4096                   # Max tokens to generate

[ollama.timeouts]
request_timeout = 120                # Seconds to wait for response
```

### Prompts

The prompts in `prompts/` directory are Markdown files with placeholders:

**react_to_leptos.md:**
- `{react_code}` - Replaced with the React component source

**fix_leptos.md:**
- `{current_code}` - Current Leptos code with errors
- `{error_history}` - All previous errors
- `{attempt_number}` - Current attempt (1, 2, 3)
- `{max_attempts}` - Maximum attempts (3)

---

## Path Mapping

The agent preserves your source directory structure in the output:

```
Input:  src/components/Button.tsx
Output: outputs/components/button.rs

Input:  src/components/card/PriceCard.tsx
Output: outputs/components/card/price_card.rs
```

**Rules:**
- PascalCase component names → snake_case Rust module names
- Directory structure is preserved
- `.tsx` extension → `.rs` extension

---

## Edge Cases Handled

| Scenario | Behavior |
|----------|----------|
| Errors in dependencies (not component.rs) | `verdict: blocked`, no fix attempts wasted |
| Markdown code fences in LLM output | Stripped before writing |
| Fix produces identical code | `verdict: stalled`, stops early |
| Crash mid-batch | Manifest saved after each file; resume on re-run |
| Non-component files (tests, stories) | Excluded by `scan_tsx()` |
| Cargo timeout | Counts as failed attempt |
| Output file exists | Overwritten (transcripts versioned by run dir) |

---

## Validating the Pipeline

Before running at scale, verify each checkpoint:

### ✅ Checkpoint 1: Scratch Crate Compiles
```bash
cd scratch_crate
cargo check
# Should finish with no errors
```

### ✅ Checkpoint 2: Error Parsing Works
```python
from tools import run_cargo_check, parse_errors
from pathlib import Path

# Write a broken component
Path('scratch_crate/src/component.rs').write_text('''
use leptos::*;
#[component]
pub fn Component() -> impl IntoView {
    view! { <broken> }
}
''')

raw = run_cargo_check(Path('scratch_crate'))
errors = parse_errors(raw)
# Should return list of errors from component.rs
```

### ✅ Checkpoint 3: Single File Conversion
```python
from agent import run_agent
from tools import read

code = read(Path('path/to/SimpleButton.tsx'))
result = run_agent(code)
# Review result['attempts'] manually
```

### ✅ Checkpoint 4: Batch with Resume
```python
from agent import run_batch

# First run with limit
summary1 = run_batch(target, output, file_limit=3)

# Second run with same limit - should skip already processed files
summary2 = run_batch(target, output, file_limit=3)
# summary2 should show 0 new files processed
```

---

## Customization

### Adding New Prompts

1. Create a new file in `prompts/` (e.g., `react_to_leptos_v2.md`)
2. Update `agent.py` to load it:
   ```python
   def convert(react_code: str, prompt_name: str = "react_to_leptos_v2") -> str:
       prompt_template = load_prompt(prompt_name)
       ...
   ```

### Changing Model Config

```python
from agent import ModelConfig, run_agent

# Custom config for a specific run
custom_config = ModelConfig(
    name="codellama:70b",
    temperature=0.0,
    num_ctx=16384
)

result = run_agent(react_code, model_config=custom_config)
```

### Custom File Filtering

```python
from tools import scan_tsx
from pathlib import Path

# Custom exclusions
exclude = [
    ".test.tsx",
    ".stories.tsx",
    "index.tsx",
    ".d.ts",
    "**/legacy/**",  # Exclude legacy directory
]

files = scan_tsx(Path('/path/to/components'), exclude=exclude)
```

---

## Project Structure Summary

```
AI-AGENTS/
└── AGENT-react-to-leptos/          # This project
    ├── README.md                   # This file
    ├── todo.md                    # Build plan
    ├── .gitignore
    ├── models.toml
    ├── prompts/
    │   ├── react_to_leptos.md
    │   └── fix_leptos.md
    ├── agent.py                   # Core logic
    ├── tools.py                   # Utilities
    └── scratch_crate/             # Template
        ├── Cargo.toml
        └── src/
            ├── lib.rs
            └── component.rs
```

---

## Troubleshooting

### Ollama Connection Issues

```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Check model is available
curl http://localhost:11434/api/tags | grep llava
```

### Cargo Check Problems

```bash
# Verify cargo is installed
cargo --version

# Check Leptos is available
cargo search leptos

# Manually test scratch crate
cd scratch_crate
cargo check
```

### Permission Issues

```bash
# Make sure files are readable
chmod -R u+rX AGENT-react-to-leptos/

# Ensure output directories exist
mkdir -p outputs runs
```

---

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `cargo check` and manual conversion tests
5. Submit a pull request
