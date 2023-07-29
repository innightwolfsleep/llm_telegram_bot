import json
import requests


class Generator:
    model_change_allowed = False  # if model changing allowed without stopping.

    def __init__(self, model_path=f'http://localhost:5000/api/v1/chat', n_ctx=2048):
        self.n_ctx = n_ctx
        if model_path.startswith('http'):
            self.URI = model_path
        else:
            self.URI = f'http://localhost:5000/api/v1/chat'

    def get_answer(
            self,
            prompt,
            generation_params,
            eos_token,
            stopping_strings,
            default_answer,
            turn_template='',
            **kwargs):
        request = {
            'user_input': prompt,
            'max_new_tokens': 250,
            'history': {'internal': [], 'visible': []},
            'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
            'character': 'Example',
            # 'instruction_template': 'Vicuna-v1.1',  # Will get autodetected if unset
            # 'context_instruct': '',  # Optional
            'your_name': 'You',
            'regenerate': False,
            '_continue': False,
            'stop_at_newline': False,
            'chat_generation_attempts': 1,
            # 'chat-instruct_command': 'Continue the chat dialogue below. Write a single reply for the character "<|character|>".\n\n<|prompt|>',
            # Generation params. If 'preset' is set to different than 'None', the values
            # in presets/preset-name.yaml are used instead of the individual numbers.
            'preset': 'None',
            'do_sample': True,
            'temperature': generation_params.get('temperature', 0.7),
            'top_p': generation_params.get('top_p', 0.1),
            'typical_p': generation_params.get('typical_p', 1),
            'epsilon_cutoff': generation_params.get('epsilon_cutoff', 0),  # In units of 1e-4
            'eta_cutoff': generation_params.get('eta_cutoff', 0),  # In units of 1e-4
            'tfs': generation_params.get('tfs', 1),
            'top_a': generation_params.get('top_a', 0),
            'repetition_penalty': generation_params.get('repetition_penalty', 1.18),
            'repetition_penalty_range': 0,
            'top_k': generation_params.get('top_k', 40),
            'min_length': 0,
            'no_repeat_ngram_size': 0,
            'num_beams': 1,
            'penalty_alpha': 0,
            'length_penalty': 1,
            'early_stopping': False,
            'mirostat_mode': 0,
            'mirostat_tau': 5,
            'mirostat_eta': 0.1,

            'seed': -1,
            'add_bos_token': True,
            'truncation_length': self.n_ctx,
            'ban_eos_token': False,
            'skip_special_tokens': True,
            'stopping_strings': stopping_strings
        }
        response = requests.post(self.URI, json=request)

        if response.status_code == 200:
            result = response.json()['results'][0]['history']
            print(json.dumps(result, indent=4))
            print()
            print()
            return result['visible'][-1][1]
        else:
            return default_answer

    def tokens_count(self, text: str):
        return 0


    def get_model_list(self):
        pass


    def load_model(self, model_file: str):
        pass
