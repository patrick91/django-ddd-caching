import dataclasses
import json
from typing import Any, Generic, List, Optional, Protocol, Type, TypeVar

import aioredis
from asgiref.sync import sync_to_async
from django.db.models.base import Model
from domain.converter import convert_django_model
from domain.entities import convert_dict_to_entity

from .stats import (
    DataFetchingStats,
    increase_redis_gets,
    increase_redis_sets,
    increase_sql_queries,
)

T = TypeVar("T")

M = TypeVar("M", bound=Model)
E = TypeVar("E")


class WithId(Protocol):
    id: Any


def _get_caching_key_for_class(entity_class: Any, id: str) -> str:
    return f"{entity_class.__name__}-{id}"


def _get_caching_key(entity: WithId) -> str:
    return _get_caching_key_for_class(type(entity), entity.id)


class BaseCacheRepository(Generic[M, E]):
    model_class: M
    entity_class: E

    DEFAULT_EXPIRE_IN_SECONDS = 60 * 5

    def __init__(
        self, redis: aioredis.Redis, data_fetching_stats: DataFetchingStats
    ) -> None:
        self.redis = redis
        self.stats = data_fetching_stats

    @increase_redis_sets
    async def _cache_entity(self, entity: WithId):
        await self.redis.set(
            _get_caching_key(entity),
            json.dumps(dataclasses.asdict(entity)),
            expire=self.DEFAULT_EXPIRE_IN_SECONDS,
        )

    @increase_redis_sets
    async def _cache_entities_batch(self, entities: List[WithId]):
        entities_dict = {
            _get_caching_key(entity): json.dumps(dataclasses.asdict(entity))
            for entity in entities
        }

        # TODO: set expiry using a lua script or similar

        await self.redis.mset(
            entities_dict,
            # expire=self.DEFAULT_EXPIRE_IN_SECONDS,
        )

    @increase_redis_gets
    async def _get_cached_entity(self, id: str, entity_class: Type[T]) -> Optional[T]:
        entity = await self.redis.get(_get_caching_key_for_class(entity_class, id))

        return convert_dict_to_entity(entity, entity_class)

    @increase_redis_gets
    async def _get_cached_entities_batch(
        self, ids: List[str], entity_class: Type[T]
    ) -> List[Optional[T]]:
        keys = [_get_caching_key_for_class(entity_class, id) for id in ids]

        entities = await self.redis.mget(*keys)

        return [convert_dict_to_entity(entity, entity_class) for entity in entities]

    @increase_sql_queries
    @sync_to_async
    def _get_by_from_db(self, id: str) -> Optional[M]:
        return self.model_class.objects.filter(id=id).first()

    async def get_by_id(self, id: str) -> Optional[E]:
        entity = await self._get_cached_entity(id, self.entity_class)

        if entity:
            return entity

        db_value = await self._get_by_from_db(id)

        if not db_value:
            return None

        entity = convert_django_model(db_value)

        await self._cache_entity(entity)

        return entity

    @increase_sql_queries
    @sync_to_async
    def _get_batch_by_ids_from_db(self, ids: str) -> List[M]:
        # TODO: this should return {'id': instance, 'id': None}.values()
        # to prevent issues with missing values
        return list(self.model_class.objects.filter(id__in=ids))

    async def get_batch_by_ids(self, ids: List[str]) -> List[Optional[E]]:
        entities = await self._get_cached_entities_batch(ids, self.entity_class)

        if all(entities):
            return entities

        entities_dict = {}
        missing_ids = []

        for id_, entity in zip(ids, entities):
            entities_dict[str(id_)] = entity

            if not entity:
                missing_ids.append(id_)

        missing_entities_db = await self._get_batch_by_ids_from_db(missing_ids)
        missing_entities = []

        for db_entity in missing_entities_db:
            entity = convert_django_model(db_entity)
            print(entity, db_entity, type(entity))

            missing_entities.append(entity)
            entities_dict[str(db_entity.id)] = entity

        await self._cache_entities_batch(missing_entities)

        return list(entities_dict.values())
