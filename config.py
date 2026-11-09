"""Settings for this lab, read from environment variables.

load_dotenv() copies the values in your .env file into the environment. A
variable that is already set in your terminal wins over the same one in .env.
"""

import os

from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("MODEL", "qwen3:1.7b")  # which Ollama model to use
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")  # where Ollama is running
NUM_CTX = int(os.getenv("NUM_CTX", "8192"))  # context window, in tokens
HF_TOKEN = os.getenv("HF_TOKEN")  # your Hugging Face token (a secret: never commit it)
HF_TOKENIZER = os.getenv("HF_TOKENIZER", "Qwen/Qwen3-1.7B")  # where to download the model's tokenizer
