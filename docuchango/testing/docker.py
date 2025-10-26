"""
Docker Compose environment management for AGF testing.

Handles starting/stopping Docker Compose services for tests.
"""

import subprocess
import time
from pathlib import Path
from typing import Optional


class DockerComposeManager:
    """Manage Docker Compose environments for testing."""

    def __init__(self, compose_file: Optional[Path] = None, project_name: str = "agf-test"):
        """
        Initialize Docker Compose manager.

        Args:
            compose_file: Path to docker-compose.yml (defaults to testing/docker-compose.yml)
            project_name: Docker Compose project name
        """
        if compose_file is None:
            project_root = Path(__file__).parent.parent.parent
            compose_file = project_root / "testing" / "docker-compose.yml"

        self.compose_file = Path(compose_file)
        self.project_name = project_name

        if not self.compose_file.exists():
            raise FileNotFoundError(f"Compose file not found: {self.compose_file}")

    def _run_command(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        """Run a docker compose command."""
        cmd = ["docker", "compose", "-f", str(self.compose_file), "-p", self.project_name, *args]

        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check,
        )

    def up(self, services: Optional[list[str]] = None, detach: bool = True, wait: int = 10) -> None:
        """
        Start Docker Compose services.

        Args:
            services: Specific services to start (None for all)
            detach: Run in background
            wait: Seconds to wait after starting
        """
        args = ["up"]
        if detach:
            args.append("-d")

        if services:
            args.extend(services)

        print("Starting Docker Compose services...")
        result = self._run_command(*args)

        if result.returncode != 0:
            raise RuntimeError(f"Failed to start services:\n{result.stderr}")

        if wait > 0:
            print(f"Waiting {wait}s for services to initialize...")
            time.sleep(wait)

    def down(self, volumes: bool = False, remove_orphans: bool = True) -> None:
        """
        Stop and remove Docker Compose services.

        Args:
            volumes: Remove named volumes
            remove_orphans: Remove containers for services not in compose file
        """
        args = ["down"]
        if volumes:
            args.append("--volumes")
        if remove_orphans:
            args.append("--remove-orphans")

        print("Stopping Docker Compose services...")
        self._run_command(*args, check=False)

    def ps(self) -> list[str]:
        """
        List running services.

        Returns:
            List of running service names
        """
        result = self._run_command("ps", "--services", "--filter", "status=running", check=False)

        if result.returncode != 0:
            return []

        return [line.strip() for line in result.stdout.split("\n") if line.strip()]

    def is_running(self, service: Optional[str] = None) -> bool:
        """
        Check if services are running.

        Args:
            service: Specific service to check (None for any service)

        Returns:
            True if service(s) are running
        """
        running = self.ps()

        if service:
            return service in running

        return len(running) > 0

    def logs(self, service: Optional[str] = None, tail: int = 100) -> str:
        """
        Get logs from services.

        Args:
            service: Specific service (None for all)
            tail: Number of lines to show

        Returns:
            Log output
        """
        args = ["logs", "--tail", str(tail)]
        if service:
            args.append(service)

        result = self._run_command(*args, check=False)
        return result.stdout

    def exec(self, service: str, command: list[str]) -> subprocess.CompletedProcess:
        """
        Execute a command in a running service container.

        Args:
            service: Service name
            command: Command to execute

        Returns:
            Completed process result
        """
        args = ["exec", "-T", service, *command]
        return self._run_command(*args, check=False)

    def restart(self, service: Optional[str] = None) -> None:
        """
        Restart services.

        Args:
            service: Specific service to restart (None for all)
        """
        args = ["restart"]
        if service:
            args.append(service)

        self._run_command(*args)


class DockerContainerManager:
    """Manage individual Docker containers (without Compose)."""

    @staticmethod
    def is_running(container_name: str) -> bool:
        """Check if a container is running."""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    f"name={container_name}",
                    "--filter",
                    "status=running",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return container_name in result.stdout
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def stop(container_name: str) -> None:
        """Stop a container."""
        subprocess.run(
            ["docker", "stop", container_name],
            capture_output=True,
            check=False,
        )

    @staticmethod
    def remove(container_name: str, force: bool = True) -> None:
        """Remove a container."""
        args = ["docker", "rm"]
        if force:
            args.append("-f")
        args.append(container_name)

        subprocess.run(args, capture_output=True, check=False)

    @staticmethod
    def logs(container_name: str, tail: int = 100) -> str:
        """Get container logs."""
        result = subprocess.run(
            ["docker", "logs", "--tail", str(tail), container_name],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout
