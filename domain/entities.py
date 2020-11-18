import json
from typing import Optional, Type, TypeVar

from dacite.core import from_dict
from dacite.exceptions import DaciteError

T = TypeVar("T")


def convert_dict_to_entity(json_entity: str, entity_class: Type[T]) -> Optional[T]:
    if not json_entity:
        return None

    try:
        return from_dict(entity_class, json.loads(json_entity))
    except DaciteError:
        # TODO: log this

        return None
