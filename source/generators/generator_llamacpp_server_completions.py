import random
import requests
from urllib.parse import urljoin

try:
    from extensions.telegram_bot.source.generators.abstract_generator import AbstractGenerator
except ImportError:
    from source.generators.abstract_generator import AbstractGenerator


class Generator(AbstractGenerator):
    model_change_allowed = False
    preset_change_allowed = True
    api_is_slow = True

    def __init__(
            self,
            model_path="",  # Model name for llama.cpp
            n_ctx=2048,
            seed=0,
            n_gpu_layers=0,
    ):
        self.URI = model_path if len(model_path) > 4 else "http://localhost:8080"  # OpenAI-compatible endpoint
        self.n_ctx = n_ctx
        self.headers = {"Content-Type": "application/json"}

    def generate_answer(
        self,
        prompt,
        generation_params,
        eos_token,
        stopping_strings,
        default_answer,
        turn_template="",
        **kwargs,
    ):
        # Prepare the request payload for Ollama API
        request = {
            "prompt": prompt,
            "raw": True,
            "stream": False,
            "temperature": generation_params["temperature"],
            "top_p": generation_params["top_p"],
            "top_k": generation_params["top_k"],
            "repeat_penalty": generation_params["repetition_penalty"],
            "num_ctx": self.n_ctx,
            "n_predict": generation_params["max_new_tokens"],
            "seed": random.randint(0, 1000),  # Random seed for variability
            "stop": stopping_strings
        }

        try:
            response = requests.post(urljoin(self.URI, "/completion"),
                                     json=request,
                                     headers=self.headers,
                                     timeout=60)
            response.raise_for_status()
            result = response.json()["content"]
            return result
        except Exception as e:
            print(f"Error in generation: {str(e)}")
            return default_answer

    def tokens_count(self, text: str = None):
        if self.api_is_slow:
            return 0
        else:
            try:
                response = requests.post(
                    urljoin(self.URI, "/tokenize"),
                    json={"content": text},
                    headers=self.headers,
                    timeout=10
                )
                response.raise_for_status()
                tokens = response.json().get("tokens", [])
                return len(tokens)
            except Exception as e:
                print(f"Error counting tokens: {str(e)}")
                return 0

    def get_model_list(self):
        try:
            response = requests.get("http://localhost:8080/v1/models")
            if response.status_code == 200:
                return [model["id"] for model in response.json()["data"]]
        except:
            pass
        return []

    def load_model(self, model_file: str):
        return False
