"""
Health check utilities for AGF services.

Checks if required services (API server, PostgreSQL, Temporal) are running.
"""

import socket
import subprocess
import time
from dataclasses import dataclass
from typing import List, Optional
import psycopg2


@dataclass
class ServiceHealth:
    """Health status of a service."""
    
    name: str
    healthy: bool
    message: str
    details: Optional[str] = None


class HealthChecker:
    """Check health of AGF infrastructure services."""
    
    def __init__(
        self,
        api_host: str = "localhost",
        api_port: int = 28080,
        postgres_host: str = "localhost",
        postgres_port: int = 15432,
        postgres_user: str = "agf_user",
        postgres_password: str = "agf_password",
        postgres_db: str = "agf_dev",
        temporal_host: str = "localhost",
        temporal_port: int = 7233,
    ):
        """Initialize health checker with service endpoints."""
        self.api_host = api_host
        self.api_port = api_port
        self.postgres_host = postgres_host
        self.postgres_port = postgres_port
        self.postgres_user = postgres_user
        self.postgres_password = postgres_password
        self.postgres_db = postgres_db
        self.temporal_host = temporal_host
        self.temporal_port = temporal_port
    
    def check_port(self, host: str, port: int, timeout: float = 1.0) -> bool:
        """Check if a port is open and accepting connections."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except socket.error:
            return False
    
    def check_api_server(self) -> ServiceHealth:
        """Check if AGF API server is running."""
        if self.check_port(self.api_host, self.api_port):
            return ServiceHealth(
                name="AGF API Server",
                healthy=True,
                message=f"Running on {self.api_host}:{self.api_port}",
            )
        return ServiceHealth(
            name="AGF API Server",
            healthy=False,
            message=f"Not running on {self.api_host}:{self.api_port}",
            details="Start with: make server/start",
        )
    
    def check_postgres(self) -> ServiceHealth:
        """Check if PostgreSQL is running and accessible."""
        if not self.check_port(self.postgres_host, self.postgres_port):
            return ServiceHealth(
                name="PostgreSQL",
                healthy=False,
                message=f"Not running on {self.postgres_host}:{self.postgres_port}",
                details="Start with: docker-compose -f compose/postgres.yaml up",
            )
        
        # Try to connect
        try:
            conn = psycopg2.connect(
                host=self.postgres_host,
                port=self.postgres_port,
                user=self.postgres_user,
                password=self.postgres_password,
                database=self.postgres_db,
                connect_timeout=2,
            )
            conn.close()
            return ServiceHealth(
                name="PostgreSQL",
                healthy=True,
                message=f"Running on {self.postgres_host}:{self.postgres_port}",
            )
        except Exception as e:
            return ServiceHealth(
                name="PostgreSQL",
                healthy=False,
                message="Running but not accessible",
                details=str(e),
            )
    
    def check_temporal(self) -> ServiceHealth:
        """Check if Temporal server is running."""
        if self.check_port(self.temporal_host, self.temporal_port):
            return ServiceHealth(
                name="Temporal",
                healthy=True,
                message=f"Running on {self.temporal_host}:{self.temporal_port}",
            )
        return ServiceHealth(
            name="Temporal",
            healthy=False,
            message=f"Not running on {self.temporal_host}:{self.temporal_port}",
            details="Start with: temporal server start-dev",
        )
    
    def check_temporal_worker(self) -> ServiceHealth:
        """Check if Temporal worker is running."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "temporal-worker"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return ServiceHealth(
                    name="Temporal Worker",
                    healthy=True,
                    message="Running",
                )
        except Exception:
            pass
        
        return ServiceHealth(
            name="Temporal Worker",
            healthy=False,
            message="Not running",
            details="Start with: ./bin/temporal-worker",
        )
    
    def check_all(self) -> List[ServiceHealth]:
        """Check all services."""
        return [
            self.check_api_server(),
            self.check_postgres(),
            self.check_temporal(),
            self.check_temporal_worker(),
        ]
    
    def wait_for_service(
        self,
        host: str,
        port: int,
        timeout: float = 30.0,
        interval: float = 1.0,
    ) -> bool:
        """
        Wait for a service to become available.
        
        Args:
            host: Service host
            port: Service port
            timeout: Maximum wait time in seconds
            interval: Check interval in seconds
        
        Returns:
            True if service became available, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.check_port(host, port, timeout=1.0):
                return True
            time.sleep(interval)
        
        return False
    
    def wait_for_all(self, timeout: float = 60.0) -> bool:
        """
        Wait for all required services to become available.
        
        Returns:
            True if all services are available, False if timeout
        """
        services = [
            (self.api_host, self.api_port, "API Server"),
            (self.postgres_host, self.postgres_port, "PostgreSQL"),
            (self.temporal_host, self.temporal_port, "Temporal"),
        ]
        
        for host, port, name in services:
            print(f"Waiting for {name}...")
            if not self.wait_for_service(host, port, timeout=timeout):
                print(f"✗ {name} did not become available")
                return False
            print(f"✓ {name} is available")
        
        return True
    
    def print_status(self) -> bool:
        """
        Print health status of all services.
        
        Returns:
            True if all services are healthy, False otherwise
        """
        print("\n🔍 Service Health Check\n")
        
        all_healthy = True
        for health in self.check_all():
            status = "✓" if health.healthy else "✗"
            print(f"  {status} {health.name}: {health.message}")
            if health.details:
                print(f"    {health.details}")
            
            if not health.healthy:
                all_healthy = False
        
        print()
        return all_healthy
