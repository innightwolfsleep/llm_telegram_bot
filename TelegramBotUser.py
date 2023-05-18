import json
import yaml
from pathlib import Path


class TelegramBotUser:
    """
    Class stored individual tg user info (history, message sequence, etc...) and provide some actions
    """

    default_messages_template = {  # dict of messages templates for various situations. Use _VAR_ replacement
        "mem_lost": "<b>MEMORY LOST!</b>\nSend /start or any text for new session.",  # refers to non-existing
        "retyping": "<i>_NAME2_ retyping...</i>",  # added when "regenerate button" working
        "typing": "<i>_NAME2_ typing...</i>",  # added when generating working
        "char_loaded": "_NAME2_ LOADED!\n_OPEN_TAG__GREETING__CLOSE_TAG_ ",  # When new char loaded
        "preset_loaded": "LOADED PRESET: _OPEN_TAG__CUSTOM_STRING__CLOSE_TAG_",  # When new char loaded
        "model_loaded": "LOADED MODEL: _OPEN_TAG__CUSTOM_STRING__CLOSE_TAG_",  # When new char loaded
        "mem_reset": "MEMORY RESET!\n_OPEN_TAG__GREETING__CLOSE_TAG_",  # When history cleared
        "hist_to_chat": "To load history - forward message to this chat",  # download history
        "hist_loaded": "_NAME2_ LOADED!\n_OPEN_TAG__GREETING__CLOSE_TAG_"
                       "\n\nLAST MESSAGE:\n_OPEN_TAG__CUSTOM_STRING__CLOSE_TAG_",  # load history
    }

    def __init__(self,
                 name1="You",
                 name2="Bot",
                 context="",
                 example="",
                 language="en",
                 turn_template="",
                 greeting="Hi!"):
        """
        Init User class with default attribute
        :param name1: username
        :param name2: current character name
        :param context: context of conversation, example: "Conversation between Bot and You"
        :param greeting: just greeting message from bot
        :return: None
        """
        self.name1: str = name1
        self.name2: str = name2
        self.context: str = context
        self.example: str = example
        self.language: str = language
        self.turn_template: str = turn_template
        self.user_in: list = []  # "user input history": [["Hi!","Who are you?"]], need for regenerate option
        self.history: list = []  # "history": [["Hi!", "Hi there!","Who are you?", "I am you assistant."]],
        self.msg_id: list = []  # "msg_id": [143, 144, 145, 146],
        self.greeting: str = greeting

    def pop(self):
        #  Converts all data to json string
        user_in = self.user_in.pop()
        msg_id = self.msg_id.pop()
        self.history = self.history[:-2]
        return user_in, msg_id

    def reset_history(self):
        #  clear all user history
        self.user_in = []
        self.history = []
        self.msg_id = []

    def to_json(self):
        #  Converts all data to json string
        return json.dumps({
            "name1": self.name1,
            "name2": self.name2,
            "context": self.context,
            "example": self.example,
            "language": self.language,
            "turn_template": self.turn_template,
            "user_in": self.user_in,
            "history": self.history,
            "msg_id": self.msg_id,
            "greeting": self.greeting,
        })

    def from_json(self, s: str):
        #  Converts json string to internal values
        data = json.loads(s)
        try:
            self.name1 = data["name1"] if "name1" in data else "You"
            self.name2 = data["name2"] if "name2" in data else "Bot"
            self.context = data["context"] if "context" in data else ""
            self.example = data["example"] if "example" in data else ""
            self.language = data["language"] if "language" in data else "en"
            self.turn_template = data["turn_template"] if "turn_template" in data else ""
            self.user_in = data["user_in"]
            self.history = data["history"]
            self.msg_id = data["msg_id"]
            self.greeting = data["greeting"] if "greeting" in data else "Hi!"
            return True
        except Exception as exception:
            print("from_json", exception)
            return False

    def load_character_file(self, characters_dir_path: str, char_file: str):
        # Copy default user data. If reading will fail - return default user data
        try:
            # Try to read char file.
            char_file_path = Path(f'{characters_dir_path}/{char_file}')
            with open(char_file_path, 'r', encoding='utf-8') as user_file:
                if char_file.split(".")[-1] == "json":
                    data = json.loads(user_file.read())
                else:
                    data = yaml.safe_load(user_file.read())
            #  load persona and scenario
            if 'you_name' in data:
                self.name1 = data['you_name']
            if 'char_name' in data:
                self.name2 = data['char_name']
            if 'name' in data:
                self.name2 = data['name']
            if 'turn_template' in data:
                self.turn_template = data['turn_template']
            self.context = ''
            if 'char_persona' in data:
                self.context += f"{self.name2}'s Persona: {data['char_persona'].strip()}\n"
            if 'context' in data:
                self.context += f"{data['context'].strip()}\n"
            if 'world_scenario' in data:
                self.context += f"Scenario: {data['world_scenario'].strip()}\n"
            #  add dialogue examples
            if 'example_dialogue' in data:
                self.example = f"\n{data['example_dialogue'].strip()}\n"
            #  add char greeting
            if 'char_greeting' in data:
                self.greeting = data['char_greeting'].strip()
            if 'greeting' in data:
                self.greeting = data['greeting'].strip()
            self.context = self.replace_context_templates(self.context)
            self.greeting = self.replace_context_templates(self.greeting)
            self.example = self.replace_context_templates(self.example)
            self.msg_id = []
            self.user_in = []
            self.history = []
        except Exception as exception:
            print("load_char_json_file", exception)
        finally:
            return self

    def replace_context_templates(self, s: str) -> str:
        s = s.replace('{{char}}', self.name2)
        s = s.replace('{{user}}', self.name1)
        s = s.replace('<BOT>', self.name2)
        s = s.replace('<USER>', self.name1)
        return s

    def load_user_history(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as user_file:
                data = user_file.read()
            self.from_json(data)
        except Exception as exception:
            print(f"load_user_history: {exception}")

    def save_user_history(self, chat_id, char_name="", history_dir_path="history"):
        """
        Save two history file -user+char and default user history files and return their path
        :param chat_id: user chat_id
        :param char_name: char name (or additional data)
        :param history_dir_path: history dir path
        :return: user_char_file_path, default_user_file_path
        """
        user_data = self.to_json()
        user_char_file_path = Path(f"{history_dir_path}/{chat_id}{char_name}.json")
        with user_char_file_path.open("w", encoding="utf-8") as user_file:
            user_file.write(user_data)

        default_user_file_path = Path(f"{history_dir_path}/{chat_id}.json")
        with default_user_file_path.open("w", encoding="utf-8") as user_file:
            user_file.write(user_data)

        return str(user_char_file_path), str(default_user_file_path)
