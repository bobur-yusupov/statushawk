from typing import Type, TypeVar, Generic, Optional, Dict, Any
from django.db import models
from django.db.models import QuerySet
from .crud import FullCRUD

T = TypeVar("T", bound=models.Model)


class BaseService(Generic[T]):
    """Base service class that uses CRUD layer."""

    model: Type[T]
    crud_class: Type[FullCRUD[T]] = FullCRUD

    def __init__(self) -> None:
        self.crud = self.crud_class()
        self.crud.model = self.model

    def create(self, user: Any = None, **kwargs: Any) -> T:
        return self.crud.create(user=user, **kwargs)

    def get(self, id: int, user: Any = None) -> T:
        return self.crud.get(id=id, user=user)

    def list(
        self, user: Any = None, filters: Optional[Dict[str, Any]] = None
    ) -> QuerySet[T]:
        return self.crud.list(user=user, filters=filters)

    def update(self, instance: T, **data: Any) -> T:
        return self.crud.update(instance=instance, **data)

    def delete(self, instance: T) -> None:
        return self.crud.delete(instance=instance)
