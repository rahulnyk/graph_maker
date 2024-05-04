from pydantic import BaseModel
from typing import List, Dict, Union
from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def __init__(self, model: str, temperature: float, top_p: float):
        pass

    @abstractmethod
    def generate(self, user_message: str, system_message: str) -> str:
        "Generate and return the first choice from chat completion as string"
        pass


class Ontology(BaseModel):
    labels: List[Union[str, Dict]]
    relationships: List[str]

    def dump(self):
        if len(self.relationships) == 0:
            return self.model_dump(exclude=["relationships"])
        else:
            return self.model_dump()


class Node(BaseModel):
    label: str
    name: str


class Edge(BaseModel):
    node_1: Node
    node_2: Node
    relationship: str
    metadata: dict = {}
    order: Union[int, None] = None


class Document(BaseModel):
    text: str
    metadata: dict
