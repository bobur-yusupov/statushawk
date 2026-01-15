from typing import Type, TypeVar, Generic, List, Optional
from django.db import models
from django.shortcuts import get_object_or_404

T = TypeVar('T', bound=models.Model)

class BaseCRUD(Generic[T]):
    """
    Base service class for generic CRUD operations.
    """
    model: Type[T]


class CreateMixin(BaseCRUD[T]):
    def create(self, user=None, **kwargs) -> T:
        """
        Generic create. Auto-injects 'user' if the model expects it.
        """

        if user and hasattr(self.model, 'user'):
            kwargs['user'] = user

        instance = self.model(**kwargs)
        instance.save()
        return instance
    
class RetrieveMixin(BaseCRUD[T]):
    def get(self, id: int, user=None) -> T:
        """
        Generic get. Enforces ownership if 'user' is passed.
        """
        filters = {"id": id}
        if user and hasattr(self.model, 'user'):
            filters["user"] = user
            
        return get_object_or_404(self.model, **filters)

class ListMixin(BaseCRUD[T]):
    def list(self, user=None, filters: dict = None) -> models.QuerySet[T]:
        """
        Generic list. Auto-filters by user.
        """
        qs = self.model.objects.all()
        
        if user and hasattr(self.model, 'user'):
            qs = qs.filter(user=user)
            
        if filters:
            qs = qs.filter(**filters)
            
        return qs

class UpdateMixin(BaseCRUD[T]):
    def update(self, instance: T, **data) -> T:
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
    def filter(self, user=None, **filters) -> models.QuerySet[T]:
        """
        Generic filter method.
        """
        if user and hasattr(self.model, 'user'):
            filters["user"] = user

        if filters:
            filters.update(filters)

        return self.model.objects.filter(**filters)

# ---------------------------------------------------------
# THE COMBO PACK
# ---------------------------------------------------------

class FullCRUD(
    CreateMixin[T], 
    RetrieveMixin[T], 
    ListMixin[T], 
    UpdateMixin[T], 
    DeleteMixin[T],
    FilterMixin[T]
):
    """Inherit from this to get everything instantly."""
    pass
