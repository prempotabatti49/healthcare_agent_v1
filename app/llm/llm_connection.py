import os
from openai import OpenAI

# It is best practice to store keys in environment variables
# export OPENAI_API_KEY='your-api-key-here'
client = OpenAI()

class LLMConnection:
    def __init__(self):
        self.client = OpenAI()
    
    def chat(self, messages):
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return response.choices[0].message.content
