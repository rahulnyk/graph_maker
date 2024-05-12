from .types import Ontology, LLMClient, Edge, Document
from .llm_clients.groq_client import GroqClient
from pydantic import ValidationError
import json
import re
from .logger import GraphLogger
from typing import List, Union
import time

green_logger = GraphLogger(name="GRAPH MAKER LOG", color="green_bright").getLogger()
json_parse_logger = GraphLogger(name="GRAPH MAKER ERROR", color="magenta").getLogger()
verbose_logger = GraphLogger(name="GRAPH MAKER VERBOSE", color="blue").getLogger()

default_ontology = Ontology(
    labels=[
        {"Person": "Person name without any adjectives"},
        "Place",
        "Object",
        "Document",
        "Concept",
        "Organisation",
        "Event",
        "Action",
    ],
    relationships=["Relationship between Any two labeled entities"],
)


class GraphMaker:
    _ontology: Ontology
    _llm_client: LLMClient
    _model: str
    _verbose: bool

    def __init__(
        self,
        ontology: Ontology = default_ontology,
        llm_client: LLMClient = GroqClient(
            model="mixtral-8x7b-32768", temperature=0.2, top_p=1
        ),
        verbose: bool = False,
    ):
        self._ontology = ontology
        self._llm_client = llm_client
        self._verbose = verbose
        if self._verbose:
            verbose_logger.setLevel("INFO")
        else:
            verbose_logger.setLevel("DEBUG")

    def user_message(self, text: str) -> str:
        return f"input text: ```\n{text}\n```"

    def system_message(self) -> str:
        return (
            "You are an expert at creating Knowledge Graphs. "
            "Consider the following ontology. \n"
            f"{self._ontology} \n"
            "The user will provide you with an input text delimited by ```. "
            "Extract all the entities and relationships from the user-provided text as per the given ontology. Do not use any previous knowledge about the context."
            "Remember there can be multiple direct (explicit) or implied relationships between the same pair of nodes. "
            "Be consistent with the given ontology. Use ONLY the labels and relationships mentioned in the ontology. "
            "Format your output as a json with the following schema. \n"
            "[\n"
            "   {\n"
            '       node_1: Required, an entity object with attributes: {"label": "as per the ontology", "name": "Name of the entity"},\n'
            '       node_2: Required, an entity object with attributes: {"label": "as per the ontology", "name": "Name of the entity"},\n'
            "       relationship: Describe the relationship between node_1 and node_2 as per the context, in a few sentences.\n"
            "   },\n"
            "]\n"
            "Do not add any other comment before or after the json. Respond ONLY with a well formed json that can be directly read by a program."
        )

    def generate(self, text: str) -> str:
        # verbose_logger.info(f"SYSTEM_PROMPT: {self.system_message()}")
        response = self._llm_client.generate(
            user_message=self.user_message(text),
            system_message=self.system_message(),
        )
        return response

    def parse_json(self, text: str):
        green_logger.info(f"Trying JSON Parsing: \n{text}")
        try:
            parsed_json = json.loads(text)
            green_logger.info(f"JSON Parsing Successful!")
            return parsed_json
        except json.JSONDecodeError as e:
            json_parse_logger.info(f"JSON Parsing failed with error: { e.msg}")
            verbose_logger.info(f"FAULTY JSON: {text}")
            return None

    def manually_parse_json(self, text: str):
        green_logger.info(f"Trying Manual Parsing: \n{text}")
        pattern = r"\}\s*,\s*\{"
        stripped_text = text.strip("\n[{]}` ")
        # Split the json string into string of objects
        splits = re.split(pattern, stripped_text, flags=re.MULTILINE | re.DOTALL)
        # reconstruct object strings
        obj_string_list = list(map(lambda x: "{" + x + "}", splits))
        edge_list = []
        for string in obj_string_list:
            try:
                edge = json.loads(string)
                edge_list.append(edge)
            except json.JSONDecodeError as e:
                json_parse_logger.info(f"Failed to Parse the Edge: {string}\n{e.msg}")
                verbose_logger.info(f"FAULTY EDGE: {string}")
                continue
        green_logger.info(f"Manually exracted {len(edge_list)} Edges")
        return edge_list

    def json_to_edge(self, edge_dict):
        try:
            edge = Edge(**edge_dict)
        except ValidationError as e:
            json_parse_logger.info(
                f"Failed to parse the Edge: \n{e.errors(include_url=False, include_input=False)}"
            )
            verbose_logger.info(f"FAULTY EDGE: {edge_dict}")
            edge = None
        finally:
            return edge

    def from_text(self, text):
        response = self.generate(text)
        verbose_logger.info(f"LLM Response:\n{response}")

        json_data = self.parse_json(response)
        if not json_data:
            json_data = self.manually_parse_json(response)

        edges = [self.json_to_edge(edg) for edg in json_data]
        edges = list(filter(None, edges))
        return edges

    def from_document(
        self, doc: Document, order: Union[int, None] = None
    ) -> List[Edge]:
        verbose_logger.info(f"Using Ontology:\n{self._ontology}")
        graph = self.from_text(doc.text)
        for edge in graph:
            edge.metadata = doc.metadata
            edge.order = order
        return graph

    def from_documents(
        self,
        docs: List[Document],
        order_attribute: Union[int, None] = None,
        delay_s_between=0,
    ) -> List[Edge]:
        graph: List[Edge] = []
        for index, doc in enumerate(docs):
            ## order defines the chronology or the order in which the documents should in interpretted.
            order = getattr(doc, order_attribute) if order_attribute else index
            green_logger.info(f"Document: {index+1}")
            subgraph = self.from_document(doc, order)
            graph = [*graph, *subgraph]
            if delay_s_between > 0:
                green_logger.info(
                    f"Waiting for {delay_s_between}s before the next request ... "
                )
                time.sleep(delay_s_between)
        return graph
