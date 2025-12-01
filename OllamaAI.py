import requests
import json
import subprocess
import asyncio
import aiohttp


class OllamaAI:
    def __init__(self, model: str = "goekdenizguelmez/JOSIEFIED-Qwen3:4b", preset_mode: int = 0, discard_token: str = None, documents: str = None, max_history_pairs: int = 3):
        """
        Initialize the OllamaAI class.

        model: str - The model that the AI should use for generating responses.
        preset_mode: int - The preset personality for the AI.
        max_history_pairs: int - Maximum number of user-assistant message pairs to keep in history (default: 3).
        """
        self.model = model
        self.options = {
            "repeat_penalty": 1.3,
            "repeat_last_n": 40,
            "num_ctx": self.get_context_window_size(self.model),
        }
        self.discard_token = discard_token #########################################################
        self.max_history_pairs = max_history_pairs
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
        
        # Automatically trim chat history to maintain sliding window
        self.__trim_chat_history()

        return response

    def __get_response(self):
        data = {"model": self.model, "messages": self.chat_history, "stream": False}
        response = requests.post(
            "http://localhost:11434/api/chat", data=json.dumps(data)
        )
        response_json = response.json()
        return response_json["message"]["content"]
    
    async def send_message_async(self, message, session):
        """Async version of send_message that doesn't modify chat history."""
        messages = self.chat_history.copy()
        message_obj = {
            "role": "user",
            "content": message,
            "options": self.options
        }
        messages.append(message_obj)
        
        data = {"model": self.model, "messages": messages, "stream": False}
        
        async with session.post(
            "http://localhost:11434/api/chat",
            json=data,
            timeout=aiohttp.ClientTimeout(total=120)
        ) as response:
            response_json = await response.json()
            return response_json["message"]["content"]
    
    def __trim_chat_history(self):
        """
        Trim chat history to keep only system message + last N user-assistant pairs.
        Maintains a sliding window of recent conversations for contextual ranking.
        """
        if len(self.chat_history) <= 1:  # Only system message or empty
            return
        
        # Separate system message from conversation
        system_messages = [msg for msg in self.chat_history if msg.get("role") == "system"]
        conversation = [msg for msg in self.chat_history if msg.get("role") != "system"]
        
        # Keep only last N pairs (2N messages: N user + N assistant)
        # If max_history_pairs is 0, clear all conversation history
        max_messages = self.max_history_pairs * 2
        if max_messages == 0:
            conversation = []
        elif len(conversation) > max_messages:
            conversation = conversation[-max_messages:]
        
        # Rebuild chat history: system message(s) + trimmed conversation
        self.chat_history = system_messages + conversation
    
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
        """
        Reset chat history to only the system message.
        This clears all conversation context including the sliding window.
        """
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
    ai = OllamaAI("deepseek-r1:14b", 0)
    while True:
        message = input("\n\033[38;5;208m>>> ")
        message = """
work_id: 45849109
title: TOOL-ASSISTED SPEEDRUN
author: karmatens
author_url: https://archiveofourown.org/users/karmatens/pseuds/karmatens
url: https://archiveofourown.org/works/45849109
fandoms: ULTRAKILL (Video Game)
rating: Explicit
warnings: No Archive Warnings Apply
category: Other
is_complete: True
publish_date: 19 Mar 2023
warnings_tags: No Archive Warnings Apply
relationships: Gabriel/V1 (ULTRAKILL)
characters: Gabriel (ULTRAKILL), V1 (ULTRAKILL)
freeform_tags: Speedrunning, Video Game Mechanics, Character Study, Religious Imagery & Symbolism, Loss of Virginity, Robot Sex, Artificial Vagina, Cum Consumption, Size Difference, Power Bottoming, Degradation, Overstimulation, Fucking Machines, (Literally & Figuratively), Metaphysics
summary: Optimization is V1’s specialty. From projectile punching to explosion-propelled feats of acceleration, V1 was made to make itself better: faster. To achieve maximum performance, it opts to optimize its energy usage. A more efficient source of biofuel may exist—but V1 needs a means to extract it. A particular peripheral used by Mindflayers seems promising. V1 intends to test it on Gabriel. There must be something better than blood.
language: English
word_count: 12602
chapters: 1/1
chapters_complete: True
comments: 232
kudos: 2612
bookmarks: 415
hits: 41850

USER INPUT: i am looking for  work that is compleated, has more than 5000 words, and is 2+ chapters long."""
        response = ai.send_message(message)
        print("\n\033[38;5;33mAI:", response)