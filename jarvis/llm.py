from abc import ABC, abstractmethod
from groq import Groq as Groqq, AsyncGroq as AsyncGroqq
from openai import OpenAI as OpenAII, AsyncOpenAI as AsyncOpenAII
import json

class LLM(ABC):
    def __init__(self, model, temperature=0.7, max_tokens=100, top_p=0.9, stream=True, model_params=None):
        self.model = model
        self.intent_model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.stream = stream
        self.client = None
        
        self.llm_params = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": stream,
        }
        
        self.llm_params.update(model_params or {})

    def completion(self, messages, **kwargs):
        raise NotImplementedError("Method not implemented")
        pass

    async def acompletion(self, messages, **kwargs):
        raise NotImplementedError("Method not implemented")
        pass
    
    def update_params(self, **kwargs):
        self.llm_params.update(kwargs)
        
    def intentify(self, text):
        completion = self.client.chat.completions.create(
            model= self.intent_model,
            messages=[
                {
                    "role": "system",
                    "content": "You always response JSON. "
                },
                {
                    "role": "user",
                    "content": "You always response JSON. Your task is to do a binary classification for the given query here which is the last message of user conversation between her and het assistant. Classify the given query into one of the following three classes:\n\n1/ \"QUESTION\": When user's message is ending in a way that is expected to have an answer from assistant.\n2/ \"PARTIAL\": When the message is not completed yet grammatically, and still is like a middle of conversation.\n3/ \"DEFAULT\": When non of above two cases, and meaning user just sharing a casual statement and no need any response yet.\n\nOutput format:\n{\"class\":\"[Class Label]\"}\n\nQuery:\n" + text
                }
            ],
            temperature=0.01,
            max_tokens=50,
            top_p=1,
            stream=False,
            response_format={"type": "json_object"},
            stop=None,
        )

        response = completion.choices[0].message.content
        return json.loads(response).get("class", "DEFAULT")

class Groq(LLM):
    def __init__(self, model="llama3-8b-8192", **kwargs):
        super().__init__(model, **kwargs)
        self.client = Groqq()
        self.intent_model = "llama3-70b-8192"
    
    def completion(self, messages, **kwargs):
        # Update self.llm_params with kwargs
        self.llm_params.update(kwargs)
        
        return self.client.chat.completions.create(
            messages=messages,
            **self.llm_params,
            # stream=True
            # model=kwargs.get('model', self.model),
            # temperature=kwargs.get('temperature', self.temperature),
            # max_tokens=kwargs.get('max_tokens', self.max_tokens),
            # top_p=kwargs.get('top_p', self.top_p),
            # stream=kwargs.get('stream', self.stream),
        )
        
    def acompletion(self, messages, **kwargs):
        # Raise error this method is not implemented
        raise NotImplementedError("Method not implemented")

class AsyncGroq(LLM):
    def __init__(self, model="llama3-8b-8192", **kwargs):
        super().__init__(model, **kwargs)
        self.client = AsyncGroqq()
        self.intent_model = "llama3-70b-8192"
    
    async def acompletion(self, messages, **kwargs):
        # Update self.llm_params with kwargs
        self.llm_params.update(kwargs)
    
        return await self.client.chat.completions.create(
            messages=messages,
            **self.llm_params,
        )

class OpenAI(LLM):
    def __init__(self, model="gpt-4o", **kwargs):
        super().__init__(model, **kwargs)
        self.client = OpenAII()
    
    def completion(self, messages, **kwargs):
        self.llm_params.update(kwargs)
        return self.client.chat.completions.create(
            messages=messages,
            **self.llm_params
        )
        
class AsyncOpenAI(LLM):
    def __init__(self, model="gpt-4o", **kwargs):
        super().__init__(model, **kwargs)
        self.client = AsyncOpenAII()
    
    async def acompletion(self, messages, **kwargs):
        self.llm_params.update(kwargs)
        return await self.client.chat.completions.create(
            messages=messages,
            **self.llm_params
        )
        
class Ollama(OpenAI):
    def __init__(self, model="llama3", **kwargs):
        super().__init__(model, **kwargs)
        self.client.base_url = "http://localhost:11434/v1"
        self.client.api_key = "ollama"
        
class AsyncOllama(AsyncOpenAI):
    def __init__(self, model="llama3", **kwargs):
        super().__init__(model, **kwargs)
        self.client.base_url = "http://localhost:11434/v1"
        self.client.api_key = "ollama"

if __name__ == "__main__":
    client = Groq()
    client = OpenAI()
    stream = client.completion(
                messages=[
                    {"role": "user", "content": "Why sky os blue?"},
                ],
                stream=True
            )
    
    for chunk in stream:
        response_text = chunk.choices[0].delta.content
        print(response_text)