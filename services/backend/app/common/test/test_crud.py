from typing import Any
from unittest.mock import MagicMock, patch
from common.crud import (
    FullCRUD,
    CreateMixin,
    RetrieveMixin,
    ListMixin,
    UpdateMixin,
    DeleteMixin,
    FilterMixin,
)


class TestCRUDMixins:
    def test_create_mixin(self) -> None:
        crud: CreateMixin[Any] = CreateMixin()
        crud.model = MagicMock()
        mock_instance = MagicMock()
        crud.model.return_value = mock_instance

        result = crud.create(name="Test")

        crud.model.assert_called_once_with(name="Test")
        mock_instance.save.assert_called_once()
        assert result == mock_instance

    def test_create_mixin_with_user(self) -> None:
        crud: CreateMixin[Any] = CreateMixin()
        crud.model = MagicMock()
        crud.model.user = True
        mock_instance = MagicMock()
        crud.model.return_value = mock_instance
        mock_user = MagicMock()

        result = crud.create(user=mock_user, name="Test")

        crud.model.assert_called_once_with(user=mock_user, name="Test")
        assert result == mock_instance

    @patch("common.crud.get_object_or_404")
    def test_retrieve_mixin(self, mock_get: Any) -> None:
        crud: RetrieveMixin[Any] = RetrieveMixin()
        crud.model = MagicMock()
        mock_instance = MagicMock()
        mock_get.return_value = mock_instance

        result = crud.get(id=1)

        mock_get.assert_called_once_with(crud.model, id=1)
        assert result == mock_instance

    def test_list_mixin(self) -> None:
        crud: ListMixin[Any] = ListMixin()
        crud.model = MagicMock()
        mock_queryset = MagicMock()
        crud.model.objects.all.return_value = mock_queryset

        result = crud.list()

        crud.model.objects.all.assert_called_once()
        assert result == mock_queryset

    def test_list_mixin_with_filters(self) -> None:
        crud: ListMixin[Any] = ListMixin()
        crud.model = MagicMock()
        mock_queryset = MagicMock()
        crud.model.objects.all.return_value = mock_queryset

        crud.list(filters={"is_active": True})

        mock_queryset.filter.assert_called_once_with(is_active=True)

    def test_update_mixin(self) -> None:
        crud: UpdateMixin[Any] = UpdateMixin()
        mock_instance = MagicMock()

        result = crud.update(mock_instance, name="Updated")

        assert mock_instance.name == "Updated"
        mock_instance.save.assert_called_once()
        assert result == mock_instance

    def test_delete_mixin(self) -> None:
        crud: DeleteMixin[Any] = DeleteMixin()
        mock_instance = MagicMock()

        crud.delete(mock_instance)

        mock_instance.delete.assert_called_once()

    def test_filter_mixin(self) -> None:
        crud: FilterMixin[Any] = FilterMixin()
        crud.model = MagicMock()
        mock_queryset = MagicMock()
        crud.model.objects.filter.return_value = mock_queryset

        result = crud.filter(is_active=True)

        crud.model.objects.filter.assert_called_once_with(is_active=True)
        assert result == mock_queryset


class TestFullCRUD:
    def test_full_crud_has_all_methods(self) -> None:
        crud: FullCRUD[Any] = FullCRUD()
        assert hasattr(crud, "create")
        assert hasattr(crud, "get")
        assert hasattr(crud, "list")
        assert hasattr(crud, "update")
        assert hasattr(crud, "delete")
        assert hasattr(crud, "filter")
