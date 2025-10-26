"""
Custom assertions for AGF testing.

Provides domain-specific assertions for AGF resources.
"""

from typing import Any, Optional


class AGFAssertions:
    """AGF-specific test assertions."""

    @staticmethod
    def assert_fabric_valid(fabric: dict[str, Any]) -> None:
        """Assert that a fabric object has required fields."""
        required_fields = ["id", "name", "organization_id", "project_id", "status"]

        for field in required_fields:
            if field not in fabric:
                raise AssertionError(f"Fabric missing required field: {field}\nFabric: {fabric}")

        # Validate ID format
        if not fabric["id"].startswith("fab-"):
            raise AssertionError(f"Invalid fabric ID format: {fabric['id']}\nExpected format: fab-*")

    @staticmethod
    def assert_cluster_valid(cluster: dict[str, Any]) -> None:
        """Assert that a cluster object has required fields."""
        required_fields = ["id", "name", "fabric_id", "status"]

        for field in required_fields:
            if field not in cluster:
                raise AssertionError(f"Cluster missing required field: {field}\nCluster: {cluster}")

        # Validate ID format
        if not cluster["id"].startswith("clus-"):
            raise AssertionError(f"Invalid cluster ID format: {cluster['id']}\nExpected format: clus-*")

    @staticmethod
    def assert_component_valid(component: dict[str, Any]) -> None:
        """Assert that a component object has required fields."""
        required_fields = ["id", "name", "cluster_id", "type", "status"]

        for field in required_fields:
            if field not in component:
                raise AssertionError(f"Component missing required field: {field}\nComponent: {component}")

        # Validate ID format
        if not component["id"].startswith("comp-"):
            raise AssertionError(f"Invalid component ID format: {component['id']}\nExpected format: comp-*")

    @staticmethod
    def assert_operation_valid(operation: dict[str, Any]) -> None:
        """Assert that an operation object has required fields."""
        required_fields = ["id", "type", "status", "resource_id"]

        for field in required_fields:
            if field not in operation:
                raise AssertionError(f"Operation missing required field: {field}\nOperation: {operation}")

        # Validate ID format
        if not operation["id"].startswith("op-"):
            raise AssertionError(f"Invalid operation ID format: {operation['id']}\nExpected format: op-*")

        # Validate status
        valid_statuses = ["pending", "running", "completed", "failed"]
        if operation["status"] not in valid_statuses:
            raise AssertionError(f"Invalid operation status: {operation['status']}\nValid statuses: {valid_statuses}")

    @staticmethod
    def assert_status(resource: dict[str, Any], expected_status: str, resource_type: str = "resource") -> None:
        """Assert that a resource has the expected status."""
        actual_status = resource.get("status")

        if actual_status != expected_status:
            raise AssertionError(
                f"{resource_type} has unexpected status\n"
                f"Expected: {expected_status}\n"
                f"Actual: {actual_status}\n"
                f"Resource: {resource}"
            )

    @staticmethod
    def assert_has_field(data: dict[str, Any], field: str, expected_value: Optional[Any] = None) -> None:
        """Assert that data has a field, optionally with expected value."""
        if field not in data:
            raise AssertionError(f"Missing field: {field}\nData: {data}")

        if expected_value is not None:
            actual_value = data[field]
            if actual_value != expected_value:
                raise AssertionError(
                    f"Field '{field}' has unexpected value\nExpected: {expected_value}\nActual: {actual_value}"
                )

    @staticmethod
    def assert_id_format(resource_id: str, prefix: str, resource_type: str = "resource") -> None:
        """Assert that a resource ID has the correct format."""
        if not resource_id.startswith(prefix):
            raise AssertionError(f"Invalid {resource_type} ID format: {resource_id}\nExpected prefix: {prefix}")
