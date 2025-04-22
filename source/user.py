import json
import time
from os.path import exists, normpath
from pathlib import Path
from typing import List

import yaml


class Msg:
    """
    Class stored all data related to single message between user and bot
    """
    name_in: str  # username
    text_in: str  # user input
    msg_in: str  # bot request
    msg_out: str  # bot answer
    msg_previous_out: List[str]  # bot answer
    msg_id: int  # user message IDs for possible deleting

    def __init__(self,
                 name_in="User",
                 text_in="",
                 msg_in="",
                 msg_out="",
                 msg_previous_out=None,
                 msg_id=0,
                 ):
        self.name_in = name_in
        self.text_in = text_in
        self.msg_in = msg_in
        self.msg_out = msg_out
        self.msg_previous_out = msg_previous_out if msg_previous_out is not None else []  # Ensure it's a list even when empty
        self.msg_id = msg_id

    def to_json(self) -> str:
        """Serializes the object to JSON string."""
        return json.dumps({
            "name_in": self.name_in,
            "text_in": self.text_in,
            "msg_in": self.msg_in,
            "msg_out": self.msg_out,
            "msg_previous_out": self.msg_previous_out,
            "msg_id": self.msg_id
        })

    @classmethod
    def from_json(cls, json_str: str) -> "Msg":
        """Deserializes the object from JSON string."""
        data = json.loads(json_str)
        return cls(**data)  # Use keyword arguments for initialization


class User:
    """
    Class stored individual tg user info (history, message sequence, etc...) and provide some actions
    """

    def __init__(
            self,
            char_file="",  # Path to the character file (e.g., JSON or YAML)
            user_id=0,  # Unique identifier for the user
            name1="You",  # User's name (default: "You")
            name2="Bot",  # Character's name (default: "Bot")
            context="",  # Context of the conversation (e.g., "Conversation between Bot and You")
            example="",  # Example dialogue for the character
            language="en",  # Language of the conversation (default: "en")
            silero_speaker="None",  # Silero speaker model (for text-to-speech)
            silero_model_id="None",  # Silero model ID (for text-to-speech)
            turn_template="",  # Template for formatting conversation turns
            greeting="Hello.",  # Initial greeting message from the bot (default: "Hello.")
    ):
        """
        Init User class with default attribute

        Args:
          name1: username
          name2: current character name
          context: context of conversation, example: "Conversation between Bot and You"
          greeting: just greeting message from bot
        """
        self.char_file: str = char_file  # Character file path
        self.user_id: int = user_id  # User ID
        self.name1: str = name1  # User's name
        self.name2: str = name2  # Character's name
        self.context: str = context  # Conversation context
        self.example: str = example  # Dialogue example
        self.language: str = language  # Conversation language
        self.silero_speaker: str = silero_speaker  # Silero speaker model
        self.silero_model_id: str = silero_model_id  # Silero model ID
        self.turn_template: str = turn_template  # Turn template
        self.messages: List[Msg] = []  # List of all message exchanges
        self.greeting: str = greeting  # "hello" or something
        self.alternate_greetings = []  # List of alternative greetings
        self.last_msg_timestamp: int = 0  # last message timestamp to avoid message flood.

    def __or__(self, arg):
        return arg

    @property
    def length(self) -> int:
        """Returns length of conversation."""
        return len(self.messages)

    @property
    def last(self) -> Msg:
        """Returns length of conversation."""
        return self.messages[-1]

    def truncate_last_message(self):
        """Truncate user history (minus one answer and user input)

        Returns:
            user_in: truncated user input string
            msg_id: truncated answer message id (to be deleted in chat)
        """
        if not self.messages:
            return None, None

        last_msg = self.messages.pop()
        return last_msg.text_in, last_msg.msg_id

    def history_append(self, message="", answer=""):
        """Appends a new message and answer to the history."""
        msg = Msg(name_in=self.name1, text_in=message, msg_in=message, msg_out=answer)
        self.messages.append(msg)

    def history_last_extend(self, message_add=None, answer_add=None):
        """Extends the last message in the history with additional text.

        Args:
            message_add: Text to append to the last input message.
            answer_add: Text to append to the last output message.
        """
        if self.messages:
            if message_add:
                self.messages[-1].msg_in += "\n" + message_add
            if answer_add:
                self.messages[-1].msg_out += "\n" + answer_add

    def history_as_str(self) -> str:
        """Returns the entire history as a single string."""
        history_str = ""
        for msg in self.messages:
            if msg.msg_in:
                history_str += msg.msg_in
            if msg.msg_out:
                history_str += msg.msg_out
        return history_str

    def history_as_list(self) -> list:
        """Returns the entire history as a list of strings."""
        history_list = []
        for msg in self.messages:
            if msg.msg_in:
                history_list.append(msg.msg_in)
            if msg.msg_out:
                history_list.append(msg.msg_out)
        return history_list

    def change_last_message(self, text_in=None, name_in=None, history_in=None, history_out=None, msg_id=None):
        """Changes the values of the last message in the history.

        Args:
            text_in: New user input.
            name_in: New username.
            history_in: New input message for the history.
            history_out: New output message for the history.
            msg_id: New message ID.
        """
        if not self.messages:
            return

        last_msg = self.messages[-1]
        if text_in is not None:
            last_msg.text_in = text_in
        if name_in is not None:
            last_msg.name_in = name_in
        if history_in is not None:
            last_msg.msg_in = history_in
        if history_out is not None:
            last_msg.msg_out = history_out
        if msg_id is not None:
            last_msg.msg_id = msg_id

    def back_to_previous_out(self, msg_id):
        """Reverts the last output message to a previous version based on the message ID.

        Args:
            msg_id: The message ID of the previous output message.

        Returns:
            The previous output message if found, otherwise None.
        """
        if not self.messages:
            return None

        for msg in reversed(self.messages):
            if msg.msg_id == msg_id and msg.msg_previous_out:
                last_out = msg.msg_out  # Store current output
                new_out = msg.msg_previous_out.pop()  # Get previous output
                msg.msg_out = new_out  # Restore previous output
                msg.msg_previous_out.insert(0, last_out)  # Store current for future revert
                return new_out
        return None

    def reset(self):
        """Clear bot history and reset to default everything but language, silero and chat_file."""
        self.name1 = "You"  # Reset user name
        self.name2 = "Bot"  # Reset character name
        self.context = ""  # Reset conversation context
        self.example = ""  # Reset dialogue example
        self.turn_template = ""  # Reset turn template
        self.messages = []  # Reset all messages
        self.greeting = "Hello."  # Reset initial greeting
        self.alternate_greetings = []  # Reset alternative greetings

    def switch_greeting(self):
        """Clear bot history and change greeting to alternate greeting, if alternate exist."""
        if len(self.alternate_greetings) > 0:
            last_greeting = self.greeting  # Store the current greeting
            new_greeting = self.alternate_greetings.pop(-1)  # Get the next greeting
            self.greeting = new_greeting  # Update the greeting
            self.alternate_greetings.insert(0, last_greeting)  # Store the previous greeting
            self.messages = []  # Reset messages
            return True  # Greeting switched successfully
        else:
            return False  # No alternative greetings available

    def to_json(self):
        """Convert user data to json string.

        Returns:
            user data as json string
        """
        return json.dumps(
            {
                "char_file": self.char_file,
                "user_id": self.user_id,
                "name1": self.name1,
                "name2": self.name2,
                "context": self.context,
                "example": self.example,
                "language": self.language,
                "silero_speaker": self.silero_speaker,
                "silero_model_id": self.silero_model_id,
                "turn_template": self.turn_template,
                "messages": [msg.to_json() for msg in self.messages],
                "greeting": self.greeting,
                "alternate_greetings": self.alternate_greetings,
            }
        )

    def from_json(self, json_data: str):
        """Convert json string data to internal variables of User class

        Args:
            json_data: user json data string

        Returns:
            True if success, otherwise False
        """
        try:
            data = json.loads(json_data)
            self.char_file = data.get("char_file", "")
            self.user_id = data.get("user_id", 0)
            self.name1 = data.get("name1", "You")
            self.name2 = data.get("name2", "Bot")
            self.context = data.get("context", "")
            self.example = data.get("example", "")
            self.language = data.get("language", "en")
            self.silero_speaker = data.get("silero_speaker", "None")
            self.silero_model_id = data.get("silero_model_id", "None")
            self.turn_template = data.get("turn_template", "")
            self.messages = [Msg.from_json(msg_json) for msg_json in data.get("messages", [])]
            self.greeting = data.get("greeting", "Hello.")
            self.alternate_greetings = data.get("alternate_greetings", [])
            return True
        except Exception as exception:
            print("from_json", exception)
            return False

    def load_character_file(self, characters_dir_path: str, char_file: str):
        """Load character_file file.
        First, reset all internal user data to default
        Second, read character_file file as yaml or json and converts to internal User data

        Args:
            characters_dir_path: path to character dir
            char_file: name of character_file file

        Returns:
            True if success, otherwise False
        """
        self.reset()
        # Copy default user data. If reading will fail - return default user data
        try:
            # Try to read character_file file.
            char_file_path = Path(f"{characters_dir_path}/{char_file}")
            with open(normpath(char_file_path), "r", encoding="utf-8") as user_file:
                if char_file.split(".")[-1] == "json":
                    data = json.loads(user_file.read())
                else:
                    data = yaml.safe_load(user_file.read())
            if "data" in data:
                data = data["data"]
            #  load persona and scenario
            self.char_file = char_file
            if "user" in data:
                self.name1 = data["user"]
            if "bot" in data:
                self.name2 = data["bot"]
            if "you_name" in data:
                self.name1 = data["you_name"]
            if "char_name" in data:
                self.name2 = data["char_name"]
            if "name" in data:
                self.name2 = data["name"]
            if "turn_template" in data:
                self.turn_template = data["turn_template"]
            self.context = ""
            if "char_persona" in data:
                self.context += f"{self.name2}'s persona: {data['char_persona'].strip()}\n"
            if "context" in data:
                if data["context"].strip() not in self.context:
                    self.context += f"{data['context'].strip()}\n"
            if "world_scenario" in data:
                if data["world_scenario"].strip() not in self.context:
                    self.context += f"Scenario: {data['world_scenario'].strip()}\n"
            if "scenario" in data:
                if data["scenario"].strip() not in self.context:
                    self.context += f"Scenario: {data['scenario'].strip()}\n"
            if "personality" in data:
                if data["personality"].strip() not in self.context:
                    self.context += f"Personality: {data['personality'].strip()}\n"
            if "description" in data:
                if data["description"].strip() not in self.context:
                    self.context += f"Description: {data['description'].strip()}\n"
            #  add dialogue examples
            if "example_dialogue" in data:
                self.example = f"\n{data['example_dialogue'].strip()}\n"
            #  add character_file greeting
            if "char_greeting" in data:
                self.greeting = data["char_greeting"].strip()
            if "first_mes" in data:
                self.greeting = data["first_mes"].strip()
            if "greeting" in data:
                self.greeting = data["greeting"].strip()
            if "alternate_greetings" in data:
                self.alternate_greetings = data["alternate_greetings"]
            self.context = self._replace_context_templates(self.context)
            self.greeting = self._replace_context_templates(self.greeting)
            self.example = self._replace_context_templates(self.example)
            for i, greeting in enumerate(self.alternate_greetings):
                self.alternate_greetings[i] = self._replace_context_templates(greeting)
            self.messages = []
        except Exception as exception:
            print("load_char_json_file", exception)
        finally:
            print(self.context)
            return self

    def _replace_context_templates(self, s: str) -> str:
        """Replaces placeholders in a string with corresponding user and character names."""
        s = s.replace("{{char}}", self.name2)  # Replace {{char}} with character's name
        s = s.replace("{{user}}", self.name1)  # Replace {{user}} with user's name
        s = s.replace("{{Char}}", self.name2)  # Replace {{Char}} with character's name
        s = s.replace("{{User}}", self.name1)  # Replace {{User}} with user's name
        s = s.replace("<BOT>", self.name2)  # Replace <BOT> with character's name
        s = s.replace("<USER>", self.name1)  # Replace <USER> with user's name
        return s

    def find_and_load_user_char_history(self, chat_id, history_dir_path: str):
        """Find and load user chat history. History files searched by file name template:
            chat_id + char_file + .json (new template versions)
            chat_id + name2 + .json (old template versions)

        Args:
            chat_id: user id
            history_dir_path: path to history dir

        Returns:
            True user history found and loaded, otherwise False
        """
        chat_id = str(chat_id)
        user_char_history_path = f"{history_dir_path}/{str(chat_id)}{self.char_file}.json"
        user_char_history_old_path = f"{history_dir_path}/{str(chat_id)}{self.name2}.json"
        if exists(user_char_history_path):
            return self.load_user_history(user_char_history_path)
        elif exists(user_char_history_old_path):
            return self.load_user_history(user_char_history_old_path)
        return False

    def load_user_history(self, file_path):
        """load history file data to User data

        Args:
            file_path: path to history file

        Returns:
            True user history loaded, otherwise False
        """
        try:
            if exists(file_path):
                with open(normpath(file_path), "r", encoding="utf-8") as user_file:
                    data = user_file.read()
                self.from_json(data)
                if self.char_file == "":
                    self.char_file = self.name2
            return True
        except Exception as exception:
            print(f"load_user_history: {exception}")
            return False

    def save_user_history(self, chat_id, history_dir_path="history"):
        """Save two history file "user + character_file + .json" and default user history files and return their path

        Args:
          chat_id: user chat_id
          history_dir_path: history dir path

        Returns:
          user_char_file_path, default_user_file_path
        """
        if self.char_file == "":
            self.char_file = self.name2
        user_data = self.to_json()
        user_char_file_path = Path(f"{history_dir_path}/{chat_id}{self.char_file}.json")
        with user_char_file_path.open("w", encoding="utf-8") as user_file:
            user_file.write(user_data)

        default_user_file_path = Path(f"{history_dir_path}/{chat_id}.json")
        with default_user_file_path.open("w", encoding="utf-8") as user_file:
            user_file.write(user_data)

        return str(user_char_file_path), str(default_user_file_path)

    def check_flooding(self, flood_avoid_delay=5.0):
        """just check if passed flood_avoid_delay between last timestamp and now and renew new timestamp if True

        Args:
          flood_avoid_delay:

        Returns:
          True or False
        """
        if time.time() - flood_avoid_delay > self.last_msg_timestamp:
            self.last_msg_timestamp = time.time()
            return True
        else:
            return False