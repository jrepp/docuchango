"""
CLI execution module for AGF testing.

Provides utilities to run AGF CLI commands, capture output, and parse results.
"""

import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import shlex


@dataclass
class CLIResult:
    """Result of a CLI command execution."""
    
    stdout: str
    stderr: str
    exit_code: int
    duration: float
    command: List[str]
    error: Optional[Exception] = None
    json_output: Optional[Dict[str, Any]] = None
    
    @property
    def success(self) -> bool:
        """Check if command succeeded."""
        return self.exit_code == 0 and self.error is None
    
    def assert_success(self) -> None:
        """Assert that command succeeded."""
        if not self.success:
            raise AssertionError(
                f"Command failed with exit code {self.exit_code}\n"
                f"Command: {' '.join(self.command)}\n"
                f"Stderr: {self.stderr}\n"
                f"Error: {self.error}"
            )
    
    def assert_contains(self, text: str) -> None:
        """Assert that stdout contains text."""
        if text not in self.stdout:
            raise AssertionError(
                f"Expected stdout to contain '{text}'\n"
                f"Stdout: {self.stdout}"
            )
    
    def assert_not_contains(self, text: str) -> None:
        """Assert that stdout does not contain text."""
        if text in self.stdout:
            raise AssertionError(
                f"Expected stdout to not contain '{text}'\n"
                f"Stdout: {self.stdout}"
            )
    
    def get_json_value(self, path: str) -> Any:
        """
        Get value from JSON output using dot notation.
        
        Example: result.get_json_value("fabric.id")
        """
        if not self.json_output:
            raise ValueError("No JSON output available")
        
        keys = path.split(".")
        value = self.json_output
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
            
            if value is None:
                return None
        
        return value


class AGFCLIRunner:
    """
    AGF CLI command runner with configurable defaults.
    
    Handles building the CLI binary, setting up environment,
    and executing commands with proper flags.
    """
    
    def __init__(
        self,
        binary_path: Optional[Path] = None,
        server: str = "localhost:28080",
        org_id: str = "org-test-default",
        project_id: str = "proj-test-default",
        insecure: bool = True,
        timeout: float = 60.0,
        auto_build: bool = True,
    ):
        """
        Initialize CLI runner.
        
        Args:
            binary_path: Path to AGF binary (will auto-build if None)
            server: AGF API server address
            org_id: Default organization ID
            project_id: Default project ID
            insecure: Skip TLS verification
            timeout: Command timeout in seconds
            auto_build: Automatically build binary if missing
        """
        self.server = server
        self.org_id = org_id
        self.project_id = project_id
        self.insecure = insecure
        self.timeout = timeout
        
        if binary_path is None:
            project_root = Path(__file__).parent.parent.parent
            binary_path = project_root / "bin" / "agf"
        
        self.binary_path = Path(binary_path)
        
        if auto_build and not self.binary_path.exists():
            self._build_binary()
    
    def _build_binary(self) -> None:
        """Build the AGF CLI binary."""
        project_root = self.binary_path.parent.parent
        
        print(f"Building AGF CLI binary...")
        result = subprocess.run(
            ["make", "agf/build"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to build AGF CLI:\n{result.stderr}"
            )
        
        if not self.binary_path.exists():
            raise RuntimeError(
                f"Build succeeded but binary not found at {self.binary_path}"
            )
        
        print(f"✓ AGF CLI built successfully: {self.binary_path}")
    
    def run(
        self,
        *args: str,
        org_id: Optional[str] = None,
        project_id: Optional[str] = None,
        server: Optional[str] = None,
        output_json: bool = False,
        timeout: Optional[float] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> CLIResult:
        """
        Run an AGF CLI command.
        
        Args:
            *args: Command arguments (e.g., "fabric", "create", "my-fabric")
            org_id: Override default org ID
            project_id: Override default project ID
            server: Override default server
            output_json: Add --output json flag
            timeout: Override default timeout
            env: Additional environment variables
        
        Returns:
            CLIResult with command output and metadata
        """
        # Build command
        cmd = [str(self.binary_path)]
        
        # Add global flags
        cmd.extend(["--server", server or self.server])
        cmd.extend(["--org-id", org_id or self.org_id])
        cmd.extend(["--project-id", project_id or self.project_id])
        
        if self.insecure:
            cmd.append("--insecure")
        
        # Add command args
        cmd.extend(args)
        
        # Add output format
        if output_json:
            cmd.extend(["--output", "json"])
        
        # Setup environment
        run_env = dict(env or {})
        
        # Execute command
        start_time = time.time()
        error = None
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
                env={**subprocess.os.environ, **run_env},
            )
            stdout = result.stdout
            stderr = result.stderr
            exit_code = result.returncode
        except subprocess.TimeoutExpired as e:
            stdout = e.stdout.decode() if e.stdout else ""
            stderr = e.stderr.decode() if e.stderr else ""
            exit_code = -1
            error = e
        except Exception as e:
            stdout = ""
            stderr = str(e)
            exit_code = -1
            error = e
        
        duration = time.time() - start_time
        
        # Parse JSON output if requested
        json_output = None
        if output_json and exit_code == 0:
            try:
                json_output = json.loads(stdout)
            except json.JSONDecodeError:
                # Not valid JSON, ignore
                pass
        
        return CLIResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            duration=duration,
            command=cmd,
            error=error,
            json_output=json_output,
        )
    
    def run_json(self, *args: str, **kwargs) -> CLIResult:
        """Run command with JSON output."""
        return self.run(*args, output_json=True, **kwargs)
    
    def fabric_create(
        self,
        name: str,
        description: str = "",
        region: str = "us-west-2",
        **kwargs
    ) -> CLIResult:
        """Create a fabric."""
        cmd = ["fabric", "create", name]
        if description:
            cmd.extend(["--description", description])
        if region:
            cmd.extend(["--region", region])
        return self.run_json(*cmd, **kwargs)
    
    def fabric_get(self, fabric_id: str, **kwargs) -> CLIResult:
        """Get fabric details."""
        return self.run_json("fabric", "get", fabric_id, **kwargs)
    
    def fabric_list(self, **kwargs) -> CLIResult:
        """List fabrics."""
        return self.run_json("fabric", "list", **kwargs)
    
    def fabric_update(
        self,
        fabric_id: str,
        description: Optional[str] = None,
        **kwargs
    ) -> CLIResult:
        """Update a fabric."""
        cmd = ["fabric", "update", fabric_id]
        if description is not None:
            cmd.extend(["--description", description])
        return self.run_json(*cmd, **kwargs)
    
    def fabric_delete(self, fabric_id: str, **kwargs) -> CLIResult:
        """Delete a fabric."""
        return self.run_json("fabric", "delete", fabric_id, **kwargs)
    
    def operation_get(self, operation_id: str, **kwargs) -> CLIResult:
        """Get operation status."""
        return self.run_json("operation", "get", operation_id, **kwargs)
    
    def operation_wait(
        self,
        operation_id: str,
        timeout: str = "5m",
        interval: str = "2s",
        **kwargs
    ) -> CLIResult:
        """Wait for operation to complete."""
        return self.run(
            "operation", "wait", operation_id,
            "--timeout", timeout,
            "--interval", interval,
            **kwargs
        )
