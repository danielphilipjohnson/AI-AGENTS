scan test

python3 cli.py scan //home/daniel/Documents/agency/mainsite/packages/ui/src/layout --output manifest.json

python3 cli.py scan //home/daniel/Documents/agency/mainsite --output manifest.json


python3 cli.py convert-manifest manifest.json --output ./leptos-output --model qwen2.5-coder:7b


now we need to cargo check


python3 cli.py scan //home/daniel/Documents/agency/mainsite/packages/ui/src/layout --output manifest.json


# Stage 1: Convert
python3 cli.py convert-manifest manifest.json --output ./leptos-output

# Stage 2: Check
python3 cli.py check-compile manifest.json

# Stage 3: Fix
python3 cli.py fix-compile manifest.json

# Stage 2 again: Verify
python3 cli.py check-compile manifest.json


python3 cli.py run manifest.json --output ./leptos-output --max-tries 3



# One-shot batch (easiest)
python3 cli.py batch /path/to/components --output ./leptos-output --max-tries 3

# Or with manifest tracking
python3 cli.py scan /path/to/components --output manifest.json
python3 cli.py run manifest.json --output ./leptos-output --max-tries 3