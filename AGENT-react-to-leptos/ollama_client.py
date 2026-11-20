"""
Ollama API client for the React -> Leptos Conversion Agent.

Uses OpenAI-compatible endpoint (/v1) like Gradio for better performance.
"""

import json
import httpx
from pathlib import Path
from typing import Optional


class OllamaClient:
    """Client for interacting with the Ollama API via OpenAI-compatible endpoint."""
    
    def __init__(self, url: str = "http://localhost:11434"):
        # Use /v1 endpoint for OpenAI compatibility (faster, like Gradio)
        self.base_url = url.rstrip('/') + "/v1"
        self.default_timeout = 600  # 10 minutes default
    
    def chat(self, 
             model: str, 
             prompt: str, 
             system: Optional[str] = None,
             temperature: float = 0.1,
             num_ctx: int = 8192,
             timeout: Optional[int] = None) -> str:
        """
        Send a chat completion request to Ollama via OpenAI-compatible API.
        
        Args:
            model: The model name (e.g., 'gpt-oss-20b-32k')
            prompt: The user prompt
            system: Optional system prompt
            temperature: Sampling temperature (0.0 - 1.0)
            num_ctx: Context window size
            timeout: Request timeout in seconds (uses default_timeout if None)
            
        Returns:
            The model's response text (content only)
        """
        if timeout is None:
            timeout = self.default_timeout
        
        url = f"{self.base_url}/chat/completions"
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "temperature": temperature,
        }
        
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, json=payload, 
                                      headers={"Content-Type": "application/json"})
                response.raise_for_status()
                data = response.json()
                
                # OpenAI format: choices[0].message.content
                if data.get("choices") and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    content = choice["message"]["content"]
                    finish_reason = choice.get("finish_reason", "")
                    
                    # Check for errors
                    if not content or content.strip() == "":
                        raise ValueError(f"Empty response from model (finish_reason: {finish_reason})")
                    if finish_reason == "length":
                        raise ValueError(f"Response truncated (hit token limit). Increase num_predict.")
                    
                    return content
                else:
                    raise ValueError(f"Unexpected response format: {list(data.keys())}")
        except httpx.HTTPError as e:
            print(f"HTTP Error: {e}")
            raise  # Re-raise the exception
        except Exception as e:
            print(f"Error: {e}")
            raise  # Re-raise the exception


def get_ollama_client() -> OllamaClient:
    """Get an Ollama client configured from models.toml."""
    import tomllib
    
    config_path = Path(__file__).parent / "models.toml"
    try:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
        url = config.get("ollama", {}).get("url", "http://localhost:11434")
        client = OllamaClient(url)
        # Set default timeout from TOML
        timeout = config.get("ollama", {}).get("timeouts", {}).get("request_timeout", 600)
        client.default_timeout = timeout
        return client
    except Exception:
        return OllamaClient()  # Fallback to default
