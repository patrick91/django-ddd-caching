from __future__ import annotations

from campaigns import models
from domain.repositories.cache import BaseCacheRepository

from ..entities import Brand


class BrandRepository(BaseCacheRepository):
    model_class = models.Brand
    entity_class = Brand
