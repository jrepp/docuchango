"""
AGF Testing Framework

A comprehensive Python testing library for AGF Portal integration and E2E tests.

Modules:
- cli: AGF CLI command execution and result handling
- grpc: gRPC client wrappers for AGF services
- docker: Docker Compose environment management
- assertions: Custom assertions for AGF testing
- fixtures: Reusable test data factories
- health: Service health checks
"""

__version__ = "0.1.0"

from .assertions import AGFAssertions
from .cli import AGFCLIRunner, CLIResult
from .health import HealthChecker

__all__ = [
    "AGFCLIRunner",
    "CLIResult",
    "AGFAssertions",
    "HealthChecker",
]
