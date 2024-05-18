from openai import OpenAI
from ..types import LLMClient


class OpenAIClient(LLMClient):
    _model: str
    _temperature: float
    _max_tokens: int
    _top_p: float

    def __init__(
        self, model: str = "gpt-3.5-turbo", temperature=0.2, top_p=1, max_tokens=2048
    ):
        self._model = model
        self._temperature = temperature
        self._top_p = top_p
        self._max_tokens = max_tokens
        self.client = OpenAI()

    def generate(self, user_message: str, system_message: str) -> str:
        print("Using Model: ", self._model)

        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            top_p=self._top_p,
            stop=None,
        )

        return response.choices[0].message.content
