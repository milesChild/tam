# imports
import openai
import os
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

class OpenAIInterface():

    def __init__(self):
        """
        Initialize the OpenAI API interface.
        """
        openai.api_key = "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"
    
    def get_completion(prompt, model="gpt-3.5-turbo"):
        messages = [{"role": "user", "content": prompt}]
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0, # this is the degree of randomness of the model's output
        )
        return response.choices[0].message["content"]

    def get_completion_from_messages(messages, model="gpt-3.5-turbo", temperature=0):
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature, # this is the degree of randomness of the model's output
        )
        return response.choices[0].message["content"]