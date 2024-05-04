from neomodel import db
from neo4j import GraphDatabase
from contextlib import contextmanager
from neomodel import install_labels
from neomodel import (
    StructuredNode,
    StringProperty,
    RelationshipTo,
    StructuredRel,
    JSONProperty,
    IntegerProperty,
)
from typing import List
from .types import Edge, Node

from dotenv import dotenv_values

config = dotenv_values(".env")


class Relationship(StructuredRel):
    description = StringProperty()
    metadata = JSONProperty()
    order = IntegerProperty()


class Entity(StructuredNode):
    label = StringProperty()
    name = StringProperty(unique_index=True)
    relationship = RelationshipTo("Entity", "RELATED", model=Relationship)


@contextmanager
def neo4jDb():
    username = config["NEO4J_USERNAME"]
    password = config["NEO4J_PASSWORD"]
    uri = config["NEO4J_URI"]
    driver = GraphDatabase().driver(uri, auth=(username, password))

    try:
        db.set_connection(driver=driver)
        yield db
    finally:
        # Code to release resource, e.g.:
        db.close_connection()


class Neo4jGraphModel:
    _edges: List[Edge]
    _create_indices: bool = False

    def __init__(self, edges: List[Edge], create_indices: bool = False):
        self._edges = edges
        self._create_indices = create_indices

    def migrate(self):
        if self._create_indices:
            with neo4jDb as db:
                install_labels(Entity, Relationship)

    def save(self):
        count = 0
        for edge in self._edges:
            with neo4jDb() as db:
                with db.transaction:
                    [entity_1, entity_2] = Entity.get_or_create(
                        edge.node_1.model_dump(), edge.node_2.model_dump()
                    )
                    entity_1.relationship.connect(
                        entity_2,
                        {
                            "description": edge.relationship,
                            **edge.model_dump(exclude=["description"]),
                        },
                    )
                    count += 1
        return count
