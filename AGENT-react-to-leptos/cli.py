#!/usr/bin/env python3
"""
CLI for React -> Leptos Conversion Agent

Usage:
    python cli.py scan <directory> [--output FILE] [--limit N]
    python cli.py convert <file> [--output FILE] [--max-tries N]
    python cli.py batch <directory> --output <dir> [--limit N] [--max-tries N]
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from tools import scan_tsx, read, write_component, seed_scratch_crate, run_cargo_check, parse_errors, map_output_path
from agent import run_agent, run_batch, ModelConfig, load_model_config, load_prompt, strip_code_fences
from pathlib import Path


def cmd_scan(args):
    """
    Scan a directory for TSX files.
    
    Usage:
        python cli.py scan /path/to/components --output manifest.json
    """
    target = Path(args.directory)
    
    if not target.exists():
        print(f"Error: Directory '{target}' does not exist")
        sys.exit(1)
    
    if not target.is_dir():
        print(f"Error: '{target}' is not a directory")
        sys.exit(1)
    
    # Scan for TSX files
    files = scan_tsx(target, exclude=args.exclude)
    
    if args.limit:
        files = files[:args.limit]
    
    print(f"Found {len(files)} TSX file(s) in '{target}'")
    
    # Build manifest
    manifest = []
    for f in files:
        manifest.append({
            "source": str(f.relative_to(target)),
            "absolute": str(f.resolve()),
            "status": "pending",
        })
        print(f"  - {f.relative_to(target)}")
    
    # Save to output file
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(manifest, indent=2))
        print(f"\nManifest saved to: {output_path}")
    else:
        # Print to stdout
        print("\nManifest:")
        print(json.dumps(manifest, indent=2))
    
    return 0


def cmd_convert(args):
    """
    Convert a single TSX file to Leptos.
    
    Usage:
        python cli.py convert /path/to/Button.tsx --output button.rs
    """
    source = Path(args.file)
    
    if not source.exists():
        print(f"Error: File '{source}' does not exist")
        sys.exit(1)
    
    # Load the model config - from CLI flags if provided, otherwise from TOML
    if args.model:
        model_config = ModelConfig(name=args.model, temperature=args.temperature)
    else:
        model_config = load_model_config()
    
    # Read the file
    react_code = read(source)
    
    print(f"Converting: {source}")
    print(f"Model: {model_config.name} (from {'CLI' if args.model else 'TOML'})")
    
    # Run the agent
    result = run_agent(react_code, max_tries=args.max_tries, model_config=model_config)
    
    print(f"\nVerdict: {result['verdict']}")
    print(f"Tries used: {result['tries_used']}")
    print(f"Final code length: {len(result['final_code'])} chars")
    
    # Save output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result['final_code'])
        print(f"\nOutput saved to: {output_path}")
    else:
        print(f"\nFinal code:\n{result['final_code']}")
    
    # Save transcript
    if args.transcript:
        transcript_path = Path(args.transcript)
        transcript_path.parent.mkdir(parents=True, exist_ok=True)
        transcript_path.write_text(json.dumps(result, indent=2, default=str))
        print(f"Transcript saved to: {transcript_path}")
    
    return 0


def cmd_batch(args):
    """
    Convert all TSX files in a directory.
    
    Usage:
        python cli.py batch /path/to/components --output ./outputs
    """
    target = Path(args.directory)
    output = Path(args.output)
    
    if not target.exists():
        print(f"Error: Directory '{target}' does not exist")
        sys.exit(1)
    
    if not target.is_dir():
        print(f"Error: '{target}' is not a directory")
        sys.exit(1)
    
    output.mkdir(parents=True, exist_ok=True)
    
    # Load model config - from CLI flags if provided, otherwise from TOML
    if args.model:
        model_config = ModelConfig(name=args.model, temperature=args.temperature)
    else:
        model_config = load_model_config()
    
    print(f"Scanning: {target}")
    print(f"Model: {model_config.name} (from {'CLI' if args.model else 'TOML'})")
    print(f"Output: {output}")
    print(f"Max tries: {args.max_tries}")
    print(f"File limit: {args.limit}")
    
    # Run batch
    summary = run_batch(
        target=target,
        output=output,
        max_tries=args.max_tries,
        file_limit=args.limit,
        model_config=model_config,
    )
    
    print(f"\nBatch complete:")
    print(f"  Files processed: {summary.get('files_processed', 0)}")
    print(f"  Passed: {summary.get('passed', 0)}")
    print(f"  Failed: {summary.get('failed', 0)}")
    print(f"  Stalled: {summary.get('stalled', 0)}")
    print(f"  Blocked: {summary.get('blocked', 0)}")
    
    return 0


def cmd_convert_manifest(args):
    """
    Convert all components from a manifest file using Ollama.
    
    Usage:
        python cli.py convert-manifest manifest.json --output ./leptos-output
    """
    import json
    
    manifest_path = Path(args.manifest)
    output_dir = Path(args.output)
    
    if not manifest_path.exists():
        print(f"Error: Manifest file '{manifest_path}' not found")
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load manifest
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    # Load model config from TOML (or CLI override)
    if args.model:
        model_config = ModelConfig(name=args.model, temperature=args.temperature)
    else:
        model_config = load_model_config()
    
    # Load prompts
    prompt_template = load_prompt("react_to_leptos")
    
    print(f"Processing {len(manifest)} components from {manifest_path}")
    print(f"Model: {model_config.name} (from {'CLI' if args.model else 'TOML'})")
    print(f"Output: {output_dir}\n")
    
    # Process each component and track results
    converted_count = 0
    failed_count = 0
    
    for item in manifest:
        source_path = Path(item["absolute"])
        
        if not source_path.exists():
            print(f"❌ {item['source']} - FILE NOT FOUND")
            item["status"] = "failed"
            item["error"] = "file_not_found"
            failed_count += 1
            continue
        
        # Read the React code
        react_code = read(source_path)
        
        # Create the prompt
        prompt = prompt_template.replace("{react_code}", react_code)
        
        print(f"🔄 Converting: {item['source']}...")
        
        try:
            # Generate Leptos code via Ollama
            from ollama_client import get_ollama_client
            client = get_ollama_client()
            
            response = client.chat(
                model=model_config.name,
                prompt=prompt,
                temperature=model_config.temperature,
                num_ctx=model_config.num_ctx,
            )
            
            # Strip code fences
            leptos_code = strip_code_fences(response)
            
            # Validate the response is actual code, not an error
            if not leptos_code or leptos_code.strip() == "":
                raise ValueError("Empty response from model")
            if leptos_code.startswith("Error:") or leptos_code.startswith("NEEDS-HUMAN:"):
                raise ValueError(f"Model returned error: {leptos_code[:100]}")
            if "{" in leptos_code[:10] and "model" in leptos_code[:50]:
                raise ValueError("Response appears to be raw JSON, not code")
            if len(leptos_code) < 20:
                raise ValueError(f"Response too short ({len(leptos_code)} chars), likely invalid")
            
            # Map to output path
            output_path = map_output_path(output_dir, source_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the Leptos code
            output_path.write_text(leptos_code)
            
            # Update manifest
            item["status"] = "converted"
            item["output"] = str(output_path.relative_to(output_dir))
            item["verdict"] = "passed"
            item["model"] = model_config.name
            
            print(f"✅ {item['source']} -> {output_path.relative_to(output_dir)} ({len(leptos_code)} chars)")
            converted_count += 1
            
        except Exception as e:
            # Update manifest with failure
            item["status"] = "failed"
            item["error"] = str(e)
            item["verdict"] = "failed"
            print(f"❌ {item['source']} - ERROR: {e}")
            failed_count += 1
    
    # Save updated manifest (overwrite original)
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nDone! {converted_count} converted, {failed_count} failed")
    print(f"Manifest updated: {manifest_path}")
    
    return 0


def cmd_check_compile(args):
    """
    Run cargo check on converted components from manifest.
    
    Usage:
        python cli.py check-compile manifest.json --crate ./scratch_crate
    """
    import json
    import shutil
    
    manifest_path = Path(args.manifest)
    crate_path = Path(args.crate)
    
    if not manifest_path.exists():
        print(f"Error: Manifest file '{manifest_path}' not found")
        sys.exit(1)
    
    if not crate_path.exists():
        print(f"Error: Crate directory '{crate_path}' not found")
        sys.exit(1)
    
    # Load manifest
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    print(f"Checking {len(manifest)} components from {manifest_path}")
    print(f"Crate: {crate_path}\n")
    
    compiled_count = 0
    failed_count = 0
    
    for item in manifest:
        # Check items that were converted, passed, or fixed
        if item.get("status") not in ["converted", "passed", "fixed"]:
            print(f"⊘ {item['source']} - Skipped (status: {item.get('status', 'unknown')})")
            continue
        
        # Get the output path
        if "output" not in item:
            print(f"⚠️ {item['source']} - No output path, skipping")
            continue
        
        print(f"🔍 Checking: {item['source']}...")
        
        try:
            # Find the actual file in leptos-output
            leptos_output_dir = Path("leptos-output")
            if not leptos_output_dir.is_absolute():
                leptos_output_dir = Path.cwd() / leptos_output_dir
            
            output_rel = item["output"]
            source_file = leptos_output_dir / output_rel
            
            if not source_file.exists():
                print(f"❌ {item['source']} - Output file not found: {source_file}")
                item["status"] = "failed_to_compile"
                item["error"] = "output_file_missing"
                item["verdict"] = "failed"
                failed_count += 1
                continue
            
            # Copy to scratch_crate/src/component.rs (what cargo check uses)
            component_file = crate_path / "src" / "component.rs"
            shutil.copy2(source_file, component_file)
            
            # Run cargo check
            raw_output = run_cargo_check(crate_path)
            errors = parse_errors(raw_output)
            
            if errors:
                # Compilation failed
                item["status"] = "failed_to_compile"
                item["verdict"] = "failed"
                item["error_count"] = len(errors)
                item["errors"] = errors
                print(f"❌ {item['source']} - {len(errors)} errors:")
                for err in errors[:3]:  # Show first 3 errors
                    print(f"     {err.get('message', 'Unknown error')}")
                failed_count += 1
            else:
                # Compilation passed
                item["status"] = "compiled"
                item["verdict"] = "passed"
                print(f"✅ {item['source']} - Compiled successfully")
                compiled_count += 1
            
        except Exception as e:
            item["status"] = "failed_to_compile"
            item["error"] = str(e)
            item["verdict"] = "failed"
            print(f"❌ {item['source']} - ERROR: {e}")
            failed_count += 1
    
    # Save updated manifest
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nDone! {compiled_count} compiled, {failed_count} failed")
    print(f"Manifest updated: {manifest_path}")
    
    return 0


def cmd_fix_compile(args):
    """
    Use LLM to fix compilation errors in failed components.
    
    Usage:
        python cli.py fix-compile manifest.json --max-tries 3
    """
    import json
    import time
    
    manifest_path = Path(args.manifest)
    max_tries = args.max_tries or 3
    
    if not manifest_path.exists():
        print(f"Error: Manifest file '{manifest_path}' not found")
        sys.exit(1)
    
    # Load manifest
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    # Load model config from TOML
    model_config = load_model_config()
    if args.model:
        model_config = ModelConfig(name=args.model, temperature=args.temperature)
    
    # Load prompts
    fix_prompt_template = load_prompt("fix_leptos")
    
    print(f"Fixing {len(manifest)} components from {manifest_path}")
    print(f"Model: {model_config.name}")
    print(f"Max tries: {max_tries}\n")
    
    fixed_count = 0
    failed_count = 0
    
    for item in manifest:
        # Only fix items that failed to compile
        if item.get("status") != "failed_to_compile":
            print(f"⊘ {item['source']} - Skipped (status: {item.get('status', 'unknown')})")
            continue
        
        print(f"🔧 Fixing: {item['source']}...")
        
        try:
            # Get the output path
            if "output" not in item:
                print(f"⚠️ {item['source']} - No output path, skipping")
                continue
            
            output_rel = item["output"]
            leptos_output_dir = Path("leptos-output")
            if not leptos_output_dir.is_absolute():
                leptos_output_dir = Path.cwd() / leptos_output_dir
            
            source_file = leptos_output_dir / output_rel
            
            if not source_file.exists():
                print(f"❌ {item['source']} - File not found")
                continue
            
            # Get the code
            code = source_file.read_text()
            
            # Get errors from manifest
            errors = item.get("errors", [])
            error_history = "\n".join([
                f"Line {e.get('line')}: {e.get('message')}"
                for e in errors
            ])
            
            # Build the fix prompt
            prompt = fix_prompt_template.replace("{current_code}", code)
            prompt = prompt.replace("{error_history}", error_history)
            prompt = prompt.replace("{attempt_number}", "1")
            prompt = prompt.replace("{max_attempts}", str(max_tries))
            
            # Call LLM to fix
            from ollama_client import get_ollama_client
            client = get_ollama_client()
            
            response = client.chat(
                model=model_config.name,
                prompt=prompt,
                temperature=model_config.temperature,
                num_ctx=model_config.num_ctx,
            )
            
            # Strip code fences
            fixed_code = strip_code_fences(response)
            
            # Write the fixed code back
            source_file.write_text(fixed_code)
            
            # Update manifest - clear old errors
            item["status"] = "fixed"
            item["verdict"] = "fixed"
            item["fixed_code"] = fixed_code
            # Clear old error data
            if "errors" in item:
                del item["errors"]
            if "error_count" in item:
                del item["error_count"]
            if "error" in item:
                del item["error"]
            
            print(f"✅ {item['source']} - Fixed")
            fixed_count += 1
            
        except Exception as e:
            item["status"] = "failed_to_fix"
            item["error"] = str(e)
            item["verdict"] = "failed"
            print(f"❌ {item['source']} - ERROR: {e}")
            failed_count += 1
    
    # Save updated manifest
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nDone! {fixed_count} fixed, {failed_count} failed")
    print(f"Manifest updated: {manifest_path}")
    print("\nNext: Run check-compile to verify fixes")
    
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='React -> Leptos Conversion Agent CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan a directory for TSX files
  python cli.py scan ./src/components --output manifest.json

  # Convert a single file
  python cli.py convert ./Button.tsx --output button.rs

  # Batch convert a directory
  python cli.py batch ./src --output ./leptos-output --limit 5

  # Convert from manifest using gpt-oss
  python cli.py convert-manifest manifest.json --output ./leptos-output

  # Check if converted files compile
  python cli.py check-compile manifest.json --crate ./scratch_crate

  # Fix compilation errors with LLM
  python cli.py fix-compile manifest.json --max-tries 3
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # SCAN command
    scan_parser = subparsers.add_parser('scan', help='Scan directory for TSX files')
    scan_parser.add_argument('directory', help='Directory to scan')
    scan_parser.add_argument('--output', '-o', help='Output manifest file (JSON)')
    scan_parser.add_argument('--limit', '-n', type=int, help='Limit number of files')
    scan_parser.add_argument('--exclude', nargs='*', default=None,
                          help='Patterns to exclude (e.g., .test.tsx .stories.tsx)')
    
    # CONVERT command
    convert_parser = subparsers.add_parser('convert', help='Convert single TSX file')
    convert_parser.add_argument('file', help='TSX file to convert')
    convert_parser.add_argument('--output', '-o', help='Output Rust file')
    convert_parser.add_argument('--transcript', '-t', help='Save transcript JSON')
    convert_parser.add_argument('--max-tries', type=int, default=3, help='Max fix attempts (default: 3)')
    convert_parser.add_argument('--model', help='Ollama model to use')
    convert_parser.add_argument('--temperature', type=float, default=0.1, help='Temperature (default: 0.1)')
    
    # BATCH command
    batch_parser = subparsers.add_parser('batch', help='Convert all TSX files in directory')
    batch_parser.add_argument('directory', help='Directory to scan')
    batch_parser.add_argument('--output', '-o', required=True, help='Output directory for Rust files')
    batch_parser.add_argument('--limit', '-n', type=int, help='Limit number of files')
    batch_parser.add_argument('--max-tries', type=int, default=3, help='Max fix attempts (default: 3)')
    batch_parser.add_argument('--model', help='Ollama model to use')
    batch_parser.add_argument('--temperature', type=float, default=0.1, help='Temperature (default: 0.1)')
    
    # CHECK-COMPILE command
    check_compile_parser = subparsers.add_parser('check-compile', 
                                                  help='Run cargo check on converted components from manifest')
    check_compile_parser.add_argument('manifest', help='Path to manifest.json file')
    check_compile_parser.add_argument('--crate', '-c', default='./scratch_crate', 
                                       help='Path to scratch crate (default: ./scratch_crate)')
    
    # FIX-COMPILE command
    fix_compile_parser = subparsers.add_parser('fix-compile', 
                                                help='Use LLM to fix compilation errors in failed components')
    fix_compile_parser.add_argument('manifest', help='Path to manifest.json file')
    fix_compile_parser.add_argument('--max-tries', '-n', type=int, default=3, 
                                     help='Max fix attempts (default: 3)')
    fix_compile_parser.add_argument('--model', help='Ollama model to use (overrides TOML)')
    fix_compile_parser.add_argument('--temperature', type=float, help='Temperature (overrides TOML)')
    
    # CONVERT-MANIFEST command
    convert_manifest_parser = subparsers.add_parser('convert-manifest', 
                                                      help='Convert all components from manifest using Ollama')
    convert_manifest_parser.add_argument('manifest', help='Path to manifest.json file')
    convert_manifest_parser.add_argument('--output', '-o', required=True, 
                                          help='Output directory for Rust files')
    convert_manifest_parser.add_argument('--model', help='Ollama model to use (overrides TOML)')
    convert_manifest_parser.add_argument('--temperature', type=float, help='Temperature (overrides TOML)')
    convert_manifest_parser.add_argument('--timeout', type=int, help='Request timeout in seconds (overrides TOML)')
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # Route to the appropriate command
    ## WORKS LATER TEST DEEP DEPTHS
    if args.command == 'scan':
        return cmd_scan(args)
    elif args.command == 'convert':
        return cmd_convert(args)
    elif args.command == 'batch':
        return cmd_batch(args)
    elif args.command == 'convert-manifest':
        return cmd_convert_manifest(args)
    elif args.command == 'check-compile':
        return cmd_check_compile(args)
    elif args.command == 'fix-compile':
        return cmd_fix_compile(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    sys.exit(main() or 0)
