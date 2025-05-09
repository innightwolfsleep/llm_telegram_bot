import importlib
import logging
from re import findall, match
from typing import List, Dict

try:
    from extensions.telegram_bot.source.generators.abstract_generator import AbstractGenerator
except ImportError:
    from source.generators.abstract_generator import AbstractGenerator


generator: AbstractGenerator


# ====================================================================================
# GENERATOR
def init(script="generator_llama_cpp.py", model_path="", n_ctx=4096, n_gpu_layers=0):
    """Initiate generator type
    generator - is a class Generator from package generators/script
    Generator class should contain method:
       __init__() - method to initiate model
       get_answer() - method get answer
       tokens_count(str) - method to get str length in tokens
    If Generator.model_change_allowed = True - also method:
       get_model_list() - get list of available models
       load_model(str) - load new model

    Args:
      script: script type, one of generators/*.py files
      model_path: path to model file, if generator needs
      n_ctx: context length, if generator needs
      n_gpu_layers: n_gpu_layers for llama
    """
    logging.info(f"### text_process INIT generator: {script}, model: {model_path} ###")
    try:
        generator_class = getattr(importlib.import_module("source.generators." + script), "Generator")
    except ImportError:
        generator_class = getattr(
            importlib.import_module("extensions.telegram_bot.source.generators." + script), "Generator"
        )
    global generator
    generator = generator_class(model_path, n_ctx=n_ctx, n_gpu_layers=n_gpu_layers)
    logging.info(f"### text_process INIT generator: {script}, model: {model_path} DONE ###")


def generate_answer(
        prompt: str,
        generation_params: Dict,
        eos_token: List[str],
        stopping_strings: List[str],
        default_answer: str,
        turn_template: str = "",
        **kwargs,
) -> str:
    """Generate and return answer string.

    Args:
      prompt: user prompt
      generation_params: dict with various generator params
      eos_token: list with end of string tokens
      stopping_strings: list with strings stopping generating
      default_answer: if generating fails, default_answer will be returned
      turn_template: turn template if generator needs it

    Returns:
      generation result string
    """
    # Preparing, add stopping_strings
    answer = default_answer
    generation_params.update({"turn_template": turn_template})
    try:
        answer = generator.generate_answer(
            prompt=prompt,
            generation_params=generation_params,
            eos_token=eos_token,
            stopping_strings=stopping_strings,
            default_answer=default_answer,
            turn_template=turn_template,
            kwargs=kwargs
        )
    except Exception as exception:
        logging.error("generation error:", str(exception) + str(exception.args))
    return answer


def get_tokens_count(text: str):
    """Return string length in tokens

    Args:
      text: text to be counted

    Returns:
      text token length (int)
    """
    count = generator.tokens_count(text)
    # If generator tokens_count invalid - count approximate
    if count <= 1:
        word_token_splitter = 6
        # Split the text into tokens (words, punctuation, special characters, numbers, newlines)
        tokens = findall(r'\b\w+\b|[^\w\s]|[\d]+|\n', text)
        # Handle long words
        long_words = [word for word in tokens if len(word) > word_token_splitter and match(r'\w+', word)]
        for word in long_words:
            tokens.extend([word[i:i + word_token_splitter] for i in range(0, len(word), word_token_splitter)])
        count = len(tokens)

    return count


def get_model_list():
    """Return list of available models

    Returns:
      list of available models
    """
    return generator.get_model_list()


def load_model(model_file: str):
    """Change current llm model to model_file

    Args:
      model_file: model file to be loaded

    Returns:
      True if loading successful, otherwise False
    """
    return generator.load_model(model_file)
