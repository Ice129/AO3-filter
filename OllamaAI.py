import requests
import json
import subprocess


class OllamaAI:
    def __init__(self, model: str = "dolphin-llama3", preset_mode: int = 0, discard_token: str = None, documents: str = None):
        """
        Initialize the OllamaAI class.

        model: str - The model that the AI should use for generating responses.
        preset_mode: int - The preset personality for the AI.

        possible values for model:
            'dolphin-llama3', 'deepseek-coder-v2'

        possible values for preset_mode:
            -1 - no preset\n
            0 - normal\n
            1 - horny\n
            2 - evil\n
            3 - chronicaly online\n
            4 - just some normal guy\n
            5 - angry\n
            6 - ai pretending to be human\n
            7 - ai trying to find out if the user is a human\n
            8 - 3rd party to keep things on track\n
        """
        self.model = model
        self.options = {
            "repeat_penalty": 1.6,
            "repeat_last_n": -1,
            "num_ctx": self.get_context_window_size(self.model),
        }
        self.discard_token = discard_token #########################################################
        self.__load_model_into_memory()
        self.preset_mode = preset_mode
        self.chat_history = []
        
        if self.preset_mode != -1:
            self.system_message = self.__get_system_message()
            self.__append_system_message()
        else:
            if documents:
                self.system_message = documents
                self.__append_system_message()

    def get_context_window_size(self, model):
        response = subprocess.run(["ollama", "show", model], capture_output=True)
        # get next number after "context length" in the output
        context_length = int(response.stdout.decode().split("context length")[1].split()[0])
        return context_length
    
    def __get_system_message(self):
        with open(f"{self.preset_mode}", "r") as f:
            return f.read()

    def __append_system_message(self):
        self.chat_history.append({"role": "system", "content": self.system_message})

    def __load_model_into_memory(self):
        data = {"model": self.model}
        response = requests.post(
            "http://localhost:11434/api/chat", data=json.dumps(data)
        )
        return

    def set_next_message(self, message):
        self.chat_history.append({"role": "assistant", "content": message})

    def send_message(self, message):
        message = {
            "role": "user",
            "content": message,
            "options": self.options
        }

        self.chat_history.append(message)

        response = self.__get_response()

        response_message = {"role": "assistant", "content": response}
        self.chat_history.append(response_message)

        return response

    def __get_response(self):
        data = {"model": self.model, "messages": self.chat_history, "stream": False}
        response = requests.post(
            "http://localhost:11434/api/chat", data=json.dumps(data)
        )
        response_json = response.json()
        return response_json["message"]["content"]
    
    def speculative_response(self, message): ###############################################################
        message = {
            "role": "user",
            "content": message,
            "options": self.options
        }
        
        chat_copy = self.chat_history.copy() # make a copy of the chat history to avoid modifying the original
        chat_copy.append(message)
        
        data = {"model": self.model, "messages": chat_copy, "stream": False}
        response = requests.post(
            "http://localhost:11434/api/chat", data=json.dumps(data)
        )
        response_json = response.json()
    
    def wipe_chat_history(self):
        self.chat_history = []
        if self.preset_mode != -1:
            self.__append_system_message()
    
    def stop(self):
        self.chat_history = []
        self.system_message = None
        data = {
            "model": self.model,
            "messages": [],
            "keep_alive": 0
        }
        response = requests.post(
            "http://localhost:11434/api/chat", data=json.dumps(data)
        )
        
            
        

if __name__ == "__main__":
    ai = OllamaAI("deepseek-coder-v2", 5)
    while True:
        message = input("\n\033[38;5;208m>>> ")
        response = ai.send_message(message)
        print("\n\033[38;5;33mAI:", response)