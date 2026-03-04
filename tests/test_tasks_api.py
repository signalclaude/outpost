"""Tests for outpost Tasks API layer."""

import httpx
import pytest
import respx

from outpost.api.client import GraphClient
from outpost.api.tasks import (
    add_task, complete_task, create_task_list, delete_task, delete_task_list,
    find_task_list_id, get_task_lists, list_tasks, update_task,
)


GRAPH_BASE = "https://graph.microsoft.com/v1.0"

SAMPLE_LISTS = {
    "value": [
        {"id": "list-default", "displayName": "Tasks", "wellknownListName": "defaultList"},
        {"id": "list-work", "displayName": "Work", "wellknownListName": "none"},
    ]
}


@pytest.fixture
def client():
    return GraphClient(token="fake-token")


class TestGetTaskLists:
    def test_returns_lists(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json=SAMPLE_LISTS)
            )
            result = get_task_lists(client)
        assert len(result) == 2
        assert result[0]["displayName"] == "Tasks"

    def test_empty_lists(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json={"value": []})
            )
            result = get_task_lists(client)
        assert result == []


class TestFindTaskListId:
    def test_default_list(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json=SAMPLE_LISTS)
            )
            result = find_task_list_id(client)
        assert result == "list-default"

    def test_named_list(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json=SAMPLE_LISTS)
            )
            result = find_task_list_id(client, "Work")
        assert result == "list-work"

    def test_named_list_case_insensitive(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json=SAMPLE_LISTS)
            )
            result = find_task_list_id(client, "work")
        assert result == "list-work"

    def test_not_found_raises(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json=SAMPLE_LISTS)
            )
            with pytest.raises(ValueError, match="not found"):
                find_task_list_id(client, "Nonexistent")

    def test_no_lists_raises(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json={"value": []})
            )
            with pytest.raises(ValueError, match="No task lists found"):
                find_task_list_id(client)


class TestAddTask:
    def test_basic_task(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json=SAMPLE_LISTS)
            )
            route = router.post("/me/todo/lists/list-default/tasks").mock(
                return_value=httpx.Response(201, json={"id": "task-1", "title": "Buy milk"})
            )
            result = add_task(client, "Buy milk")
        assert result["title"] == "Buy milk"
        body = route.calls[0].request
        import json
        parsed = json.loads(body.content)
        assert parsed["title"] == "Buy milk"
        assert parsed["importance"] == "normal"

    def test_task_with_due_date(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json=SAMPLE_LISTS)
            )
            route = router.post("/me/todo/lists/list-default/tasks").mock(
                return_value=httpx.Response(201, json={"id": "task-1", "title": "Review"})
            )
            add_task(client, "Review", due_date="2026-03-15")
        import json
        parsed = json.loads(route.calls[0].request.content)
        assert parsed["dueDateTime"]["dateTime"] == "2026-03-15T00:00:00"

    def test_task_with_priority(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json=SAMPLE_LISTS)
            )
            route = router.post("/me/todo/lists/list-default/tasks").mock(
                return_value=httpx.Response(201, json={"id": "task-1", "title": "Urgent"})
            )
            add_task(client, "Urgent", priority="high")
        import json
        parsed = json.loads(route.calls[0].request.content)
        assert parsed["importance"] == "high"

    def test_task_in_named_list(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json=SAMPLE_LISTS)
            )
            route = router.post("/me/todo/lists/list-work/tasks").mock(
                return_value=httpx.Response(201, json={"id": "task-1", "title": "Work task"})
            )
            add_task(client, "Work task", list_name="Work")
        assert route.called


class TestListTasks:
    def test_list_all_tasks(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json=SAMPLE_LISTS)
            )
            router.get("/me/todo/lists/list-default/tasks").mock(
                return_value=httpx.Response(200, json={
                    "value": [
                        {"id": "t1", "title": "Task 1", "status": "notStarted"},
                        {"id": "t2", "title": "Task 2", "status": "completed"},
                    ]
                })
            )
            result = list_tasks(client)
        assert len(result) == 2

    def test_list_with_due_filter(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json=SAMPLE_LISTS)
            )
            route = router.get("/me/todo/lists/list-default/tasks").mock(
                return_value=httpx.Response(200, json={"value": []})
            )
            list_tasks(client, due_filter="2026-03-15")
        request = route.calls[0].request
        assert "filter" in str(request.url)

    def test_list_in_named_list(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json=SAMPLE_LISTS)
            )
            router.get("/me/todo/lists/list-work/tasks").mock(
                return_value=httpx.Response(200, json={"value": [{"id": "t1", "title": "Work task"}]})
            )
            result = list_tasks(client, list_name="Work")
        assert len(result) == 1


class TestUpdateTask:
    def test_update_title(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json=SAMPLE_LISTS)
            )
            route = router.patch("/me/todo/lists/list-default/tasks/task-1").mock(
                return_value=httpx.Response(200, json={"id": "task-1", "title": "New Title"})
            )
            result = update_task(client, "task-1", title="New Title")
        assert result["title"] == "New Title"
        import json
        parsed = json.loads(route.calls[0].request.content)
        assert parsed["title"] == "New Title"

    def test_update_priority(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json=SAMPLE_LISTS)
            )
            route = router.patch("/me/todo/lists/list-default/tasks/task-1").mock(
                return_value=httpx.Response(200, json={"id": "task-1", "importance": "high"})
            )
            update_task(client, "task-1", priority="high")
        import json
        parsed = json.loads(route.calls[0].request.content)
        assert parsed["importance"] == "high"

    def test_update_due_date(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json=SAMPLE_LISTS)
            )
            route = router.patch("/me/todo/lists/list-default/tasks/task-1").mock(
                return_value=httpx.Response(200, json={"id": "task-1"})
            )
            update_task(client, "task-1", due_date="2026-04-01")
        import json
        parsed = json.loads(route.calls[0].request.content)
        assert parsed["dueDateTime"]["dateTime"] == "2026-04-01T00:00:00"

    def test_update_in_named_list(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json=SAMPLE_LISTS)
            )
            route = router.patch("/me/todo/lists/list-work/tasks/task-1").mock(
                return_value=httpx.Response(200, json={"id": "task-1"})
            )
            update_task(client, "task-1", list_name="Work", title="Updated")
        assert route.called


class TestCompleteTask:
    def test_complete_task(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json=SAMPLE_LISTS)
            )
            route = router.patch("/me/todo/lists/list-default/tasks/task-1").mock(
                return_value=httpx.Response(200, json={"id": "task-1", "status": "completed"})
            )
            result = complete_task(client, "task-1")
        assert result["status"] == "completed"
        import json
        parsed = json.loads(route.calls[0].request.content)
        assert parsed["status"] == "completed"


class TestDeleteTask:
    def test_delete_task(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json=SAMPLE_LISTS)
            )
            route = router.delete("/me/todo/lists/list-default/tasks/task-1").mock(
                return_value=httpx.Response(204)
            )
            result = delete_task(client, "task-1")
        assert result == {}
        assert route.called

    def test_delete_in_named_list(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json=SAMPLE_LISTS)
            )
            route = router.delete("/me/todo/lists/list-work/tasks/task-1").mock(
                return_value=httpx.Response(204)
            )
            delete_task(client, "task-1", list_name="Work")
        assert route.called


class TestCreateTaskList:
    def test_create_list(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.post("/me/todo/lists").mock(
                return_value=httpx.Response(201, json={"id": "new-list", "displayName": "Shopping"})
            )
            result = create_task_list(client, "Shopping")
        assert result["displayName"] == "Shopping"
        assert route.called


class TestDeleteTaskList:
    def test_delete_list(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.delete("/me/todo/lists/list-123").mock(
                return_value=httpx.Response(204)
            )
            result = delete_task_list(client, "list-123")
        assert result == {}
        assert route.called
