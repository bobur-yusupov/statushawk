from unittest.mock import MagicMock
from common.services import BaseService
from common.crud import FullCRUD


class MockService(BaseService):
    model = MagicMock()
    crud_class = FullCRUD


class TestBaseService:
    def test_service_initialization(self) -> None:
        service: MockService = MockService()

        assert service.crud is not None
        assert service.crud.model == service.model

    def test_create_delegates_to_crud(self) -> None:
        service: MockService = MockService()
        mock_create = MagicMock(return_value="created")
        service.crud.create = mock_create  # type: ignore[method-assign]

        result = service.create(name="Test")

        mock_create.assert_called_once_with(user=None, name="Test")
        assert result == "created"

    def test_get_delegates_to_crud(self) -> None:
        service: MockService = MockService()
        mock_get = MagicMock(return_value="instance")
        service.crud.get = mock_get  # type: ignore[method-assign]

        result = service.get(id=1)

        mock_get.assert_called_once_with(id=1, user=None)
        assert result == "instance"

    def test_list_delegates_to_crud(self) -> None:
        service: MockService = MockService()
        mock_list = MagicMock(return_value="queryset")
        service.crud.list = mock_list  # type: ignore[method-assign]

        result = service.list()

        mock_list.assert_called_once_with(user=None, filters=None)
        assert result == "queryset"

    def test_update_delegates_to_crud(self) -> None:
        service: MockService = MockService()
        mock_instance = MagicMock()
        mock_update = MagicMock(return_value="updated")
        service.crud.update = mock_update  # type: ignore[method-assign]

        result = service.update(mock_instance, name="New")

        mock_update.assert_called_once_with(instance=mock_instance, name="New")
        assert result == "updated"

    def test_delete_delegates_to_crud(self) -> None:
        service: MockService = MockService()
        mock_instance = MagicMock()
        mock_delete = MagicMock()
        service.crud.delete = mock_delete  # type: ignore[method-assign]

        service.delete(mock_instance)

        mock_delete.assert_called_once_with(instance=mock_instance)
