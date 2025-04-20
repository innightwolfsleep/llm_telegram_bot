import json
import time
from os.path import exists, normpath
from pathlib import Path
from typing import List, Dict

import yaml


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
        self.text_in: List[str] = []  # "user input history": ["Hi!","Who are you?"], need for regenerate option
        self.name_in: List[str] = []  # user_name history need to correct regenerate option
        self.history: List[Dict[str]] = []  # "history": [["in": "query1", "out": "answer1"],["in": "query2",...
        self.previous_history: Dict[str : List[str]] = {}  # "previous_history": Stores previous messages for back-tracking
        self.msg_id: List[int] = []  # "msg_id": [143, 144, 145, 146], Message IDs for deleting messages
        self.greeting: str = greeting  # "hello" or something
        self.alternate_greetings = []  # List of alternative greetings
        self.last_msg_timestamp: int = 0  # last message timestamp to avoid message flood.

    def __or__(self, arg):
        return arg

    @property
    def history_last_out(self) -> str:
        """Returns the last output message in the history."""
        return self.history[-1]["out"]

    @property
    def history_last_in(self) -> str:
        """Returns the last input message in the history."""
        return self.history[-1]["in"]

    def truncate_last_message(self):
        """Truncate user history (minus one answer and user input)

        Returns:
            user_in: truncated user input string
            msg_id: truncated answer message id (to be deleted in chat)
        """
        msg_id = self.msg_id.pop()  # Remove the last message ID
        user_in = self.text_in.pop()  # Remove the last user input
        self.name_in.pop()  # Remove the last user name
        self.history.pop()  # Remove the last message pair from history
        return user_in, msg_id

    def history_append(self, message="", answer=""):
        """Appends a new message and answer to the history."""
        self.history.append({"in": message, "out": answer})

    def history_last_extend(self, message_add=None, answer_add=None):
        """Extends the last message in the history with additional text.

        Args:
            message_add: Text to append to the last input message.
            answer_add: Text to append to the last output message.
        """
        if len(self.history) > 0:
            if message_add:
                self.history[-1]["in"] = self.history[-1]["in"] + "\n" + message_add
            if answer_add:
                self.history[-1]["out"] = self.history[-1]["out"] + "\n" + answer_add

    def history_as_str(self) -> str:
        """Returns the entire history as a single string."""
        history = ""
        if len(self.history) == 0:
            return history
        for s in self.history:
            if len(s["in"]) > 0:
                history += s["in"]
            if len(s["out"]) > 0:
                history += s["out"]
        return history

    def history_as_list(self) -> list:
        """Returns the entire history as a list of strings."""
        history_list = []
        if len(self.history) == 0:
            return history_list
        for s in self.history:
            if len(s["in"]) > 0:
                history_list.append(s["in"])
            if len(s["out"]) > 0:
                history_list.append(s["out"])
        return history_list

    def change_last_message(self, text_in=None, name_in=None, history_in=None, history_out=None, msg_id=None):
        """Changes the values of the last message in the history.

        Args:
            text_in: New user input.
            name_in: New user name.
            history_in: New input message for the history.
            history_out: New output message for the history.
            msg_id: New message ID.
        """
        if text_in:
            self.text_in[-1] = text_in
        if name_in:
            self.name_in[-1] = name_in
        if history_in:
            self.history[-1]["in"] = history_in
        if history_out:
            self.history[-1]["out"] = history_out
        if msg_id:
            self.msg_id[-1] = msg_id

    def back_to_previous_out(self, msg_id):
        """Reverts the last output message to a previous version based on the message ID.

        Args:
            msg_id: The message ID of the previous output message.

        Returns:
            The previous output message if found, otherwise None.
        """
        if str(msg_id) in self.previous_history:
            last_out = self.history_last_out  # Store the current output
            new_out = self.previous_history[str(msg_id)].pop(-1)  # Get the previous output
            self.history[-1]["out"] = new_out  # Restore the previous output
            self.previous_history[str(msg_id)].insert(0, last_out)  # Store the current output for future revert
            return self.history_last_out
        else:
            return None

    def reset(self):
        """Clear bot history and reset to default everything but language, silero and chat_file."""
        self.name1 = "You"  # Reset user name
        self.name2 = "Bot"  # Reset character name
        self.context = ""  # Reset conversation context
        self.example = ""  # Reset dialogue example
        self.turn_template = ""  # Reset turn template
        self.text_in = []  # Reset user input history
        self.name_in = []  # Reset user name history
        self.history = []  # Reset conversation history
        self.previous_history = {}  # Reset previous history
        self.msg_id = []  # Reset message IDs
        self.greeting = "Hello."  # Reset initial greeting
        self.alternate_greetings = []  # Reset alternative greetings

    def switch_greeting(self):
        """Clear bot history and change greeting to alternate greeting, if alternate exist."""
        if len(self.alternate_greetings) > 0:
            last_greeting = self.greeting  # Store the current greeting
            new_greeting = self.alternate_greetings.pop(-1)  # Get the next greeting
            self.greeting = new_greeting  # Update the greeting
            self.alternate_greetings.insert(0, last_greeting)  # Store the previous greeting
            self.history = []  # Reset history
            self.previous_history = {}  # Reset previous history
            self.msg_id = []  # Reset message IDs
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
                "text_in": self.text_in,
                "name_in": self.name_in,
                "history": self.history,
                "previous_history": self.previous_history,
                "msg_id": self.msg_id,
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
        data = json.loads(json_data)
        try:
            self.char_file = data["char_file"] if "char_file" in data else ""
            self.user_id = data["user_id"] if "user_id" in data else 0
            self.name1 = data["name1"] if "name1" in data else "You"
            self.name2 = data["name2"] if "name2" in data else "Bot"
            self.context = data["context"] if "context" in data else ""
            self.example = data["example"] if "example" in data else ""
            self.language = data["language"] if "language" in data else "en"
            self.silero_speaker = data["silero_speaker"] if "silero_speaker" in data else "None"
            self.silero_model_id = data["silero_model_id"] if "silero_model_id" in data else "None"
            self.turn_template = data["turn_template"] if "turn_template" in data else ""
            self.text_in = data["text_in"] if "text_in" in data else []
            self.name_in = data["name_in"] if "name_in" in data else []
            self.history = data["history"] if "history" in data else []
            self.previous_history = data["previous_history"] if "previous_history" in data else {}
            self.msg_id = data["msg_id"] if "msg_id" in data else []
            self.greeting = data["greeting"] if "greeting" in data else "Hello."
            self.alternate_greetings = data["alternate_greetings"] if "alternate_greetings" in data else []
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
            self.msg_id = []
            self.text_in = []
            self.name_in = []
            self.history = []
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
