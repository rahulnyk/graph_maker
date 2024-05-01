from groq import Groq
from ..types import LLMClient

client = Groq()


class GroqClient(LLMClient):
    _model: str
    _temperature: float
    _top_p: float

    def __init__(self, model: str = "mixtral-8x7b-32768", temperature=0.2, top_p=1):

        self._model = model
        self._temperature = temperature
        self._top_p = top_p

    def generate(self, user_message: str, system_message: str) -> str:
        print("Using Model: ", self._model)
        result = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_message},
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
            # The language model which will generate the completion.
            model=self._model,
            #
            # Optional parameters
            #
            temperature=self._temperature,
            # The maximum number of tokens to generate. Requests can use up to
            # 2048 tokens shared between prompt and completion.
            # max_tokens=2084,
            # Controls diversity via nucleus sampling: 0.5 means half of all
            # likelihood-weighted options are considered.
            top_p=self._top_p,
            # A stop sequence is a predefined or user-specified text string that
            # signals an AI to stop generating content, ensuring its responses
            # remain focused and concise. Examples include punctuation marks and
            # markers like "[end]".
            stop=None,
            # If set, partial message deltas will be sent.
            stream=False,
        )

        return result.choices[0].message.content
