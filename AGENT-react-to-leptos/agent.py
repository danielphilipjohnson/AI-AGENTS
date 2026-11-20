"""
React -> Leptos Conversion Agent

LLM-powered conversion functions and the main agent loop.
"""

import tomllib
from pathlib import Path
from typing import Any
import json

from tools import (
    read,
    write_component,
    seed_scratch_crate,
    run_cargo_check,
    parse_errors,
)
from ollama_client import get_ollama_client
## ADD default model here

class ModelConfig:
    """Configuration for an Ollama model."""
    
    def __init__(self, name: str, temperature: float = 0.1, num_ctx: int = 8192):
        self.name = name
        self.temperature = temperature
        self.num_ctx = num_ctx


def load_config() -> dict:
    """Load the full configuration from models.toml."""
    config_path = Path(__file__).parent / "models.toml"
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def load_model_config(model_name: str = None) -> ModelConfig:
    """
    Load model configuration from models.toml.
    
    Args:
        model_name: Specific model to load (e.g., 'llava:13b'). 
                     If None, uses the 'convert' model from config.
    
    Returns:
        ModelConfig with name, temperature, and num_ctx from TOML
    """
    config = load_config()
    
    # Get the model name from config if not provided
    if model_name is None:
        models_config = config.get("ollama", {}).get("models", {})
        model_name = models_config.get("convert", "llava:13b")
    
    # Get settings from config
    settings = config.get("ollama", {}).get("settings", {})
    temperature = settings.get("temperature", 0.1)
    num_ctx = settings.get("num_ctx", 8192)
    
    return ModelConfig(name=model_name, temperature=temperature, num_ctx=num_ctx)


def load_prompt(prompt_name: str) -> str:
    """Load a prompt template from the prompts directory."""
    prompt_path = Path(__file__).parent / "prompts" / f"{prompt_name}.md"
    return read(prompt_path)


def chat(model: ModelConfig, prompt: str, system: str = None) -> str:
    """
    Send a prompt to Ollama and get the response.
    
    Returns the message content only (stripped of code fences).
    """
    client = get_ollama_client()
    
    response = client.chat(
        model=model.name,
        prompt=prompt,
        system=system,
        temperature=model.temperature,
        num_ctx=model.num_ctx,
    )
    
    return response


def strip_code_fences(text: str) -> str:
    """Remove markdown code fences and language identifiers from text."""
    import re
    # Remove ```rust```, ```tsx```, ```, etc.
    text = re.sub(r'^```\w*\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n```$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n```\w*$', '', text, flags=re.MULTILINE)
    return text.strip()


def convert(react_code: str, model_config: ModelConfig = None) -> str:
    """
    Convert React TSX code to Leptos Rust.
    
    Args:
        react_code: The React component source code
        model_config: Optional model configuration override
        
    Returns:
        Leptos Rust code (stripped of markdown fences)
    """
    if model_config is None:
        model_config = load_model_config("llava:13b")
    
    prompt_template = load_prompt("react_to_leptos")
    prompt = prompt_template.replace("{react_code}", react_code)
    
    response = chat(model_config, prompt)
    return strip_code_fences(response)


def fix(code: str, error_history: list[dict], attempt: int, max_attempts: int = 3, 
        model_config: ModelConfig = None) -> str:
    """
    Fix Leptos code based on compilation errors.
    
    Args:
        code: Current Leptos code with errors
        error_history: List of previous error dicts
        attempt: Current attempt number (1-indexed)
        max_attempts: Maximum attempts allowed
        model_config: Optional model configuration override
        
    Returns:
        Fixed Leptos Rust code (stripped of markdown fences)
    """
    if model_config is None:
        model_config = load_model_config("llava:13b")
    
    prompt_template = load_prompt("fix_leptos")
    
    # Format error history as string
    error_history_str = "\n".join(
        [f"Attempt {e.get('try', 1)}: {json.dumps(e.get('errors', []))}" 
         for e in error_history]
    )
    
    prompt = prompt_template.replace("{current_code}", code)
    prompt = prompt.replace("{error_history}", error_history_str)
    prompt = prompt.replace("{attempt_number}", str(attempt))
    prompt = prompt.replace("{max_attempts}", str(max_attempts))
    
    response = chat(model_config, prompt)
    return strip_code_fences(response)


def run_agent(react_code: str, max_tries: int = 3, model_config: ModelConfig = None) -> dict:
    """
    Run the full conversion agent loop for a single file.
    
    Does the full loop: convert → check → fix (up to max_tries) → final verdict
    
    Args:
        react_code: The React component source
        max_tries: Maximum number of attempts (default 3)
        model_config: Optional model configuration override
        
    Returns:
        Dictionary with:
        - verdict: "passed" | "failed" | "stalled" | "blocked"
        - tries_used: Number of attempts made
        - attempts: List of attempt dicts (code, errors, try number)
        - final_code: The final generated code
    """
    if model_config is None:
        model_config = load_model_config()
    
    crate_path = seed_scratch_crate()
    code = None
    history = []
    attempts = []
    
    for try_no in range(1, max_tries + 1):
        # Generate code
        try:
            if try_no == 1:
                code = convert(react_code, model_config)
            else:
                code = fix(code, history, try_no, max_tries, model_config)
            
            # Validate the code is not empty or error
            if not code or code.strip() == "":
                raise ValueError("Empty response from model")
            if code.startswith("Error:") or code.startswith("NEEDS-HUMAN:"):
                raise ValueError(f"Model error: {code[:100]}")
        except Exception as e:
            # LLM call failed
            attempts.append({
                "try": try_no,
                "code": code or "",
                "errors": [{"message": str(e), "file": "llm", "line": 0, "column": 0}],
                "error_count": 1,
                "llm_error": str(e),
            })
            if try_no >= max_tries:
                return {
                    "verdict": "failed",
                    "tries_used": try_no,
                    "attempts": attempts,
                    "final_code": code or "",
                    "error": str(e),
                }
            continue
        
        # Write and check
        write_component(crate_path, code)
        raw_output = run_cargo_check(crate_path)
        errors = parse_errors(raw_output)
        
        attempt_record = {
            "try": try_no,
            "code": code,
            "errors": errors,
            "error_count": len(errors),
        }
        attempts.append(attempt_record)
        
        # Print attempt live
        if errors:
            print(f"  Attempt {try_no}/{max_tries}: ❌ {len(errors)} errors")
            for err in errors[:3]:
                msg = err.get("message", "unknown")[:60]
                line = err.get("line", "?")
                print(f"    Line {line}: {msg}")
        else:
            print(f"  Attempt {try_no}/{max_tries}: ✅ compiled successfully")
        
        # Check if errors are outside component.rs (blocked)
        blocked_errors = [e for e in errors if "component.rs" not in e.get("file", "")]
        if blocked_errors:
            return {
                "verdict": "blocked",
                "tries_used": try_no,
                "attempts": attempts,
                "final_code": code,
                "blocked_errors": blocked_errors,
            }
        
        # Success
        if not errors:
            return {
                "verdict": "passed",
                "tries_used": try_no,
                "attempts": attempts,
                "final_code": code,
            }
        
        # Stall detection: identical code to previous attempt
        if try_no > 1 and code == attempts[-2]["code"]:
            return {
                "verdict": "stalled",
                "tries_used": try_no,
                "attempts": attempts,
                "final_code": code,
            }
        
        history = attempts
    
    # Exhausted all tries
    return {
        "verdict": "failed",
        "tries_used": max_tries,
        "attempts": attempts,
        "final_code": code,
    }


def run_batch(target: Path, output: Path, max_tries: int = 3, 
               file_limit: int = None, model_config: ModelConfig = None) -> dict:
    """
    Run the full conversion agent on a batch of TSX files.
    
    Scans the target directory, runs run_agent() on each file,
    and writes results to output directory.
    
    Args:
        target: Path to the directory containing .tsx files
        output: Path to write the converted .rs files
        max_tries: Maximum attempts per file (default 3)
        file_limit: Limit number of files to process (for testing)
        model_config: Optional model configuration override
        
    Returns:
        Summary dictionary with overall statistics and per-file results
    """
    from tools import scan_tsx, read, map_output_path
    import json
    
    if model_config is None:
        model_config = load_model_config()
    
    # Scan for TSX files
    files = scan_tsx(target)
    if file_limit:
        files = files[:file_limit]
    
    output.mkdir(parents=True, exist_ok=True)
    
    results = {
        "target": str(target),
        "output": str(output),
        "model": model_config.name,
        "files_processed": 0,
        "passed": 0,
        "failed": 0,
        "stalled": 0,
        "blocked": 0,
        "files": [],
    }
    
    for tsx_path in files:
        source_rel = tsx_path.relative_to(target)
        print(f"\n{'='*60}")
        print(f"🚀 Processing: {source_rel}")
        print(f"{'='*60}")
        
        # Read the React code
        react_code = read(tsx_path)
        
        # Run the full agent loop
        result = run_agent(react_code, max_tries=max_tries, model_config=model_config)
        
        # Map to output path
        output_path = map_output_path(output, tsx_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result["final_code"])
        
        # Record result
        file_result = {
            "source": str(source_rel),
            "output": str(output_path.relative_to(output)),
            "verdict": result["verdict"],
            "tries_used": result["tries_used"],
            "attempts": result["attempts"],
        }
        results["files"].append(file_result)
        results["files_processed"] += 1
        
        # Update counts
        if result["verdict"] == "passed":
            results["passed"] += 1
            print(f"✅ {source_rel} - passed ({result['tries_used']}/{max_tries} tries)")
        elif result["verdict"] == "stalled":
            results["stalled"] += 1
            print(f"⚠️ {source_rel} - stalled ({result['tries_used']}/{max_tries} tries)")
        elif result["verdict"] == "blocked":
            results["blocked"] += 1
            print(f"🚫 {source_rel} - blocked")
        else:
            results["failed"] += 1
            print(f"❌ {source_rel} - failed ({result['tries_used']}/{max_tries} tries)")
    
    # Save summary
    summary_path = output / "batch_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Done! {results['passed']} passed, {results['failed']} failed, "
          f"{results['stalled']} stalled, {results['blocked']} blocked")
    print(f"Summary saved to: {summary_path}")
    
    return results
