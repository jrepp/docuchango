"""
Test fixtures and data factories for AGF testing.

Provides reusable test data generation and resource cleanup.
"""

import random
import string
import time
from dataclasses import dataclass
from typing import List, Optional

from .cli import AGFCLIRunner, CLIResult


def random_id(prefix: str = "test", length: int = 8) -> str:
    """Generate a random ID with prefix."""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    timestamp = int(time.time())
    return f"{prefix}-{timestamp}-{suffix}"


def random_name(prefix: str = "test") -> str:
    """Generate a random resource name."""
    return random_id(prefix)


@dataclass
class TestFabric:
    """Test fabric with cleanup tracking."""
    
    id: str
    name: str
    description: str
    operation_id: Optional[str] = None
    
    def __repr__(self) -> str:
        return f"TestFabric(id={self.id}, name={self.name})"


@dataclass
class TestCluster:
    """Test cluster with cleanup tracking."""
    
    id: str
    name: str
    fabric_id: str
    operation_id: Optional[str] = None
    
    def __repr__(self) -> str:
        return f"TestCluster(id={self.id}, name={self.name}, fabric_id={self.fabric_id})"


@dataclass
class TestComponent:
    """Test component with cleanup tracking."""
    
    id: str
    name: str
    cluster_id: str
    type: str
    operation_id: Optional[str] = None
    
    def __repr__(self) -> str:
        return f"TestComponent(id={self.id}, name={self.name}, cluster_id={self.cluster_id})"


class ResourceFactory:
    """Factory for creating test resources with automatic cleanup."""
    
    def __init__(self, cli_runner: AGFCLIRunner):
        """
        Initialize factory with CLI runner.
        
        Args:
            cli_runner: AGF CLI runner for creating resources
        """
        self.cli = cli_runner
        self.fabrics: List[TestFabric] = []
        self.clusters: List[TestCluster] = []
        self.components: List[TestComponent] = []
    
    def create_fabric(
        self,
        name: Optional[str] = None,
        description: str = "Test fabric",
        region: str = "us-west-2",
    ) -> TestFabric:
        """
        Create a test fabric.
        
        Args:
            name: Fabric name (auto-generated if None)
            description: Fabric description
            region: AWS region
        
        Returns:
            TestFabric object
        """
        if name is None:
            name = random_name("test-fabric")
        
        result = self.cli.fabric_create(
            name=name,
            description=description,
            region=region,
        )
        result.assert_success()
        
        fabric_id = result.get_json_value("fabric.id")
        operation_id = result.get_json_value("operation_id")
        
        if not fabric_id:
            raise ValueError("No fabric ID in create response")
        
        fabric = TestFabric(
            id=fabric_id,
            name=name,
            description=description,
            operation_id=operation_id,
        )
        self.fabrics.append(fabric)
        
        return fabric
    
    def create_cluster(
        self,
        fabric_id: str,
        name: Optional[str] = None,
        description: str = "Test cluster",
    ) -> TestCluster:
        """
        Create a test cluster.
        
        Args:
            fabric_id: Parent fabric ID
            name: Cluster name (auto-generated if None)
            description: Cluster description
        
        Returns:
            TestCluster object
        """
        if name is None:
            name = random_name("test-cluster")
        
        result = self.cli.run_json(
            "cluster", "create", name,
            "--fabric-id", fabric_id,
            "--description", description,
        )
        result.assert_success()
        
        cluster_id = result.get_json_value("cluster.id")
        operation_id = result.get_json_value("operation_id")
        
        if not cluster_id:
            raise ValueError("No cluster ID in create response")
        
        cluster = TestCluster(
            id=cluster_id,
            name=name,
            fabric_id=fabric_id,
            operation_id=operation_id,
        )
        self.clusters.append(cluster)
        
        return cluster
    
    def create_component(
        self,
        cluster_id: str,
        name: Optional[str] = None,
        component_type: str = "terraform-cloud",
        description: str = "Test component",
    ) -> TestComponent:
        """
        Create a test component.
        
        Args:
            cluster_id: Parent cluster ID
            name: Component name (auto-generated if None)
            component_type: Component type
            description: Component description
        
        Returns:
            TestComponent object
        """
        if name is None:
            name = random_name("test-component")
        
        result = self.cli.run_json(
            "component", "create", name,
            "--cluster-id", cluster_id,
            "--type", component_type,
            "--description", description,
        )
        result.assert_success()
        
        component_id = result.get_json_value("component.id")
        operation_id = result.get_json_value("operation_id")
        
        if not component_id:
            raise ValueError("No component ID in create response")
        
        component = TestComponent(
            id=component_id,
            name=name,
            cluster_id=cluster_id,
            type=component_type,
            operation_id=operation_id,
        )
        self.components.append(component)
        
        return component
    
    def cleanup(self, verbose: bool = True) -> None:
        """
        Clean up all created resources.
        
        Args:
            verbose: Print cleanup progress
        """
        # Clean up in reverse order: components -> clusters -> fabrics
        
        if verbose and self.components:
            print(f"\nCleaning up {len(self.components)} test components...")
        
        for component in self.components:
            try:
                if verbose:
                    print(f"  Deleting component: {component.id}")
                self.cli.run("component", "delete", component.id)
            except Exception as e:
                if verbose:
                    print(f"  ⚠ Failed to delete component {component.id}: {e}")
        
        if verbose and self.clusters:
            print(f"\nCleaning up {len(self.clusters)} test clusters...")
        
        for cluster in self.clusters:
            try:
                if verbose:
                    print(f"  Deleting cluster: {cluster.id}")
                self.cli.run("cluster", "delete", cluster.id)
            except Exception as e:
                if verbose:
                    print(f"  ⚠ Failed to delete cluster {cluster.id}: {e}")
        
        if verbose and self.fabrics:
            print(f"\nCleaning up {len(self.fabrics)} test fabrics...")
        
        for fabric in self.fabrics:
            try:
                if verbose:
                    print(f"  Deleting fabric: {fabric.id}")
                self.cli.fabric_delete(fabric.id)
            except Exception as e:
                if verbose:
                    print(f"  ⚠ Failed to delete fabric {fabric.id}: {e}")
        
        # Clear lists
        self.components.clear()
        self.clusters.clear()
        self.fabrics.clear()
        
        if verbose:
            print("\n✓ Cleanup complete")
