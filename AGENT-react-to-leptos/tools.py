"""
Tools for the React -> Leptos Conversion Agent.

Filesystem and cargo utilities. Pure side effects, no LLM calls.
"""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional


def scan_tsx(folder: Path, exclude: list[str] = None) -> list[Path]:
    """
    Recursively scan a directory for .tsx files.
    
    Args:
        folder: Path to scan
        exclude: List of patterns to exclude (e.g., [".test.tsx", ".stories.tsx"])
        
    Returns:
        List of Path objects to .tsx files, sorted leaf-first
    """
    if exclude is None:
        exclude = [".test.tsx", ".stories.tsx", "index.tsx", ".d.ts"]
    
    tsx_files = list(folder.rglob("*.tsx"))
    
    # Filter out excluded patterns
    filtered = []
    for f in tsx_files:
        if any(f.name.endswith(excl) for excl in exclude):
            continue
        # Skip barrel files (index.tsx)
        if f.name == "index.tsx":
            continue
        filtered.append(f)
    
    # Sort leaf-first (files in deepest directories first)
    filtered.sort(key=lambda p: (len(p.parts) * -1, p.name))
    
    return filtered


def read(path: Path) -> str:
    """Read a file and return its contents."""
    return path.read_text(encoding="utf-8")


def write_component(crate_path: Path, code: str) -> None:
    """
    Write Leptos code to the scratch crate's component.rs.
    
    Args:
        crate_path: Path to the scratch crate root
        code: The Leptos Rust code to write
    """
    component_file = crate_path / "src" / "component.rs"
    component_file.parent.mkdir(parents=True, exist_ok=True)
    component_file.write_text(code, encoding="utf-8")


def seed_scratch_crate() -> Path:
    """
    Create a fresh copy of the scratch crate template.
    
    Returns:
        Path to the new scratch crate directory
    """
    # Get the template directory
    template_dir = Path(__file__).parent / "scratch_crate"
    
    # Create a temporary directory for this run
    import tempfile
    import time
    timestamp = int(time.time())
    run_dir = Path(__file__).parent / "runs" / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    crate_dir = run_dir / "crate"
    
    # Copy the template
    shutil.copytree(template_dir, crate_dir)
    
    return crate_dir


def run_cargo_check(crate_path: Path, timeout: int = 60) -> str:
    """
    Run `cargo check --message-format=json` on a crate.
    
    Args:
        crate_path: Path to the crate root
        timeout: Timeout in seconds
        
    Returns:
        Raw stdout + stderr as a single string
    """
    try:
        result = subprocess.run(
            ["cargo", "check", "--message-format=json"],
            cwd=crate_path,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "TIMEOUT: cargo check exceeded {timeout}s"
    except Exception as e:
        return f"ERROR: {str(e)}"


def parse_errors(raw: str) -> list[dict]:
    """
    Parse cargo check JSON output and extract actionable errors.
    
    Args:
        raw: Raw JSON output from cargo check
        
    Returns:
        List of error dictionaries with keys:
        - message: The error message
        - file: The file path
        - line: Line number
        - column: Column number
        - span_snippet: Code snippet with the error
        - help: Help message (if available)
        
    Only returns errors that point to component.rs (actionable by the fixer)
    """
    errors = []
    
    for line in raw.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        
        # Only process compiler messages
        if obj.get("reason") != "compiler-message":
            continue
        
        # The actual message is nested under obj['message']
        msg_data = obj.get("message", {})
        if not isinstance(msg_data, dict):
            continue
        
        # Check the diagnostic level
        level = msg_data.get("level")
        severity = msg_data.get("severity")
        
        # Skip non-errors (warnings, notes, help messages, etc.)
        # In cargo's JSON output, errors have level='error'
        if level != "error" and severity != "error":
            continue
        
        # Extract span information
        spans = msg_data.get("spans", [])
        if not spans:
            continue
        
        span = spans[0]  # Take the first span
        
        # Only keep errors in component.rs
        file_path = span.get("file_name", "")
        if "component.rs" not in file_path:
            continue
        
        # Get the code from the span's text snippets
        span_text_parts = span.get("text", [])
        span_snippet = ""
        if span_text_parts:
            span_snippet = span_text_parts[0].get("text", "")
        
        error_dict = {
            "message": msg_data.get("message", ""),
            "file": file_path,
            "line": span.get("line_start"),
            "column": span.get("column_start"),
            "span_snippet": span_snippet,
            "help": msg_data.get("help", ""),
        }
        errors.append(error_dict)
    
    return errors


def to_snake_case(name: str) -> str:
    """Convert PascalCase or camelCase to snake_case."""
    snake = ""
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            snake += "_"
        snake += char.lower()
    return snake


def map_output_path(output_root: Path, source_path: Path) -> Path:
    """
    Map a source .tsx file path to an output .rs file path.
    
    Args:
        output_root: Root directory for output files
        source_path: Path to the source .tsx file
        
    Returns:
        Path to the output .rs file
        
    Example:
        source: /path/to/src/components/Button.tsx
        output: outputs/components/button.rs
    """
    # Convert filename to snake_case
    snake_filename = to_snake_case(source_path.stem) + ".rs"
    
    # Get the relative path from source to preserve directory structure
    # If source has a parent directory, use it
    if source_path.parent != source_path:
        # Get the relative path from the source's parent
        # Remove the .tsx extension
        relative = source_path.with_suffix("")
        # Get just the path parts after the root
        # For simplicity, just use the last few directory levels
        parts = list(relative.parts)
        # Find where "src" or "components" or similar starts
        start_idx = 0
        for i, part in enumerate(parts):
            if part in ('src', 'components', 'ui', 'packages'):
                start_idx = i
                break
        
        # Build the output path
        output_path = output_root / Path(*parts[start_idx:])
        # Replace the final part with snake_case filename
        output_path = output_path.parent / snake_filename
    else:
        # Fallback: just use the filename
        output_path = output_root / snake_filename
    
    return output_path
