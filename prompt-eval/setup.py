"""
Prompt evaluation setup utilities.
Call setup_prompt_eval() to initialize the directory structure.
"""

from pathlib import Path

DEFAULT_MODELS = '''# Ollama server location
[ollama]
url = "http://localhost:11434"

[models."mistral:latest"]
model_id = "mistral:latest"
temperature = 0.5
num_ctx = 4096
description = "Small and fast"

[models."gemma4:12b"]
model_id = "gemma4:12b"
temperature = 0.6
num_ctx = 8192
description = "Gemma mid-size model"

[models."gpt-oss-20b-32k"]
model_id = "gpt-oss-20b-32k:latest"
temperature = 0.6
num_ctx = 32768
description = "Open-weight reasoning model, 32k context"

[models."qwen2.5-coder:7b"]
model_id = "qwen2.5-coder:7b"
temperature = 0.2
num_ctx = 8192
description = "Coding model"

[models."qwen3.8:27b"]
model_id = "qwen3.8:27b"
temperature = 0.5
num_ctx = 8192
description = "Larger Qwen model, slower"

[models."glm-4.7-flash:latest"]
model_id = "glm-4.7-flash:latest"
temperature = 0.7
num_ctx = 131072
description = "GLM 4.7 Flash - fast reasoning model"

[models."deepseek-v2:16b"]
model_id = "deepseek-v2:16b"
temperature = 0.5
num_ctx = 16384
description = "DeepSeek v2 16B - coding and reasoning"
'''

DEFAULT_EVALUATION = '''def evaluation(text: str) -> str:
    """Custom evaluation logic. Edit and click 'Reload evaluation.py' in the UI."""
    return "todo"
'''

DEFAULT_PROMPTS = {
    "greet_v1.md": "You are a friendly greeter. Greet the user warmly and ask how their day is going.",
    "greet_v2.md": "You are a friendly greeter. In two sentences, welcome the user and offer to help.",
    "summarise_v1.md": "Summarise the user's text as three bullet points, in plain English, with no preamble.",
}


def setup_prompt_eval(base_dir="."):
    """Initialize the prompt evaluation directory structure."""
    base = Path(base_dir)

    # Create models.toml if missing
    models_file = base / "models.toml"
    if not models_file.exists():
        models_file.write_text(DEFAULT_MODELS, encoding="utf-8")
        print(f"Created {models_file}")

    # Create prompts/ directory and samples
    prompts_dir = base / "prompts"
    prompts_dir.mkdir(exist_ok=True)
    for name, content in DEFAULT_PROMPTS.items():
        file_path = prompts_dir / name
        if not file_path.exists():
            file_path.write_text(content, encoding="utf-8")
            print(f"Created {file_path}")

    # Create evaluation.py if missing
    eval_file = base / "evaluation.py"
    if not eval_file.exists():
        eval_file.write_text(DEFAULT_EVALUATION, encoding="utf-8")
        print(f"Created {eval_file}")


if __name__ == "__main__":
    setup_prompt_eval()
