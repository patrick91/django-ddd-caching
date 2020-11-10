import json
from dataclasses import dataclass
from typing import Type, Optional, TypeVar

from dacite.core import from_dict
from dacite.exceptions import DaciteError


@dataclass
class Event:
    id: str
    title: str


@dataclass
class Campaign:
    id: str
    title: str


EntityType = TypeVar("EntityType", Event, Campaign)


def convert_dict_to_entity(
    entity: str, entity_class: Type[EntityType]
) -> Optional[EntityType]:
    if not entity:
        return None

    try:
        return from_dict(entity_class, json.loads(entity))
    except DaciteError:
        # TODO: log this

        return None
