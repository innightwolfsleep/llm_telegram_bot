import os

try:
    from extensions.telegram_bot.source.generators.generator_ollama_chat import Generator as OllamaGenerator
except ImportError:
    from source.generators.generator_ollama_chat import Generator as OllamaGenerator


class Generator(OllamaGenerator):
    # llmman (https://github.com/llmmanorg/llmman) serves the Ollama API on port 17434.
    # Override host/port with LLMMAN_HOST=[host][:port].
    base_url = "http://" + os.environ.get("LLMMAN_HOST", "127.0.0.1:17434")
