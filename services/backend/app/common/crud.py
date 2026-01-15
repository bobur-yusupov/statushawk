from typing import Type, TypeVar, Generic, Optional, Dict, Any
from django.db import models
from django.shortcuts import get_object_or_404

T = TypeVar("T", bound=models.Model)


class BaseCRUD(Generic[T]):
    """
    Base service class for generic CRUD operations.
    """

    model: Type[T]


class CreateMixin(BaseCRUD[T]):
    def create(self, user: Any = None, **kwargs: Any) -> T:
        """
        Generic create. Auto-injects 'user' if the model expects it.
        """

        if user and hasattr(self.model, "user"):
            kwargs["user"] = user

        instance = self.model(**kwargs)
        instance.save()
        return instance


class RetrieveMixin(BaseCRUD[T]):
    def get(self, id: int, user: Any = None) -> T:
        """
        Generic get. Enforces ownership if 'user' is passed.
        """
        filters: Dict[str, Any] = {"id": id}
        if user and hasattr(self.model, "user"):
            filters["user"] = user

        return get_object_or_404(self.model, **filters)


class ListMixin(BaseCRUD[T]):
    def list(
        self, user: Any = None, filters: Optional[Dict[str, Any]] = None
    ) -> models.QuerySet[T]:
        """
        Generic list. Auto-filters by user.
        """
        qs = self.model.objects.all()  # type: ignore[attr-defined]

        if user and hasattr(self.model, "user"):
            qs = qs.filter(user=user)

        if filters:
            qs = qs.filter(**filters)

        return qs


class UpdateMixin(BaseCRUD[T]):
    def update(self, instance: T, **data: Any) -> T:
        """
        Generic update. Iterates over data items and sets attributes.
        """
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class DeleteMixin(BaseCRUD[T]):
    def delete(self, instance: T) -> None:
        instance.delete()


class FilterMixin(BaseCRUD[T]):
    def filter(self, user: Any = None, **filters: Any) -> models.QuerySet[T]:
        """
        Generic filter method.
        """
        filter_dict: Dict[str, Any] = {}
        if user and hasattr(self.model, "user"):
            filter_dict["user"] = user

        if filters:
            filter_dict.update(filters)

        return self.model.objects.filter(**filter_dict)  # type: ignore[attr-defined]


# ---------------------------------------------------------
# THE COMBO PACK
# ---------------------------------------------------------


class FullCRUD(
    CreateMixin[T],
    RetrieveMixin[T],
    ListMixin[T],
    UpdateMixin[T],
    DeleteMixin[T],
    FilterMixin[T],
):
    """Inherit from this to get everything instantly."""

    pass
