# Prompt Evaluation

A local Ollama prompt playground for testing and evaluating prompts with different models.

## Structure

```
prompt-eval/
├── eval-template.ipynb    # Main Gradio UI notebook
├── setup.py               # Setup module - creates default files if missing
├── evaluation.py          # Custom evaluation functions
├── models.toml            # Model configurations
├── prompts/               # Versioned prompt files
│   ├── greet_v1.md        # Example: greeting prompt v1
│   ├── greet_v2.md        # Example: greeting prompt v2
│   └── summarise_v1.md   # Example: summary prompt v1
└── .gitignore             # Excludes __pycache__/
```

## Components

### `setup.py`
Setup module that initializes the directory structure with default files:

```python
from setup import setup_prompt_eval
setup_prompt_eval()  # Creates models.toml, prompts/, evaluation.py if missing
```

Run standalone: `python setup.py`

### `eval-template.ipynb`
- **Purpose**: Interactive Gradio UI for testing prompts with local Ollama models
- **Features**:
  - Select model from `models.toml`
  - Choose prompt and version from `prompts/`
  - Edit prompts on-the-fly
  - Stream responses in real-time
  - Live evaluation with `evaluation.py`

### `models.toml`
TOML configuration file defining available models and their settings:

```toml
[models."model-name"]
model_id = "actual-ollama-model-id"
temperature = 0.7
num_ctx = 4096
description = "Model description"
```

### `prompts/`
Directory containing versioned prompt files. Naming convention: `<name>_v<version>.md`

- Example: `greet_v1.md`, `greet_v2.md`, `summarise_v1.md`
- New prompts: Add files following the naming pattern, then restart the notebook kernel

### `evaluation.py`
Custom evaluation function that the notebook imports and calls:

```python
def evaluation(text: str) -> str:
    """Your custom evaluation logic here."""
    return "result"
```

- **Hot-reload**: Edit the file, then click "Reload evaluation.py" in the UI
- No kernel restart needed

## Setup

### Initialize the project
Run the setup module to create default files:
```bash
python setup.py
```
Or run the notebook cells - the first cell calls `setup_prompt_eval()` automatically.

This creates:
- `models.toml` with example model configurations
- `prompts/` directory with sample prompts
- `evaluation.py` with a stub function

### Prerequisites
- Ollama running: `ollama serve`
- Pull models listed in `models.toml`:
  ```bash
  ollama pull llama3.1
  ollama pull gemma4:12b
  # etc.
  ```

### Install dependencies
```bash
pip install gradio requests
```

## Usage

1. Start Ollama: `ollama serve`
2. Run the notebook from this directory
3. Execute cells in order
4. First run creates example files (`models.toml`, `prompts/`, `evaluation.py`) if missing

### Workflow
- Select model, prompt, and version from dropdowns
- Optionally edit the prompt text
- Enter your message
- Adjust max tokens slider
- Click **Run** to stream the response
- Use **Evaluation** section to test custom evaluation logic

## Customization

### Add a Model
Edit `models.toml`:
```toml
[models."my-model"]
model_id = "my-model:tag"
temperature = 0.7
num_ctx = 4096
description = "My custom model"
```

### Add a Prompt
Create a file in `prompts/` following the naming pattern:
```bash
touch prompts/my_prompt_v1.md
```
Add your prompt text to the file.

### Update Evaluation
Edit `evaluation.py` with your custom logic, then click "Reload evaluation.py" in the UI.

## Notes

- Restart the notebook kernel after editing `models.toml` or adding new prompt files
- The notebook uses streaming for real-time responses
- All communication is with your local Ollama instance (no external API calls)
