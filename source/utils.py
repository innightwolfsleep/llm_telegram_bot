import json
import logging
import asyncio

from functools import wraps, partial
from os import listdir
from os.path import exists, normpath
from re import sub, DOTALL
from typing import Dict

from deep_translator import GoogleTranslator as Translator

try:
    import extensions.telegram_bot.source.text_process as tp
    import extensions.telegram_bot.source.const as const
    from extensions.telegram_bot.source.conf import cfg
    from extensions.telegram_bot.source.user import User as User
except ImportError:
    import source.text_process as tp
    import source.const as const
    from source.conf import cfg
    from source.user import User as User


def async_wrap(func):
    """
    Wraps a synchronous function to make it asynchronous.

    Args:
        func: The synchronous function to wrap.

    Returns:
        An asynchronous function that executes the original function in a separate thread.
    """
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        target_func = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, target_func)

    return run


async def translate_text(text: str, source="en", target="en"):
    """
    Translates text from one language to another.

    Args:
        text: The text to translate.
        source: The source language (default: "en").
        target: The target language (default: "en").

    Returns:
        The translated text.
    """
    return Translator(source=source, target=target).translate(text)


async def prepare_text(original_text: str, user: User, direction="to_user"):
    """
    Prepares text for sending to the user or the LLM, including translation and HTML formatting.

    Args:
        original_text: The original text to prepare.
        user: The User object containing user preferences.
        direction: The direction of the translation ("to_model" or "to_user").

    Returns:
        The prepared text.
    """
    text = original_text
    # translate
    if cfg.llm_lang != user.language:
        try:
            if direction == "to_model":
                # if user try to write in model language - "auto" better
                text = await translate_text(text=text, source="auto", target=cfg.llm_lang)
                # text = await translate_text(text=text, source=user.language, target=cfg.llm_lang)
            elif direction == "to_user":
                text = await translate_text(text=text, source=cfg.llm_lang, target=user.language)
        except Exception as exception:
            text = "can't translate text:" + str(text)
            logging.error("translator_error:\n" + str(exception) + "\n" + str(exception.args))

    # Add HTML tags and other...
    def truncate_trim_wrap_code(tr_text, max_length):
        """Truncates and wraps code blocks in HTML tags."""
        def wrap_code(match):
            return f"{cfg.code_html_tag[0]}{match.group(1)}{cfg.code_html_tag[1]}"

        tr_text = tr_text.replace("#", "&#35;").replace("<", "&#60;").replace(">", "&#62;")
        tr_text = sub(r"```.*", "```", tr_text)
        if len(tr_text) > max_length:
            tr_text = tr_text[:max_length]
        tr_text = sub(r"```([\s\S]*?)```", wrap_code, tr_text, flags=DOTALL)
        return tr_text

    if direction not in ["to_model", "no_html"]:
        if cfg.llm_lang != user.language and direction == "to_user" and cfg.translation_as_hidden_text == "on":
            original_text = truncate_trim_wrap_code(original_text, 2000)
            text = truncate_trim_wrap_code(text, 2000)
            text = "\n\n".join(
                [
                    cfg.html_tag[0] + original_text + cfg.html_tag[1],
                    cfg.translate_html_tag[0] + text + cfg.translate_html_tag[1],
                ]
            )
        else:
            text = truncate_trim_wrap_code(text, 4000)
            text = cfg.html_tag[0] + text + cfg.html_tag[1]
    return text


def parse_characters_dir() -> list:
    """
    Parses the characters directory and returns a list of character file names.

    Returns:
        A list of character file names.
    """
    char_list = []
    for f in listdir(cfg.characters_dir_path):
        if f.endswith((".json", ".yaml", ".yml")):
            char_list.append(f)
    return char_list


def parse_presets_dir() -> list:
    """
    Parses the presets directory and returns a list of preset file names.

    Returns:
        A list of preset file names.
    """
    preset_list = []
    for f in listdir(cfg.presets_dir_path):
        if f.endswith(".txt") or f.endswith(".yaml"):
            preset_list.append(f)
    return preset_list


# User checking rules
def check_user_permission(chat_id):
    """
    Checks if a user has permission to access the bot.

    Args:
        chat_id: The user's chat ID.

    Returns:
        True if the user has permission, False otherwise.
    """
    # Read admins list
    if exists(cfg.users_file_path):
        with open(normpath(cfg.users_file_path), "r") as users_file:
            users_list = users_file.read().split()
    else:
        users_list = []
    # check
    if str(chat_id) in users_list or len(users_list) == 0:
        return True
    else:
        return False


def check_user_rule(chat_id, option):
    """
    Checks if a user has permission to perform a specific action.

    Args:
        chat_id: The user's chat ID.
        option: The action to check.

    Returns:
        True if the user has permission, False otherwise.
    """
    if exists(cfg.user_rules_file_path):
        with open(normpath(cfg.user_rules_file_path), "r") as user_rules_file:
            user_rules = json.loads(user_rules_file.read())
    # if checked button with numeral postfix  - delete numerals
    option = sub(r"[0123456789-]", "", option)
    if option.endswith(const.BTN_OPTION):
        option = const.BTN_OPTION
    # Read admins list
    if exists(cfg.admins_file_path):
        with open(normpath(cfg.admins_file_path), "r") as admins_file:
            admins_list = admins_file.read().split()
    else:
        admins_list = []
    # check admin rules
    if str(chat_id) in admins_list or cfg.bot_mode == const.MODE_ADMIN:
        return bool(user_rules[option][const.MODE_ADMIN])
    else:
        return bool(user_rules[option][cfg.bot_mode])


def init_check_user(users: Dict[int, User], chat_id):
    """
    Initializes a new user if they don't already exist.

    Args:
        users: A dictionary of User objects.
        chat_id: The user's chat ID.
    """
    if chat_id not in users:
        # Load default
        users.update({chat_id: User()})
        users[chat_id].user_id = chat_id
        users[chat_id].load_character_file(
            characters_dir_path=cfg.characters_dir_path,
            char_file=cfg.character_file,
        )
        users[chat_id].load_user_history(f"{cfg.history_dir_path}/{str(chat_id)}.json")
        users[chat_id].find_and_load_user_char_history(chat_id, cfg.history_dir_path)


def get_conversation_info(user: User):
    """
    Returns information about the current conversation, such as the length of the history and the context.

    Args:
        user: The User object.

    Returns:
        A string containing information about the conversation.
    """
    history_tokens = -1
    context_tokens = -1
    greeting_tokens = -1
    conversation_tokens = -1
    try:
        history_tokens = tp.generator.get_tokens_count(user.history_as_str())
        context_tokens = tp.generator.get_tokens_count(user.context)
        greeting_tokens = tp.generator.get_tokens_count(user.greeting)
        conversation_tokens = history_tokens + context_tokens + greeting_tokens
    except Exception as e:
        logging.error("options_button tokens_count" + str(e))

    max_token_param = "truncation_length"
    max_tokens = cfg.generation_params[max_token_param] if max_token_param in cfg.generation_params else "???"
    return (
        f"{user.name2}\n"
        f"Conversation length {str(conversation_tokens)}/{max_tokens} tokens.\n"
        f"(context {(str(context_tokens))}, "
        f"greeting {(str(greeting_tokens))}, "
        f"messages {(str(history_tokens))})\n"
        f"Voice: {user.silero_speaker}\n"
        f"Language: {user.language}"
    )
