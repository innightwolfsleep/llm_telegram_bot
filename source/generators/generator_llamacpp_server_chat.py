import random
import requests

try:
    from extensions.telegram_bot.source.generators.abstract_generator import AbstractGenerator
except ImportError:
    from source.generators.abstract_generator import AbstractGenerator


class Generator(AbstractGenerator):
    model_change_allowed = False
    preset_change_allowed = True

    def __init__(
            self,
            model_path="",  # Model name for llama.cpp
            n_ctx=2048,
            seed=0,
            n_gpu_layers=0,
    ):
        self.model = model_path
        self.n_ctx = n_ctx
        self.headers = {"Content-Type": "application/json"}
        self.URI = "http://localhost:8080/v1/chat/completions"  # OpenAI-compatible endpoint

    def generate_answer(
            self,
            prompt,
            generation_params,
            eos_token,
            stopping_strings,
            default_answer,
            kwargs,
            turn_template="",
    ):
        # Prepare messages in OpenAI format
        history = kwargs["history"]
        context = kwargs["context"]
        example = kwargs["example"]
        greeting = kwargs["greeting"]

        messages = [
            {"role": "system", "content": context},
            {"role": "system", "content": example},
            {"role": "assistant", "content": greeting},
        ]

        for m in history:
            if m["in"]:
                messages.append({"role": "user", "content": m["in"]})
            if m["out"]:
                messages.append({"role": "assistant", "content": m["out"]})

        # Add current prompt
        messages.append({"role": "user", "content": prompt})

        request = {
            "model": self.model,
            "messages": messages,
            "temperature": generation_params["temperature"],
            "top_p": generation_params["top_p"],
            "top_k": generation_params.get("top_k", 40),  # Default if not provided
            "max_tokens": generation_params["max_new_tokens"],
            "stop": stopping_strings + [eos_token] if eos_token else stopping_strings,
            "seed": random.randint(0, 1000),
        }

        try:
            response = requests.post(self.URI, json=request, headers=self.headers, timeout=60)
            response.raise_for_status()

            result = response.json()["choices"][0]["message"]["content"]
            return result
        except Exception as e:
            print(f"Error in generation: {str(e)}")
            return default_answer

    def tokens_count(self, text: str = None):
        # For llama.cpp with OpenAI API, you might need to implement token counting
        # Alternatively, use the /v1/tokenize endpoint if available
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