# !/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
PM2 Python Library - Professional Process Management
=====================================================

A comprehensive, production-ready Python wrapper for PM2 (Process Manager 2).
Provides both synchronous and asynchronous interfaces for managing Node.js and
Python applications with PM2.

Features:
    - 🚀 Full PM2 API coverage (start, stop, restart, delete, reload, etc.)
    - ⚡ Both sync and async support
    - 📊 Real-time process monitoring and metrics
    - 🔧 Advanced configuration management
    - 📝 Comprehensive logging support
    - 🛡️ Robust error handling with custom exceptions
    - 🎯 Type hints for better IDE support
    - 🧪 Extensive test coverage

Quick Start:
    ```python
    from pm2 import PM2Manager

    # Synchronous usage
    pm2 = PM2Manager()
    app = pm2.start_app("app.js", name="my-app", instances=4)
    print(f"Started {app.name} with {app.instances} instances")

    # Asynchronous usage
    import asyncio

    async def main():
        async with PM2Manager() as pm2:
            app = await pm2.start_app("app.py", name="python-app")
            metrics = await pm2.get_metrics(app.name)
            print(f"CPU: {metrics.cpu}%, Memory: {metrics.memory}MB")

    asyncio.run(main())
    ```

Author: y4kupkaya
License: MIT
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable, AsyncGenerator, Generator
import warnings

# Import aiofiles only if available
try:
    import aiofiles

    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False
    warnings.warn(
        "aiofiles not available. Async file operations will use sync fallbacks."
    )

__version__ = "1.0.0"
__author__ = "y4kupkaya"
__email__ = "contact@yakupkaya.me"
__license__ = "GNU General Public License v3 (GPLv3)"

# Configure logging
logger = logging.getLogger(__name__)


# Enums for better type safety
class ProcessStatus(Enum):
    """PM2 process status enumeration.

    Represents all possible states that a PM2 process can be in during its lifecycle.
    These statuses are returned by PM2 daemon and reflect the current operational
    state of managed processes.

    Attributes:
        ONLINE: Process is running and operational
        STOPPING: Process is in the process of stopping
        STOPPED: Process is not running
        LAUNCHING: Process is starting up
        ERRORED: Process has encountered an error and stopped
        ONE_LAUNCH_STATUS: Process is configured to run only once

    Example:
        >>> process = pm2.get_process("my-app")
        >>> if process.status == ProcessStatus.ONLINE:
        ...     print("Process is running")
    """

    ONLINE = "online"  # Process is running and operational
    STOPPING = "stopping"  # Process is in the process of stopping
    STOPPED = "stopped"  # Process is not running
    LAUNCHING = "launching"  # Process is starting up
    ERRORED = "errored"  # Process has encountered an error
    ONE_LAUNCH_STATUS = "one-launch-status"  # Process runs only once


class ProcessMode(Enum):
    """PM2 process execution modes.

    Defines how PM2 should execute and manage the application process.
    Each mode has different characteristics and use cases.

    Attributes:
        FORK: Process runs in fork mode (single instance)
        CLUSTER: Process runs in cluster mode (multiple instances with load balancing)

    Notes:
        - FORK mode is suitable for most applications and non-HTTP processes
        - CLUSTER mode is ideal for HTTP servers to utilize multiple CPU cores
        - CLUSTER mode automatically load balances requests across instances

    Example:
        >>> config = ProcessConfiguration(
        ...     name="web-server",
        ...     script="app.js",
        ...     exec_mode=ProcessMode.CLUSTER,
        ...     instances=4
        ... )
    """

    FORK = "fork"  # Single instance mode
    CLUSTER = "cluster"  # Multi-instance cluster mode with load balancing


class LogLevel(Enum):
    """Logging levels for PM2 processes.

    Defines the verbosity level for logging output. Higher levels include
    all messages from lower levels.

    Attributes:
        ERROR: Only error messages
        WARN: Warning and error messages
        INFO: Informational, warning, and error messages
        VERBOSE: Detailed operational information
        DEBUG: All messages including debug information
        SILENT: No logging output

    Example:
        >>> pm2_logger.set_level(LogLevel.DEBUG)
        >>> # All messages will be logged
    """

    ERROR = "error"  # Only error messages
    WARN = "warn"  # Warning and error messages
    INFO = "info"  # Informational, warning, and error messages
    VERBOSE = "verbose"  # Detailed operational information
    DEBUG = "debug"  # All messages including debug information
    SILENT = "silent"  # No logging output


# Exception Hierarchy
class PM2Error(Exception):
    """Base exception for all PM2-related errors.

    This is the root exception class for all PM2-specific errors. It provides
    enhanced error information including timestamps and additional details.
    All other PM2 exceptions inherit from this class.

    Attributes:
        message (str): The error message
        details (Dict): Additional error details and context
        timestamp (datetime): When the error occurred

    Args:
        message (str): The error message describing what went wrong
        details (Optional[Dict]): Additional context about the error

    Example:
        >>> try:
        ...     pm2.start_app("nonexistent.js")
        ... except PM2Error as e:
        ...     print(f"PM2 Error: {e.message}")
        ...     print(f"Occurred at: {e.timestamp}")
        ...     if e.details:
        ...         print(f"Details: {e.details}")
    """

    def __init__(self, message: str, details: Optional[Dict] = None):
        """Initialize PM2Error with message and optional details.

        Args:
            message (str): The error message
            details (Optional[Dict]): Additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()

    def __str__(self) -> str:
        """Return string representation of the error.

        Returns:
            str: Formatted error message with details if available
        """
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class PM2ConnectionError(PM2Error):
    """Raised when PM2 daemon connection fails.

    This exception is raised when the library cannot establish communication
    with the PM2 daemon. Common causes include:
    - PM2 not installed on the system
    - PM2 daemon not running
    - PM2 binary not in PATH
    - Permission issues accessing PM2

    Example:
        >>> try:
        ...     pm2 = PM2Manager()
        ... except PM2ConnectionError as e:
        ...     print("Cannot connect to PM2:", e)
        ...     print("Make sure PM2 is installed: npm install -g pm2")
    """

    pass


class PM2CommandError(PM2Error):
    """Raised when PM2 command execution fails.

    This exception is raised when a PM2 command returns a non-zero exit code
    or fails to execute properly. It includes information about the failed
    command and exit code for debugging purposes.

    Attributes:
        command (List[str]): The PM2 command that failed
        exit_code (int): The exit code returned by the command

    Args:
        message (str): The error message
        command (List[str], optional): The command that failed
        exit_code (int, optional): The exit code from the failed command

    Example:
        >>> try:
        ...     pm2.start_app("invalid-script.js")
        ... except PM2CommandError as e:
        ...     print(f"Command failed: {' '.join(e.command)}")
        ...     print(f"Exit code: {e.exit_code}")
        ...     print(f"Error: {e.message}")
    """

    def __init__(self, message: str, command: List[str] = None, exit_code: int = None):
        """Initialize PM2CommandError with command details.

        Args:
            message (str): The error message
            command (List[str], optional): The failed command
            exit_code (int, optional): The command's exit code
        """
        super().__init__(message)
        self.command = command or []
        self.exit_code = exit_code


class PM2ProcessError(PM2Error):
    """Base class for process-related errors.

    This is the base exception class for all errors related to PM2 process
    management operations. Specific process errors inherit from this class.

    Common process-related errors include:
    - Process not found
    - Process already exists
    - Process in invalid state for operation
    - Process configuration errors

    Example:
        >>> try:
        ...     pm2.restart_process("nonexistent-app")
        ... except PM2ProcessError as e:
        ...     print(f"Process error: {e}")
    """

    pass


class PM2ProcessNotFoundError(PM2ProcessError):
    """Raised when a requested process is not found.

    This exception is raised when attempting to access a PM2 process that
    doesn't exist in the process list. The process can be searched by name,
    PID, or PM2 ID.

    Attributes:
        identifier (str): The identifier used to search for the process
        identifier_type (str): The type of identifier (name, pid, pm_id)

    Args:
        identifier (str): The process identifier that wasn't found
        identifier_type (str): The type of identifier used

    Example:
        >>> try:
        ...     process = pm2.get_process(name="missing-app")
        ... except PM2ProcessNotFoundError as e:
        ...     print(f"Process '{e.identifier}' not found")
        ...     print(f"Searched by: {e.identifier_type}")
        ...     # List available processes
        ...     processes = pm2.list_processes()
        ...     print(f"Available: {[p.name for p in processes]}")
    """

    def __init__(self, identifier: str, identifier_type: str = "name"):
        """Initialize PM2ProcessNotFoundError with identifier details.

        Args:
            identifier (str): The identifier that wasn't found
            identifier_type (str): Type of identifier (name, pid, pm_id)
        """
        message = f"Process not found with {identifier_type}='{identifier}'"
        super().__init__(message)
        self.identifier = identifier
        self.identifier_type = identifier_type


class PM2ProcessAlreadyExistsError(PM2ProcessError):
    """Raised when trying to start a process that already exists.

    This exception is raised when attempting to start a new process with
    a name that is already in use by another PM2 process. PM2 requires
    unique process names within the same namespace.

    Example:
        >>> try:
        ...     pm2.start_app("app.js", name="web-server")  # First time - OK
        ...     pm2.start_app("app2.js", name="web-server")  # Error!
        ... except PM2ProcessAlreadyExistsError as e:
        ...     print(f"Process name already in use: {e}")
        ...     # Use a different name or stop the existing process first
    """

    pass


class PM2ProcessInvalidStateError(PM2ProcessError):
    """Raised when process is in invalid state for requested operation.

    This exception is raised when attempting to perform an operation on a
    process that is not in the appropriate state. For example, trying to
    stop an already stopped process or restart a process that is launching.

    Example:
        >>> try:
        ...     process = pm2.get_process("my-app")
        ...     if process.status == ProcessStatus.STOPPED:
        ...         pm2.stop_process("my-app")  # Error!
        ... except PM2ProcessInvalidStateError as e:
        ...     print(f"Invalid operation: {e}")
        ...     print(f"Process is already stopped")
    """

    pass


class PM2ConfigurationError(PM2Error):
    """Raised when PM2 configuration is invalid.

    This exception is raised when there are issues with PM2 configuration
    files, ecosystem files, or process configuration parameters that prevent
    PM2 from operating correctly.

    Common causes:
    - Invalid JSON syntax in ecosystem.config.js
    - Missing required configuration fields
    - Invalid configuration values
    - Conflicting configuration settings

    Example:
        >>> try:
        ...     config = ProcessConfiguration(
        ...         name="",  # Empty name is invalid
        ...         script="app.js"
        ...     )
        ...     pm2.start_with_config(config)
        ... except PM2ConfigurationError as e:
        ...     print(f"Configuration error: {e}")
    """

    pass


class PM2ValidationError(PM2Error):
    """Raised when input validation fails.

    This exception is raised when method parameters or input data fail
    validation checks. It helps ensure that only valid data is passed
    to PM2 operations.

    Common validation failures:
    - Empty or None required parameters
    - Invalid parameter types
    - Parameters outside valid ranges
    - Malformed input data

    Example:
        >>> try:
        ...     pm2.get_process()  # No identifier provided
        ... except PM2ValidationError as e:
        ...     print(f"Validation error: {e}")
        ...     # Provide at least one identifier
        ...     process = pm2.get_process(name="my-app")
    """

    pass


class PathIsFolderError(PM2ValidationError):
    """Raised when a folder path is provided instead of a file path.

    This exception is raised when a directory path is provided where a
    file path is expected, such as when specifying a script to run with PM2.

    Example:
        >>> try:
        ...     pm2.start_app("/path/to/directory")  # Should be a file
        ... except PathIsFolderError as e:
        ...     print(f"Path error: {e}")
        ...     # Provide a specific file instead
        ...     pm2.start_app("/path/to/directory/app.js")
    """

    pass


# Data Models
@dataclass
class ProcessMetrics:
    """Process monitoring metrics and resource usage statistics.

    This class encapsulates real-time monitoring data for PM2 processes,
    including CPU usage, memory consumption, and heap statistics. Metrics
    are automatically updated when queried from PM2.

    Attributes:
        cpu (float): CPU usage percentage (0.0 to 100.0+)
        memory (int): Total memory usage in bytes
        heap_used (int): Used heap memory in bytes (Node.js processes)
        heap_total (int): Total heap memory allocated in bytes
        external (int): External memory usage in bytes
        rss (int): Resident Set Size memory in bytes

    Properties:
        memory_mb (float): Memory usage converted to megabytes
        heap_used_mb (float): Used heap memory converted to megabytes

    Example:
        >>> process = pm2.get_process("web-server")
        >>> metrics = process.metrics
        >>> print(f"CPU: {metrics.cpu}%")
        >>> print(f"Memory: {metrics.memory_mb:.1f} MB")
        >>> print(f"Heap: {metrics.heap_used_mb:.1f}/{metrics.heap_used_mb:.1f} MB")

        # Monitor resource usage over time
        >>> import time
        >>> for _ in range(5):
        ...     process = pm2.get_process("web-server")
        ...     print(f"CPU: {process.metrics.cpu:4.1f}% | "
        ...           f"Memory: {process.metrics.memory_mb:6.1f} MB")
        ...     time.sleep(1)
    """

    cpu: float = 0.0  # CPU usage percentage
    memory: int = 0  # Memory usage in bytes
    heap_used: int = 0  # Used heap memory in bytes
    heap_total: int = 0  # Total heap memory in bytes
    external: int = 0  # External memory usage in bytes
    rss: int = 0  # Resident Set Size memory in bytes

    @property
    def memory_mb(self) -> float:
        """Get memory usage converted to megabytes.

        Returns:
            float: Memory usage in MB (rounded to 2 decimal places)

        Example:
            >>> metrics = ProcessMetrics(memory=52428800)  # 50 MB in bytes
            >>> print(f"Memory: {metrics.memory_mb} MB")  # 50.0 MB
        """
        return round(self.memory / (1024 * 1024), 2)

    @property
    def heap_used_mb(self) -> float:
        """Get used heap memory converted to megabytes.

        Returns:
            float: Heap used in MB (rounded to 2 decimal places)

        Note:
            This is primarily relevant for Node.js processes. Python processes
            may not have meaningful heap statistics.

        Example:
            >>> metrics = ProcessMetrics(heap_used=25165824)  # 24 MB in bytes
            >>> print(f"Heap used: {metrics.heap_used_mb} MB")  # 24.0 MB
        """
        return round(self.heap_used / (1024 * 1024), 2)


@dataclass
class ProcessEnvironment:
    """Process environment configuration and variables management.

    This class manages environment variables and runtime context for PM2 processes.
    It supports setting custom variables, tracking runtime versions, and managing
    working directories and virtual environments.

    Attributes:
        variables (Dict[str, str]): Custom environment variables
        node_version (Optional[str]): Node.js version (if applicable)
        python_version (Optional[str]): Python version (if applicable)
        virtual_env (Optional[str]): Path to Python virtual environment
        working_directory (Optional[str]): Process working directory

    Example:
        >>> env = ProcessEnvironment()
        >>> env.set_var("NODE_ENV", "production")
        >>> env.set_var("PORT", "3000")
        >>> env.virtual_env = "/path/to/venv"
        >>>
        >>> config = ProcessConfiguration(
        ...     name="web-app",
        ...     script="app.py",
        ...     env=env
        ... )

        # Access environment variables from a running process
        >>> process = pm2.get_process("web-app")
        >>> port = process.environment.get_var("PORT", "8000")
        >>> print(f"App running on port: {port}")
    """

    variables: Dict[str, str] = field(default_factory=dict)
    node_version: Optional[str] = None
    python_version: Optional[str] = None
    virtual_env: Optional[str] = None
    working_directory: Optional[str] = None

    def set_var(self, key: str, value: str) -> None:
        """Set an environment variable.

        Args:
            key (str): The environment variable name
            value (str): The environment variable value

        Example:
            >>> env = ProcessEnvironment()
            >>> env.set_var("DATABASE_URL", "postgresql://localhost/mydb")
            >>> env.set_var("DEBUG", "true")
        """
        self.variables[key] = value

    def get_var(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get an environment variable value.

        Args:
            key (str): The environment variable name
            default (Optional[str]): Default value if variable not found

        Returns:
            Optional[str]: The variable value or default if not found

        Example:
            >>> env = ProcessEnvironment()
            >>> env.set_var("PORT", "3000")
            >>> port = env.get_var("PORT", "8000")  # Returns "3000"
            >>> host = env.get_var("HOST", "localhost")  # Returns "localhost"
        """
        return self.variables.get(key, default)


@dataclass
class ProcessConfiguration:
    """Advanced process configuration for PM2 applications.

    This class provides comprehensive configuration options for PM2 processes,
    including resource limits, logging settings, auto-restart behavior, and
    environment management. It supports all major PM2 configuration features.

    Attributes:
        name (str): Unique process name
        script (str): Path to the script file to execute
        args (List[str]): Command line arguments for the script
        instances (Union[int, str]): Number of instances (int) or 'max' for CPU count
        exec_mode (ProcessMode): Execution mode (fork or cluster)

        # Resource Management
        max_memory_restart (Optional[str]): Restart when memory exceeds limit (e.g., '150M')
        max_restarts (int): Maximum number of automatic restarts
        min_uptime (str): Minimum uptime before considering restart successful

        # Logging Configuration
        log_file (Optional[str]): Combined log file path
        out_file (Optional[str]): Stdout log file path
        error_file (Optional[str]): Stderr log file path
        log_date_format (str): Timestamp format for logs
        merge_logs (bool): Merge cluster logs into single files

        # Auto Restart Settings
        autorestart (bool): Enable automatic restart on crash
        watch (Union[bool, List[str]]): File watching for auto-restart
        ignore_watch (List[str]): Patterns to ignore when watching

        # Advanced Options
        source_map_support (bool): Enable source map support
        disable_source_map_support (bool): Explicitly disable source maps
        instance_var (str): Environment variable for instance ID
        pmx (bool): Enable PM2+ monitoring
        automation (bool): Enable PM2+ automation
        treekill (bool): Kill process tree on stop
        port (Optional[int]): Port number for the application

        # Environment Management
        env (ProcessEnvironment): Default environment variables
        env_production (Optional[ProcessEnvironment]): Production environment
        env_development (Optional[ProcessEnvironment]): Development environment

    Example:
        >>> # Basic configuration
        >>> config = ProcessConfiguration(
        ...     name="web-server",
        ...     script="app.js",
        ...     instances=4,
        ...     exec_mode=ProcessMode.CLUSTER
        ... )

        >>> # Advanced configuration with monitoring
        >>> env = ProcessEnvironment()
        >>> env.set_var("NODE_ENV", "production")
        >>> env.set_var("PORT", "3000")
        >>>
        >>> config = ProcessConfiguration(
        ...     name="production-app",
        ...     script="dist/server.js",
        ...     instances="max",  # Use all CPU cores
        ...     exec_mode=ProcessMode.CLUSTER,
        ...     max_memory_restart="500M",
        ...     max_restarts=10,
        ...     min_uptime="10s",
        ...     log_file="/var/log/app.log",
        ...     watch=["dist"],
        ...     ignore_watch=["node_modules", "logs"],
        ...     env=env
        ... )
        >>>
        >>> pm2_dict = config.to_dict()
    """

    name: str
    script: str
    args: List[str] = field(default_factory=list)
    instances: Union[int, str] = 1
    exec_mode: ProcessMode = ProcessMode.FORK

    # Resource limits
    max_memory_restart: Optional[str] = None
    max_restarts: int = 15
    min_uptime: str = "10s"

    # Logging
    log_file: Optional[str] = None
    out_file: Optional[str] = None
    error_file: Optional[str] = None
    log_date_format: str = "YYYY-MM-DD HH:mm:ss"
    merge_logs: bool = True

    # Auto restart
    autorestart: bool = True
    watch: Union[bool, List[str]] = False
    ignore_watch: List[str] = field(default_factory=lambda: ["node_modules", ".git"])

    # Advanced options
    source_map_support: bool = False
    disable_source_map_support: bool = False
    instance_var: str = "NODE_APP_INSTANCE"
    pmx: bool = True
    automation: bool = True
    treekill: bool = True
    port: Optional[int] = None

    # Environment
    env: ProcessEnvironment = field(default_factory=ProcessEnvironment)
    env_production: Optional[ProcessEnvironment] = None
    env_development: Optional[ProcessEnvironment] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to PM2 ecosystem format.

        Transforms the ProcessConfiguration object into a dictionary format
        that is compatible with PM2's ecosystem.config.js structure. This
        format can be used to generate PM2 configuration files or pass
        configuration directly to PM2 commands.

        Returns:
            Dict[str, Any]: PM2-compatible configuration dictionary with
            all non-None values included

        Example:
            >>> config = ProcessConfiguration(
            ...     name="web-server",
            ...     script="app.js",
            ...     instances=4,
            ...     exec_mode=ProcessMode.CLUSTER
            ... )
            >>> pm2_config = config.to_dict()
            >>> print(json.dumps(pm2_config, indent=2))
            {
              "name": "web-server",
              "script": "app.js",
              "instances": 4,
              "exec_mode": "cluster",
              ...
            }
        """
        config = {
            "name": self.name,
            "script": self.script,
            "args": self.args,
            "instances": self.instances,
            "exec_mode": self.exec_mode.value,
            "max_memory_restart": self.max_memory_restart,
            "max_restarts": self.max_restarts,
            "min_uptime": self.min_uptime,
            "autorestart": self.autorestart,
            "watch": self.watch,
            "ignore_watch": self.ignore_watch,
            "source_map_support": self.source_map_support,
            "disable_source_map_support": self.disable_source_map_support,
            "instance_var": self.instance_var,
            "pmx": self.pmx,
            "automation": self.automation,
            "treekill": self.treekill,
            "env": self.env.variables,
        }

        # Add optional fields
        if self.log_file:
            config["log_file"] = self.log_file
        if self.out_file:
            config["out_file"] = self.out_file
        if self.error_file:
            config["error_file"] = self.error_file
        if self.port:
            config["port"] = self.port
        if self.env_production:
            config["env_production"] = self.env_production.variables
        if self.env_development:
            config["env_development"] = self.env_development.variables

        return {k: v for k, v in config.items() if v is not None}


class PM2Process:
    """Enhanced PM2 process representation with advanced features.

    This class represents a PM2 process with comprehensive information about
    its current state, configuration, metrics, and runtime properties. It
    provides a rich interface for accessing all process-related data.

    The class automatically parses PM2's JSON output and provides convenient
    properties and methods for accessing process information. All timing
    information is converted to appropriate Python types, and metrics are
    structured for easy access.

    Attributes:
        name (str): Process name
        pid (Optional[int]): System process ID (None if stopped)
        pm_id (int): PM2 internal process ID
        namespace (str): PM2 namespace
        status (ProcessStatus): Current process status
        exec_mode (ProcessMode): Execution mode (fork/cluster)
        created_at (Optional[datetime]): When process was created
        pm_uptime (int): PM2 uptime timestamp
        uptime_seconds (int): Process uptime in seconds
        metrics (ProcessMetrics): Real-time process metrics
        restart_time (int): Number of times process has restarted
        autorestart (bool): Whether auto-restart is enabled
        max_restarts (int): Maximum allowed restarts
        min_uptime (str): Minimum uptime for successful restart
        user (str): User running the process
        working_directory (Optional[str]): Process working directory
        exec_path (Optional[str]): Path to executable
        environment (ProcessEnvironment): Process environment variables
        out_log_path (Optional[str]): Stdout log file path
        error_log_path (Optional[str]): Stderr log file path
        log_date_format (str): Log timestamp format
        instances (Union[int, str]): Number of instances
        watch (Union[bool, List[str]]): File watching configuration
        source_map_support (bool): Source map support enabled
        node_args (List[str]): Node.js arguments
        args (List[str]): Script arguments
        version (str): Application version
        node_version (Optional[str]): Node.js version

    Properties:
        is_online (bool): True if process is running
        is_stopped (bool): True if process is stopped
        uptime_human (str): Human-readable uptime
        memory_usage_human (str): Human-readable memory usage

    Example:
        >>> process = pm2.get_process("web-server")
        >>> print(f"Process: {process.name}")
        >>> print(f"Status: {process.status.value}")
        >>> print(f"PID: {process.pid}")
        >>> print(f"Uptime: {process.uptime_human}")
        >>> print(f"CPU: {process.metrics.cpu}%")
        >>> print(f"Memory: {process.memory_usage_human}")
        >>> print(f"Restarts: {process.restart_time}")
        >>>
        >>> # Check if process needs attention
        >>> if not process.is_online:
        ...     print(f"Process is {process.status.value}")
        >>> if process.metrics.cpu > 80:
        ...     print("High CPU usage detected")
        >>> if process.restart_time > 5:
        ...     print("Process has restarted multiple times")
    """

    def __init__(self, json_data: Dict[str, Any]) -> None:
        """Initialize PM2Process from PM2 JSON data.

        Args:
            json_data (Dict[str, Any]): Raw JSON data from PM2 list command

        Raises:
            PM2ValidationError: If json_data is not a dict or missing required fields

        Example:
            >>> # Usually called internally by PM2Manager
            >>> raw_data = {"name": "app", "pm2_env": {...}, "monit": {...}}
            >>> process = PM2Process(raw_data)
        """
        if not isinstance(json_data, dict):
            raise PM2ValidationError("Process data must be a dictionary")

        if "name" not in json_data:
            raise PM2ValidationError("Process data missing required 'name' field")

        self._raw_data = json_data
        self.pm2_env = json_data.get("pm2_env", {})  # Add direct access to pm2_env
        self._parse_process_data()

    def _parse_process_data(self) -> None:
        """Parse PM2 JSON data into structured attributes.

        This method extracts and processes all relevant information from the
        raw PM2 JSON data, converting timestamps, parsing metrics, and
        organizing data into convenient attributes.

        The parsing handles missing or malformed data gracefully, providing
        sensible defaults where appropriate.
        """
        data = self._raw_data
        pm2_env = data.get("pm2_env", {})

        # Basic process information
        self.name: str = data["name"]
        self.pid: Optional[int] = data.get("pid")
        self.pm_id: int = data.get("pm_id", 0)
        self.namespace: str = pm2_env.get("namespace", "default")

        # Status and lifecycle
        try:
            self.status = ProcessStatus(pm2_env.get("status", "stopped"))
        except ValueError:
            self.status = ProcessStatus.STOPPED

        try:
            self.exec_mode = ProcessMode(pm2_env.get("exec_mode", "fork"))
        except ValueError:
            self.exec_mode = ProcessMode.FORK

        # Timing information
        self.created_at = self._parse_timestamp(pm2_env.get("created_at"))
        self.pm_uptime = pm2_env.get("pm_uptime", 0)
        self.uptime_seconds = self._calculate_uptime()

        # Process metrics
        monit_data = data.get("monit", {})
        self.metrics = ProcessMetrics(
            cpu=float(monit_data.get("cpu", 0)),
            memory=int(monit_data.get("memory", 0)),
            heap_used=int(monit_data.get("heap_used", 0)),
            heap_total=int(monit_data.get("heap_total", 0)),
            external=int(monit_data.get("external", 0)),
            rss=int(monit_data.get("rss", 0)),
        )

        # Restart and reliability
        self.restart_time: int = pm2_env.get("restart_time", 0)
        self.autorestart: bool = pm2_env.get("autorestart", True)
        self.max_restarts: int = pm2_env.get("max_restarts", 15)
        self.min_uptime: str = pm2_env.get("min_uptime", "1000")

        # User and environment
        self.user: str = pm2_env.get("username", "")
        self.working_directory: Optional[str] = pm2_env.get("pm_cwd")
        self.exec_path: Optional[str] = pm2_env.get("pm_exec_path")

        # Environment variables
        env_vars = pm2_env.get("env", {})
        self.environment = ProcessEnvironment(
            variables=env_vars,
            virtual_env=env_vars.get("VIRTUAL_ENV"),
            working_directory=self.working_directory,
        )

        # Logging
        self.out_log_path: Optional[str] = pm2_env.get("pm_out_log_path")
        self.error_log_path: Optional[str] = pm2_env.get("pm_err_log_path")
        self.log_date_format: str = pm2_env.get(
            "log_date_format", "YYYY-MM-DD HH:mm:ss"
        )

        # Advanced settings
        self.instances: Union[int, str] = pm2_env.get("instances", 1)
        self.watch: Union[bool, List[str]] = pm2_env.get("watch", False)
        self.source_map_support: bool = pm2_env.get("source_map_support", False)
        self.node_args: List[str] = pm2_env.get("node_args", [])
        self.args: List[str] = pm2_env.get("args", [])

        # Version info
        self.version: str = pm2_env.get("version", "N/A")
        self.node_version: Optional[str] = pm2_env.get("node_version")

    def _parse_timestamp(
        self, timestamp: Optional[Union[int, str]]
    ) -> Optional[datetime]:
        """Parse PM2 timestamp to datetime object.

        PM2 timestamps are typically in milliseconds since epoch.
        This method safely converts them to Python datetime objects.

        Args:
            timestamp: PM2 timestamp (int or str, in milliseconds)

        Returns:
            Optional[datetime]: Parsed datetime or None if invalid
        """
        if not timestamp:
            return None
        try:
            if isinstance(timestamp, str):
                timestamp = int(timestamp)
            return datetime.fromtimestamp(timestamp / 1000)
        except (ValueError, TypeError):
            return None

    def _calculate_uptime(self) -> int:
        """Calculate process uptime in seconds.

        Calculates how long the process has been running based on PM2's
        uptime timestamp. Returns 0 for stopped or non-online processes.

        Returns:
            int: Process uptime in seconds, or 0 if not running
        """
        if not self.pm_uptime or self.status != ProcessStatus.ONLINE:
            return 0
        return int(time.time() - (self.pm_uptime / 1000))

    @property
    def is_online(self) -> bool:
        """Check if process is currently online and running.

        Returns:
            bool: True if process status is ONLINE, False otherwise

        Example:
            >>> process = pm2.get_process("web-server")
            >>> if process.is_online:
            ...     print(f"{process.name} is running with PID {process.pid}")
            ... else:
            ...     print(f"{process.name} is not running")
        """
        return self.status == ProcessStatus.ONLINE

    @property
    def is_stopped(self) -> bool:
        """Check if process is currently stopped.

        Returns:
            bool: True if process status is STOPPED, False otherwise

        Example:
            >>> process = pm2.get_process("web-server")
            >>> if process.is_stopped:
            ...     print(f"{process.name} is stopped, starting...")
            ...     pm2.start_process(process.name)
        """
        return self.status == ProcessStatus.STOPPED

    @property
    def uptime_human(self) -> str:
        """Get human-readable uptime string.

        Converts the process uptime into a readable format with days, hours,
        minutes, and seconds as appropriate.

        Returns:
            str: Human-readable uptime (e.g., "2d 3h 45m 12s", "1h 30m", "45s")

        Example:
            >>> process = pm2.get_process("web-server")
            >>> print(f"Uptime: {process.uptime_human}")
            # Output: "Uptime: 1d 5h 32m 18s"

            >>> # For monitoring dashboard
            >>> processes = pm2.list_processes()
            >>> for proc in processes:
            ...     status = "🟢" if proc.is_online else "🔴"
            ...     print(f"{status} {proc.name:15} {proc.uptime_human:>12}")
        """
        if self.uptime_seconds <= 0:
            return "0s"

        uptime = timedelta(seconds=self.uptime_seconds)
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if seconds:
            parts.append(f"{seconds}s")

        return " ".join(parts) if parts else "0s"

    @property
    def memory_usage_human(self) -> str:
        """Get human-readable memory usage string.

        Converts memory usage from bytes to a readable format with appropriate
        units (MB or GB) and reasonable precision.

        Returns:
            str: Human-readable memory usage (e.g., "125.4 MB", "1.2 GB")

        Example:
            >>> process = pm2.get_process("web-server")
            >>> print(f"Memory: {process.memory_usage_human}")
            # Output: "Memory: 245.6 MB"

            >>> # Check for high memory usage
            >>> if process.metrics.memory_mb > 500:
            ...     print(f"⚠️  High memory usage: {process.memory_usage_human}")
        """
        if self.metrics.memory <= 0:
            return "0 MB"

        mb = self.metrics.memory_mb
        if mb >= 1024:
            return f"{mb/1024:.1f} GB"
        return f"{mb:.1f} MB"

    def get_environment_var(
        self, key: str, default: Optional[str] = None
    ) -> Optional[str]:
        """Get an environment variable value from the process.

        Args:
            key (str): Environment variable name
            default (Optional[str]): Default value if variable not found

        Returns:
            Optional[str]: Variable value or default if not found

        Example:
            >>> process = pm2.get_process("web-server")
            >>> node_env = process.get_environment_var("NODE_ENV", "development")
            >>> port = process.get_environment_var("PORT", "3000")
            >>> print(f"Running in {node_env} mode on port {port}")
        """
        return self.environment.get_var(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert process to dictionary representation.

        Creates a comprehensive dictionary containing all process information
        in a structured format. Useful for serialization, logging, or
        integration with other systems.

        Returns:
            Dict[str, Any]: Dictionary containing all process attributes

        Example:
            >>> process = pm2.get_process("web-server")
            >>> process_data = process.to_dict()
            >>> print(f"Process {process_data['name']} uses {process_data['memory_human']}")
            >>>
            >>> # Save to file for analysis
            >>> import json
            >>> with open("process_snapshot.json", "w") as f:
            ...     json.dump(process_data, f, indent=2)
        """
        return {
            "name": self.name,
            "pid": self.pid,
            "pm_id": self.pm_id,
            "status": self.status.value,
            "exec_mode": self.exec_mode.value,
            "instances": self.instances,
            "uptime": self.uptime_seconds,
            "uptime_human": self.uptime_human,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "restart_time": self.restart_time,
            "cpu": self.metrics.cpu,
            "memory": self.metrics.memory,
            "memory_human": self.memory_usage_human,
            "user": self.user,
            "working_directory": self.working_directory,
            "exec_path": self.exec_path,
            "out_log_path": self.out_log_path,
            "error_log_path": self.error_log_path,
            "environment": self.environment.variables,
            "virtual_env": self.environment.virtual_env,
            "autorestart": self.autorestart,
            "watch": self.watch,
            "version": self.version,
            "node_version": self.node_version,
            "args": self.args,
            "node_args": self.node_args,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert process to JSON string.

        Args:
            indent (int): JSON indentation level for pretty printing

        Returns:
            str: JSON string representation of the process

        Example:
            >>> process = pm2.get_process("web-server")
            >>> json_str = process.to_json(indent=4)
            >>> print(json_str)
            {
                "name": "web-server",
                "pid": 12345,
                "status": "online",
                ...
            }
        """
        return json.dumps(
            self.to_dict(), indent=indent, default=str, ensure_ascii=False
        )

    def __str__(self) -> str:
        """Return human-readable string representation.

        Returns:
            str: Formatted string with key process information
        """
        return (
            f"PM2Process(name='{self.name}', pid={self.pid}, "
            f"status={self.status.value}, uptime='{self.uptime_human}')"
        )

    def __repr__(self) -> str:
        """Return developer-friendly string representation.

        Returns:
            str: Detailed string representation for debugging
        """
        return f"<PM2Process {self.name} (PID:{self.pid}) ({self.status.value})>"


class PM2CommandExecutor:
    """Handles PM2 command execution with proper error handling and validation.

    This class provides a robust interface for executing PM2 commands with
    comprehensive error handling, timeout management, and validation. It
    supports both synchronous and asynchronous execution modes.

    The executor automatically validates PM2 installation and provides
    detailed error information when commands fail, including command
    context and exit codes.

    Attributes:
        pm2_binary (str): Path to the PM2 binary executable

    Example:
        >>> executor = PM2CommandExecutor()
        >>> result = executor.execute(["list", "--json"])
        >>> print(result["stdout"])  # PM2 process list JSON

        >>> # Custom PM2 binary path
        >>> executor = PM2CommandExecutor("/usr/local/bin/pm2")
        >>>
        >>> # Skip validation for embedded usage
        >>> executor = PM2CommandExecutor(validate=False)
    """

    def __init__(self, pm2_binary: str = "pm2", validate: bool = True):
        """Initialize PM2CommandExecutor.

        Args:
            pm2_binary (str): Path to PM2 binary (default: "pm2")
            validate (bool): Whether to validate PM2 installation on init

        Raises:
            PM2ConnectionError: If PM2 validation fails

        Example:
            >>> # Default PM2 binary with validation
            >>> executor = PM2CommandExecutor()
            >>>
            >>> # Custom binary path
            >>> executor = PM2CommandExecutor("/opt/node/bin/pm2")
            >>>
            >>> # Skip validation for testing
            >>> executor = PM2CommandExecutor(validate=False)
        """
        self.pm2_binary = pm2_binary
        if validate:
            self._validate_pm2_installation()

    def _validate_pm2_installation(self):
        """Validate that PM2 is installed and accessible.

        Checks if the PM2 binary exists and responds to version queries.
        This helps catch installation issues early before attempting
        process management operations.

        Raises:
            PM2ConnectionError: If PM2 is not found, not accessible,
                              or doesn't respond within timeout

        Example:
            >>> executor = PM2CommandExecutor()
            >>> # Validation happens automatically in __init__
            >>> # If this succeeds, PM2 is ready to use
        """
        try:
            result = subprocess.run(
                [self.pm2_binary, "--version"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                raise PM2ConnectionError(f"PM2 binary not accessible: {result.stderr}")
        except FileNotFoundError:
            raise PM2ConnectionError(
                f"PM2 not found. Please install PM2: npm install -g pm2"
            )
        except subprocess.TimeoutExpired:
            raise PM2ConnectionError(
                "PM2 command timed out after 30 seconds. PM2 may not be responding or busy."
            )

    def execute(self, args: List[str], timeout: int = 30) -> Dict[str, Any]:
        """Execute PM2 command synchronously and return parsed result.

        Args:
            args (List[str]): PM2 command arguments (without 'pm2' binary)
            timeout (int): Command timeout in seconds (default: 30)

        Returns:
            Dict[str, Any]: Command result with stdout, stderr, and returncode

        Raises:
            PM2CommandError: If command fails, times out, or returns non-zero exit code

        Example:
            >>> executor = PM2CommandExecutor()
            >>>
            >>> # List processes
            >>> result = executor.execute(["list", "--json"])
            >>> processes = json.loads(result["stdout"])
            >>>
            >>> # Start application
            >>> result = executor.execute(["start", "app.js", "--name", "my-app"])
            >>> if result["returncode"] == 0:
            ...     print("App started successfully")
        """
        command = [self.pm2_binary] + args

        try:
            logger.debug(f"Executing PM2 command: {' '.join(command)}")

            result = subprocess.run(
                command, capture_output=True, text=True, timeout=timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                raise PM2CommandError(
                    f"PM2 command failed: {error_msg}",
                    command=command,
                    exit_code=result.returncode,
                )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }

        except subprocess.TimeoutExpired:
            raise PM2CommandError(
                f"PM2 command timed out after {timeout}s", command=command
            )
        except Exception as e:
            raise PM2CommandError(
                f"PM2 command execution failed: {str(e)}", command=command
            )

    async def execute_async(self, args: List[str], timeout: int = 30) -> Dict[str, Any]:
        """Execute PM2 command asynchronously and return parsed result.

        Args:
            args (List[str]): PM2 command arguments (without 'pm2' binary)
            timeout (int): Command timeout in seconds (default: 30)

        Returns:
            Dict[str, Any]: Command result with stdout, stderr, and returncode

        Raises:
            PM2CommandError: If command fails, times out, or returns non-zero exit code

        Example:
            >>> async def manage_processes():
            ...     executor = PM2CommandExecutor()
            ...
            ...     # List processes asynchronously
            ...     result = await executor.execute_async(["list", "--json"])
            ...     processes = json.loads(result["stdout"])
            ...
            ...     # Start multiple apps concurrently
            ...     tasks = [
            ...         executor.execute_async(["start", "app1.js"]),
            ...         executor.execute_async(["start", "app2.js"]),
            ...         executor.execute_async(["start", "app3.js"])
            ...     ]
            ...     await asyncio.gather(*tasks)
        """
        command = [self.pm2_binary] + args

        try:
            logger.debug(f"Executing async PM2 command: {' '.join(command)}")

            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise PM2CommandError(
                    f"PM2 command timed out after {timeout}s", command=command
                )

            if process.returncode != 0:
                error_msg = stderr.decode().strip() or stdout.decode().strip()
                raise PM2CommandError(
                    f"PM2 command failed: {error_msg}",
                    command=command,
                    exit_code=process.returncode,
                )

            return {
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "returncode": process.returncode,
            }

        except Exception as e:
            if not isinstance(e, PM2CommandError):
                raise PM2CommandError(
                    f"PM2 command execution failed: {str(e)}", command=command
                )
            raise


class PM2Manager:
    """Main PM2 management class with comprehensive functionality.

    This is the primary interface for managing PM2 processes. It provides both
    synchronous and asynchronous methods for all PM2 operations including
    starting, stopping, restarting, monitoring, and configuring processes.

    The manager supports both context manager usage for automatic resource
    cleanup and standalone usage. It automatically handles PM2 daemon
    communication and provides detailed error handling.

    Key Features:
    - Complete PM2 process lifecycle management
    - Real-time process monitoring and metrics
    - Comprehensive logging and error handling
    - Both sync and async operation modes
    - Context manager support for resource management
    - Process configuration management
    - Log management and analysis

    Attributes:
        executor (PM2CommandExecutor): Command executor instance
        _is_async_context (bool): Whether running in async context

    Example:
        >>> # Synchronous usage
        >>> pm2 = PM2Manager()
        >>> process = pm2.start_app("app.js", name="web-server", instances=4)
        >>> print(f"Started {process.name} with PID {process.pid}")
        >>>
        >>> processes = pm2.list_processes()
        >>> for proc in processes:
        ...     print(f"{proc.name}: {proc.status.value}")

        >>> # Asynchronous usage with context manager
        >>> async def main():
        ...     async with PM2Manager() as pm2:
        ...         process = await pm2.start_app_async("app.py", name="python-app")
        ...         metrics = process.metrics
        ...         print(f"CPU: {metrics.cpu}%, Memory: {metrics.memory_mb}MB")
        ...
        ...         logs = await pm2.get_logs_async(name="python-app", lines=50)
        ...         print(logs)

        >>> # Custom PM2 binary
        >>> pm2 = PM2Manager(pm2_binary="/usr/local/bin/pm2")

        >>> # Skip validation for testing
        >>> pm2 = PM2Manager(validate=False)
    """

    def __init__(self, pm2_binary: str = "pm2", validate: bool = True):
        """Initialize PM2Manager.

        Args:
            pm2_binary (str): Path to PM2 binary (default: "pm2")
            validate (bool): Whether to validate PM2 installation

        Raises:
            PM2ConnectionError: If PM2 validation fails

        Example:
            >>> # Default configuration
            >>> pm2 = PM2Manager()
            >>>
            >>> # Custom PM2 binary location
            >>> pm2 = PM2Manager(pm2_binary="/opt/node/bin/pm2")
            >>>
            >>> # Skip validation for testing or offline usage
            >>> pm2 = PM2Manager(validate=False)
        """
        self.executor = PM2CommandExecutor(pm2_binary, validate=validate)
        self._is_async_context = False

    async def __aenter__(self):
        """Async context manager entry.

        Enables the PM2Manager to be used as an async context manager,
        which is the recommended pattern for async operations.

        Returns:
            PM2Manager: The manager instance for chaining

        Example:
            >>> async def main():
            ...     async with PM2Manager() as pm2:
            ...         processes = await pm2.list_processes_async()
            ...         # PM2 operations here
            ...     # Automatic cleanup happens here
        """
        self._is_async_context = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit.

        Handles cleanup and resource management when exiting the
        async context manager.

        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
        """
        self._is_async_context = False

    def async_context(self):
        """Return async context manager for PM2 operations.

        Alternative method to get the async context manager when
        direct async with syntax isn't available.

        Returns:
            PM2Manager: The manager instance as async context manager

        Example:
            >>> pm2 = PM2Manager()
            >>> async_pm2 = pm2.async_context()
            >>> async with async_pm2 as pm2_ctx:
            ...     processes = await pm2_ctx.list_processes_async()
        """
        return self

    def is_pm2_running(self) -> bool:
        """Check if PM2 daemon is running and responsive.

        Tests PM2 daemon connectivity by executing a simple status command.
        This is useful for health checks and ensuring PM2 is operational
        before attempting process management operations.

        Returns:
            bool: True if PM2 daemon is running and responsive, False otherwise

        Example:
            >>> pm2 = PM2Manager()
            >>> if pm2.is_pm2_running():
            ...     print("PM2 daemon is running")
            ...     processes = pm2.list_processes()
            ... else:
            ...     print("PM2 daemon is not running")
            ...     print("Try: pm2 start ecosystem.config.js")
        """
        try:
            result = self._execute(["status"])
            return result["returncode"] == 0
        except Exception:
            return False

    def _execute(self, args: List[str], **kwargs) -> Dict[str, Any]:
        """Execute PM2 command in synchronous mode.

        Internal method that delegates to the command executor for
        synchronous operations.

        Args:
            args (List[str]): PM2 command arguments
            **kwargs: Additional arguments passed to executor

        Returns:
            Dict[str, Any]: Command execution result
        """
        return self.executor.execute(args, **kwargs)

    async def _execute_async(self, args: List[str], **kwargs) -> Dict[str, Any]:
        """Execute PM2 command in asynchronous mode.

        Internal method that delegates to the command executor for
        asynchronous operations.

        Args:
            args (List[str]): PM2 command arguments
            **kwargs: Additional arguments passed to executor

        Returns:
            Dict[str, Any]: Command execution result
        """
        return await self.executor.execute_async(args, **kwargs)

    def list_processes(self) -> List[PM2Process]:
        """List all PM2 processes with detailed information.

        Retrieves comprehensive information about all processes managed by PM2,
        including their current status, resource usage, configuration, and
        runtime metrics.

        Returns:
            List[PM2Process]: List of PM2Process objects with complete process data

        Example:
            >>> pm2 = PM2Manager()
            >>> processes = pm2.list_processes()
            >>>
            >>> # Display process overview
            >>> for proc in processes:
            ...     status_icon = "🟢" if proc.is_online else "🔴"
            ...     print(f"{status_icon} {proc.name:15} {proc.memory_usage_human:>8} "
            ...           f"{proc.metrics.cpu:>5.1f}% {proc.uptime_human:>10}")
            >>>
            >>> # Filter running processes
            >>> running = [p for p in processes if p.is_online]
            >>> print(f"Running processes: {len(running)}/{len(processes)}")
            >>>
            >>> # Find high memory usage
            >>> high_memory = [p for p in processes if p.metrics.memory_mb > 100]
            >>> if high_memory:
            ...     print("High memory usage:")
            ...     for proc in high_memory:
            ...         print(f"  {proc.name}: {proc.memory_usage_human}")
        """
        result = self._execute(["jlist"])
        processes_data = json.loads(result["stdout"])
        return [PM2Process(proc_data) for proc_data in processes_data]

    async def list_processes_async(self) -> List[PM2Process]:
        """List all PM2 processes asynchronously with detailed information.

        Asynchronous version of list_processes() that retrieves comprehensive
        information about all processes managed by PM2 without blocking.

        Returns:
            List[PM2Process]: List of PM2Process objects with complete process data

        Example:
            >>> async def monitor_processes():
            ...     async with PM2Manager() as pm2:
            ...         while True:
            ...             processes = await pm2.list_processes_async()
            ...
            ...             # Real-time monitoring dashboard
            ...             print("\033[2J\033[H")  # Clear screen
            ...             print("PM2 Process Monitor")
            ...             print("-" * 60)
            ...
            ...             for proc in processes:
            ...                 status = "🟢 Online" if proc.is_online else "🔴 Offline"
            ...                 print(f"{proc.name:15} {status:10} {proc.metrics.cpu:5.1f}% "
            ...                       f"{proc.memory_usage_human:>8} {proc.uptime_human}")
            ...
            ...             await asyncio.sleep(2)  # Update every 2 seconds
        """
        result = await self._execute_async(["jlist"])
        processes_data = json.loads(result["stdout"])
        return [PM2Process(proc_data) for proc_data in processes_data]

    def get_process(
        self,
        name: Optional[str] = None,
        pid: Optional[int] = None,
        pm_id: Optional[int] = None,
    ) -> PM2Process:
        """Get specific process by name, PID, or PM2 ID.

        Searches for and returns a specific PM2 process using one of the
        available identifiers. At least one identifier must be provided.

        Args:
            name (Optional[str]): Process name to search for
            pid (Optional[int]): System process ID to search for
            pm_id (Optional[int]): PM2 internal process ID to search for

        Returns:
            PM2Process: The matching process with complete information

        Raises:
            PM2ValidationError: If no identifier is provided
            PM2ProcessNotFoundError: If no matching process is found

        Example:
            >>> pm2 = PM2Manager()
            >>>
            >>> # Get process by name
            >>> process = pm2.get_process(name="web-server")
            >>> print(f"Found {process.name} with PID {process.pid}")
            >>>
            >>> # Get process by system PID
            >>> process = pm2.get_process(pid=12345)
            >>> print(f"Process name: {process.name}")
            >>>
            >>> # Get process by PM2 ID
            >>> process = pm2.get_process(pm_id=0)
            >>> print(f"First PM2 process: {process.name}")
            >>>
            >>> # Handle not found
            >>> try:
            ...     process = pm2.get_process(name="nonexistent")
            ... except PM2ProcessNotFoundError as e:
            ...     print(f"Process not found: {e.identifier}")
            ...     # List available processes
            ...     available = [p.name for p in pm2.list_processes()]
            ...     print(f"Available: {available}")
        """
        if not any([name, pid, pm_id]):
            raise PM2ValidationError(
                "At least one identifier (name, pid, pm_id) must be provided"
            )

        processes = self.list_processes()

        for process in processes:
            if (
                (name and process.name == name)
                or (pid and process.pid == pid)
                or (pm_id is not None and process.pm_id == pm_id)
            ):
                return process

        identifier = name or str(pid) or str(pm_id)
        identifier_type = "name" if name else "pid" if pid else "pm_id"
        raise PM2ProcessNotFoundError(identifier, identifier_type)

    async def get_process_async(
        self,
        name: Optional[str] = None,
        pid: Optional[int] = None,
        pm_id: Optional[int] = None,
    ) -> PM2Process:
        """Get specific process asynchronously by name, PID, or PM2 ID.

        Asynchronous version of get_process() that searches for and returns
        a specific PM2 process without blocking. At least one identifier
        must be provided.

        Args:
            name (Optional[str]): Process name to search for
            pid (Optional[int]): System process ID to search for
            pm_id (Optional[int]): PM2 internal process ID to search for

        Returns:
            PM2Process: The matching process with complete information

        Raises:
            PM2ValidationError: If no identifier is provided
            PM2ProcessNotFoundError: If no matching process is found

        Example:
            >>> async def check_process_health():
            ...     async with PM2Manager() as pm2:
            ...         try:
            ...             process = await pm2.get_process_async(name="api-server")
            ...
            ...             if not process.is_online:
            ...                 print(f"Process {process.name} is down, restarting...")
            ...                 await pm2.restart_process_async(name=process.name)
            ...
            ...             elif process.metrics.cpu > 90:
            ...                 print(f"High CPU usage: {process.metrics.cpu}%")
            ...                 # Maybe scale up or investigate
            ...
            ...             elif process.restart_time > 10:
            ...                 print(f"Process has restarted {process.restart_time} times")
            ...                 # Maybe check logs or configuration
            ...
            ...         except PM2ProcessNotFoundError:
            ...             print("API server not found, starting...")
            ...             await pm2.start_app_async("api.js", name="api-server")
        """
        if not any([name, pid, pm_id]):
            raise PM2ValidationError(
                "At least one identifier (name, pid, pm_id) must be provided"
            )

        processes = await self.list_processes_async()

        for process in processes:
            if (
                (name and process.name == name)
                or (pid and process.pid == pid)
                or (pm_id is not None and process.pm_id == pm_id)
            ):
                return process

        identifier = name or str(pid) or str(pm_id)
        identifier_type = "name" if name else "pid" if pid else "pm_id"
        raise PM2ProcessNotFoundError(identifier, identifier_type)

    def start_app(
        self, script: str, name: Optional[str] = None, **kwargs
    ) -> PM2Process:
        """Start a new application with PM2.

        Launches a new application using PM2 with the specified script and
        configuration options. The method supports all major PM2 start options
        and returns the started process information.

        Args:
            script (str): Path to the script file to execute
            name (Optional[str]): Custom name for the process
            **kwargs: Additional PM2 start options:
                - instances (int|str): Number of instances or 'max'
                - exec_mode (str): Execution mode ('fork' or 'cluster')
                - env (Dict[str, str]): Environment variables
                - args (List[str]): Arguments to pass to the script
                - watch (bool|List[str]): Enable file watching
                - max_memory_restart (str): Memory limit for restart (e.g., '150M')
                - log_file (str): Log file path
                - error_file (str): Error log file path
                - out_file (str): Output log file path
                - cwd (str): Working directory
                - interpreter (str): Script interpreter

        Returns:
            PM2Process: The started process with complete information

        Raises:
            PM2ValidationError: If script path is empty
            PM2CommandError: If PM2 command fails
            PM2ProcessError: If process retrieval fails

        Example:
            >>> pm2 = PM2Manager()
            >>>
            >>> # Basic app start
            >>> process = pm2.start_app("app.js", name="web-server")
            >>> print(f"Started {process.name} with PID {process.pid}")
            >>>
            >>> # Advanced configuration
            >>> process = pm2.start_app(
            ...     script="server.js",
            ...     name="api-server",
            ...     instances=4,
            ...     exec_mode="cluster",
            ...     env={"NODE_ENV": "production", "PORT": "3000"},
            ...     max_memory_restart="500M",
            ...     watch=True,
            ...     log_file="/var/log/api.log"
            ... )
            >>>
            >>> # Python script with virtual environment
            >>> process = pm2.start_app(
            ...     script="app.py",
            ...     name="python-app",
            ...     interpreter="python3",
            ...     cwd="/opt/myapp",
            ...     env={"VIRTUAL_ENV": "/opt/myapp/venv"}
            ... )
        """
        if not script:
            raise PM2ValidationError("Script path cannot be empty")

        # Build command arguments
        cmd_args = ["start", script]

        if name:
            cmd_args.extend(["--name", name])

        # Handle common options
        for key, value in kwargs.items():
            if key == "instances" and value:
                cmd_args.extend(["-i", str(value)])
            elif key == "exec_mode" and value:
                cmd_args.extend(["--node-args", value])
            elif key == "env" and isinstance(value, dict):
                # Add environment variables using PM2 syntax
                for env_key, env_value in value.items():
                    cmd_args.extend(["--env", f"{env_key}={env_value}"])
            elif key == "args" and isinstance(value, list):
                cmd_args.extend(["--", *value])

        self._execute(cmd_args)

        # Return the started process
        if name:
            return self.get_process(name=name)
        else:
            # Get the most recently started process
            processes = self.list_processes()
            if processes:
                return max(processes, key=lambda p: p.pm_id)
            else:
                raise PM2ProcessError("Failed to retrieve started process")

    async def start_app_async(
        self, script: str, name: Optional[str] = None, **kwargs
    ) -> PM2Process:
        """Start a new application with PM2 asynchronously.

        Asynchronous version of start_app() that launches a new application
        using PM2 without blocking. The method supports all major PM2 start
        options and returns the started process information.

        Args:
            script (str): Path to the script file to execute
            name (Optional[str]): Custom name for the process
            **kwargs: Additional PM2 start options (same as start_app)

        Returns:
            PM2Process: The started process with complete information

        Raises:
            PM2ValidationError: If script path is empty
            PM2CommandError: If PM2 command fails
            PM2ProcessError: If process retrieval fails

        Example:
            >>> async def deploy_microservices():
            ...     async with PM2Manager() as pm2:
            ...         # Start multiple services concurrently
            ...         services = [
            ...             ("auth-service.js", "auth", {"PORT": "3001"}),
            ...             ("user-service.js", "users", {"PORT": "3002"}),
            ...             ("order-service.js", "orders", {"PORT": "3003"}),
            ...         ]
            ...
            ...         tasks = []
            ...         for script, name, env in services:
            ...             task = pm2.start_app_async(
            ...                 script=script,
            ...                 name=name,
            ...                 env=env,
            ...                 instances=2
            ...             )
            ...             tasks.append(task)
            ...
            ...         # Wait for all services to start
            ...         processes = await asyncio.gather(*tasks)
            ...
            ...         for proc in processes:
            ...             print(f"Started {proc.name} with PID {proc.pid}")
            >>>
            >>> # Run the deployment
            >>> asyncio.run(deploy_microservices())
        """
        if not script:
            raise PM2ValidationError("Script path cannot be empty")

        # Build command arguments
        cmd_args = ["start", script]

        if name:
            cmd_args.extend(["--name", name])

        # Handle common options
        for key, value in kwargs.items():
            if key == "instances" and value:
                cmd_args.extend(["-i", str(value)])
            elif key == "exec_mode" and value:
                cmd_args.extend(["--node-args", value])
            elif key == "env" and isinstance(value, dict):
                # Add environment variables using PM2 syntax
                for env_key, env_value in value.items():
                    cmd_args.extend(["--env", f"{env_key}={env_value}"])
            elif key == "args" and isinstance(value, list):
                cmd_args.extend(["--", *value])

        await self._execute_async(cmd_args)

        # Return the started process
        if name:
            return await self.get_process_async(name=name)
        else:
            # Get the most recently started process
            processes = await self.list_processes_async()
            if processes:
                return max(processes, key=lambda p: p.pm_id)
            else:
                raise PM2ProcessError("Failed to retrieve started process")

    def stop_process(
        self,
        name: Optional[str] = None,
        pid: Optional[int] = None,
        pm_id: Optional[int] = None,
    ) -> PM2Process:
        """Stop a running PM2 process.

        Gracefully stops a PM2 process by sending a SIGTERM signal.
        The process will be given time to clean up before being forcefully
        terminated if it doesn't respond.

        Args:
            name (Optional[str]): Process name to stop
            pid (Optional[int]): System process ID to stop
            pm_id (Optional[int]): PM2 internal process ID to stop

        Returns:
            PM2Process: Updated process information after stopping

        Raises:
            PM2ValidationError: If no identifier is provided
            PM2ProcessNotFoundError: If the process doesn't exist
            PM2CommandError: If the stop command fails

        Example:
            >>> pm2 = PM2Manager()
            >>>
            >>> # Stop by name
            >>> process = pm2.stop_process(name="web-server")
            >>> print(f"Stopped {process.name}, status: {process.status.value}")
            >>>
            >>> # Stop by PID
            >>> process = pm2.stop_process(pid=12345)
            >>>
            >>> # Stop all instances of a process
            >>> processes = pm2.list_processes()
            >>> web_processes = [p for p in processes if "web" in p.name]
            >>> for proc in web_processes:
            ...     if proc.is_online:
            ...         stopped = pm2.stop_process(pm_id=proc.pm_id)
            ...         print(f"Stopped {stopped.name}")
        """
        process = self.get_process(name=name, pid=pid, pm_id=pm_id)
        self._execute(["stop", str(process.pm_id)])
        return self.get_process(pm_id=process.pm_id)

    async def stop_process_async(
        self,
        name: Optional[str] = None,
        pid: Optional[int] = None,
        pm_id: Optional[int] = None,
    ) -> PM2Process:
        """Stop a running PM2 process asynchronously.

        Asynchronous version of stop_process() that gracefully stops a PM2
        process without blocking the current thread.

        Args:
            name (Optional[str]): Process name to stop
            pid (Optional[int]): System process ID to stop
            pm_id (Optional[int]): PM2 internal process ID to stop

        Returns:
            PM2Process: Updated process information after stopping

        Raises:
            PM2ValidationError: If no identifier is provided
            PM2ProcessNotFoundError: If the process doesn't exist
            PM2CommandError: If the stop command fails

        Example:
            >>> async def graceful_shutdown():
            ...     async with PM2Manager() as pm2:
            ...         processes = await pm2.list_processes_async()
            ...
            ...         # Stop all running processes concurrently
            ...         stop_tasks = []
            ...         for proc in processes:
            ...             if proc.is_online:
            ...                 task = pm2.stop_process_async(name=proc.name)
            ...                 stop_tasks.append(task)
            ...
            ...         # Wait for all processes to stop
            ...         if stop_tasks:
            ...             stopped_processes = await asyncio.gather(*stop_tasks)
            ...             for proc in stopped_processes:
            ...                 print(f"Stopped {proc.name}")
        """
        process = await self.get_process_async(name=name, pid=pid, pm_id=pm_id)
        await self._execute_async(["stop", str(process.pm_id)])
        return await self.get_process_async(pm_id=process.pm_id)

    def restart_process(
        self,
        name: Optional[str] = None,
        pid: Optional[int] = None,
        pm_id: Optional[int] = None,
    ) -> PM2Process:
        """Restart a PM2 process.

        Performs a hard restart of a PM2 process by stopping it and then
        starting it again. This will increment the restart counter and
        may cause a brief downtime.

        Args:
            name (Optional[str]): Process name to restart
            pid (Optional[int]): System process ID to restart
            pm_id (Optional[int]): PM2 internal process ID to restart

        Returns:
            PM2Process: Updated process information after restarting

        Raises:
            PM2ValidationError: If no identifier is provided
            PM2ProcessNotFoundError: If the process doesn't exist
            PM2CommandError: If the restart command fails

        Note:
            For zero-downtime restarts of cluster mode processes,
            use reload_process() instead.

        Example:
            >>> pm2 = PM2Manager()
            >>>
            >>> # Restart after configuration changes
            >>> process = pm2.restart_process(name="api-server")
            >>> print(f"Restarted {process.name}, restart count: {process.restart_time}")
            >>>
            >>> # Restart all errored processes
            >>> processes = pm2.list_processes()
            >>> for proc in processes:
            ...     if proc.status == ProcessStatus.ERRORED:
            ...         restarted = pm2.restart_process(name=proc.name)
            ...         print(f"Restarted errored process: {restarted.name}")
        """
        process = self.get_process(name=name, pid=pid, pm_id=pm_id)
        self._execute(["restart", str(process.pm_id)])
        return self.get_process(pm_id=process.pm_id)

    async def restart_process_async(
        self,
        name: Optional[str] = None,
        pid: Optional[int] = None,
        pm_id: Optional[int] = None,
    ) -> PM2Process:
        """Restart a PM2 process asynchronously.

        Asynchronous version of restart_process() that performs a hard restart
        of a PM2 process without blocking the current thread.

        Args:
            name (Optional[str]): Process name to restart
            pid (Optional[int]): System process ID to restart
            pm_id (Optional[int]): PM2 internal process ID to restart

        Returns:
            PM2Process: Updated process information after restarting

        Raises:
            PM2ValidationError: If no identifier is provided
            PM2ProcessNotFoundError: If the process doesn't exist
            PM2CommandError: If the restart command fails

        Example:
            >>> async def rolling_restart():
            ...     async with PM2Manager() as pm2:
            ...         processes = await pm2.list_processes_async()
            ...
            ...         # Restart processes one by one with delay
            ...         for proc in processes:
            ...             if proc.is_online:
            ...                 print(f"Restarting {proc.name}...")
            ...                 restarted = await pm2.restart_process_async(name=proc.name)
            ...                 print(f"Restarted {restarted.name}")
            ...
            ...                 # Wait before restarting next process
            ...                 await asyncio.sleep(5)
        """
        process = await self.get_process_async(name=name, pid=pid, pm_id=pm_id)
        await self._execute_async(["restart", str(process.pm_id)])
        return await self.get_process_async(pm_id=process.pm_id)

    def delete_process(
        self,
        name: Optional[str] = None,
        pid: Optional[int] = None,
        pm_id: Optional[int] = None,
    ) -> bool:
        """Delete a PM2 process completely.

        Permanently removes a process from PM2 management. This will stop
        the process if it's running and remove it from the process list.
        The process cannot be restarted after deletion.

        Args:
            name (Optional[str]): Process name to delete
            pid (Optional[int]): System process ID to delete
            pm_id (Optional[int]): PM2 internal process ID to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            PM2ValidationError: If no identifier is provided
            PM2ProcessNotFoundError: If the process doesn't exist
            PM2CommandError: If the delete command fails

        Warning:
            This operation is irreversible. The process will be completely
            removed from PM2 and cannot be recovered.

        Example:
            >>> pm2 = PM2Manager()
            >>>
            >>> # Delete a specific process
            >>> success = pm2.delete_process(name="old-service")
            >>> if success:
            ...     print("Process deleted successfully")
            >>>
            >>> # Clean up all stopped processes
            >>> processes = pm2.list_processes()
            >>> for proc in processes:
            ...     if proc.is_stopped:
            ...         pm2.delete_process(name=proc.name)
            ...         print(f"Deleted stopped process: {proc.name}")
        """
        process = self.get_process(name=name, pid=pid, pm_id=pm_id)
        self._execute(["delete", str(process.pm_id)])
        return True

    async def delete_process_async(
        self,
        name: Optional[str] = None,
        pid: Optional[int] = None,
        pm_id: Optional[int] = None,
    ) -> bool:
        """Delete a PM2 process completely asynchronously.

        Asynchronous version of delete_process() that permanently removes
        a process from PM2 management without blocking.

        Args:
            name (Optional[str]): Process name to delete
            pid (Optional[int]): System process ID to delete
            pm_id (Optional[int]): PM2 internal process ID to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            PM2ValidationError: If no identifier is provided
            PM2ProcessNotFoundError: If the process doesn't exist
            PM2CommandError: If the delete command fails

        Warning:
            This operation is irreversible. The process will be completely
            removed from PM2 and cannot be recovered.

        Example:
            >>> async def cleanup_processes():
            ...     async with PM2Manager() as pm2:
            ...         processes = await pm2.list_processes_async()
            ...
            ...         # Find processes to clean up
            ...         to_delete = [
            ...             proc for proc in processes
            ...             if proc.is_stopped and proc.restart_time > 20
            ...         ]
            ...
            ...         # Delete them concurrently
            ...         if to_delete:
            ...             tasks = [
            ...                 pm2.delete_process_async(name=proc.name)
            ...                 for proc in to_delete
            ...             ]
            ...             await asyncio.gather(*tasks)
            ...             print(f"Deleted {len(to_delete)} problematic processes")
        """
        process = await self.get_process_async(name=name, pid=pid, pm_id=pm_id)
        await self._execute_async(["delete", str(process.pm_id)])
        return True

    def get_logs(
        self,
        name: Optional[str] = None,
        pid: Optional[int] = None,
        pm_id: Optional[int] = None,
        lines: int = 100,
    ) -> str:
        """Get process logs from PM2.

        Retrieves the most recent log entries for a specific process.
        Logs include both stdout and stderr output from the process.

        Args:
            name (Optional[str]): Process name to get logs for
            pid (Optional[int]): System process ID to get logs for
            pm_id (Optional[int]): PM2 internal process ID to get logs for
            lines (int): Number of log lines to retrieve (default: 100)

        Returns:
            str: Log content as a string with timestamps and process info

        Raises:
            PM2ValidationError: If no identifier is provided
            PM2ProcessNotFoundError: If the process doesn't exist
            PM2CommandError: If the logs command fails

        Example:
            >>> pm2 = PM2Manager()
            >>>
            >>> # Get recent logs
            >>> logs = pm2.get_logs(name="web-server", lines=50)
            >>> print(logs)
            >>>
            >>> # Analyze error logs
            >>> logs = pm2.get_logs(name="api-server", lines=200)
            >>> error_lines = [line for line in logs.split('\n') if 'ERROR' in line]
            >>> if error_lines:
            ...     print(f"Found {len(error_lines)} error messages:")
            ...     for error in error_lines[-5:]:  # Show last 5 errors
            ...         print(f"  {error}")
            >>>
            >>> # Monitor all processes for errors
            >>> processes = pm2.list_processes()
            >>> for proc in processes:
            ...     if proc.is_online:
            ...         logs = pm2.get_logs(name=proc.name, lines=20)
            ...         if "error" in logs.lower() or "exception" in logs.lower():
            ...             print(f"⚠️  {proc.name} has recent errors")
        """
        process = self.get_process(name=name, pid=pid, pm_id=pm_id)
        result = self._execute(
            ["logs", process.name, "--lines", str(lines), "--nostream"]
        )
        return result["stdout"]

    async def get_logs_async(
        self,
        name: Optional[str] = None,
        pid: Optional[int] = None,
        pm_id: Optional[int] = None,
        lines: int = 100,
    ) -> str:
        """Get process logs from PM2 asynchronously.

        Asynchronous version of get_logs() that retrieves the most recent
        log entries for a specific process without blocking.

        Args:
            name (Optional[str]): Process name to get logs for
            pid (Optional[int]): System process ID to get logs for
            pm_id (Optional[int]): PM2 internal process ID to get logs for
            lines (int): Number of log lines to retrieve (default: 100)

        Returns:
            str: Log content as a string with timestamps and process info

        Raises:
            PM2ValidationError: If no identifier is provided
            PM2ProcessNotFoundError: If the process doesn't exist
            PM2CommandError: If the logs command fails

        Example:
            >>> async def analyze_logs():
            ...     async with PM2Manager() as pm2:
            ...         processes = await pm2.list_processes_async()
            ...
            ...         # Get logs for all processes concurrently
            ...         log_tasks = [
            ...             pm2.get_logs_async(name=proc.name, lines=50)
            ...             for proc in processes if proc.is_online
            ...         ]
            ...
            ...         logs_results = await asyncio.gather(*log_tasks)
            ...
            ...         # Analyze logs for issues
            ...         for i, logs in enumerate(logs_results):
            ...             proc = processes[i]
            ...             error_count = logs.lower().count('error')
            ...             if error_count > 0:
            ...                 print(f"{proc.name}: {error_count} errors found")
        """
        process = await self.get_process_async(name=name, pid=pid, pm_id=pm_id)
        result = await self._execute_async(
            ["logs", process.name, "--lines", str(lines), "--nostream"]
        )
        return result["stdout"]

    def flush_logs(
        self,
        name: Optional[str] = None,
        pid: Optional[int] = None,
        pm_id: Optional[int] = None,
    ) -> bool:
        """Flush (clear) process logs.

        Clears the log files for a specific process or all processes.
        This is useful for log rotation or when log files become too large.

        Args:
            name (Optional[str]): Process name to flush logs for
            pid (Optional[int]): System process ID to flush logs for
            pm_id (Optional[int]): PM2 internal process ID to flush logs for

        Returns:
            bool: True if flush operation was successful

        Raises:
            PM2ProcessNotFoundError: If the specified process doesn't exist
            PM2CommandError: If the flush command fails

        Note:
            If no identifier is provided, logs for ALL processes will be flushed.

        Example:
            >>> pm2 = PM2Manager()
            >>>
            >>> # Flush logs for specific process
            >>> success = pm2.flush_logs(name="web-server")
            >>> if success:
            ...     print("Logs cleared for web-server")
            >>>
            >>> # Flush all logs (be careful!)
            >>> success = pm2.flush_logs()
            >>> if success:
            ...     print("All process logs have been cleared")
            >>>
            >>> # Weekly log maintenance
            >>> processes = pm2.list_processes()
            >>> for proc in processes:
            ...     # Flush logs for processes with high restart counts
            ...     if proc.restart_time > 10:
            ...         pm2.flush_logs(name=proc.name)
            ...         print(f"Cleared logs for problematic process: {proc.name}")
        """
        if name:
            self._execute(["flush", name])
        elif pid or pm_id:
            process = self.get_process(pid=pid, pm_id=pm_id)
            self._execute(["flush", process.name])
        else:
            self._execute(["flush"])
        return True

    async def flush_logs_async(
        self,
        name: Optional[str] = None,
        pid: Optional[int] = None,
        pm_id: Optional[int] = None,
    ) -> bool:
        """Flush (clear) process logs asynchronously.

        Asynchronous version of flush_logs() that clears log files for a
        specific process or all processes without blocking.

        Args:
            name (Optional[str]): Process name to flush logs for
            pid (Optional[int]): System process ID to flush logs for
            pm_id (Optional[int]): PM2 internal process ID to flush logs for

        Returns:
            bool: True if flush operation was successful

        Raises:
            PM2ProcessNotFoundError: If the specified process doesn't exist
            PM2CommandError: If the flush command fails

        Note:
            If no identifier is provided, logs for ALL processes will be flushed.

        Example:
            >>> async def log_maintenance():
            ...     async with PM2Manager() as pm2:
            ...         processes = await pm2.list_processes_async()
            ...
            ...         # Find processes that need log cleanup
            ...         to_flush = []
            ...         for proc in processes:
            ...             # Check if process has been running for a while
            ...             if proc.uptime_seconds > 86400:  # 1 day
            ...                 to_flush.append(proc.name)
            ...
            ...         # Flush logs concurrently
            ...         if to_flush:
            ...             tasks = [
            ...                 pm2.flush_logs_async(name=name)
            ...                 for name in to_flush
            ...             ]
            ...             await asyncio.gather(*tasks)
            ...             print(f"Cleared logs for {len(to_flush)} processes")
        """
        if name:
            await self._execute_async(["flush", name])
        elif pid or pm_id:
            process = await self.get_process_async(pid=pid, pm_id=pm_id)
            await self._execute_async(["flush", process.name])
        else:
            await self._execute_async(["flush"])
        return True

    def reload_process(
        self,
        name: Optional[str] = None,
        pid: Optional[int] = None,
        pm_id: Optional[int] = None,
    ) -> PM2Process:
        """Reload a process with zero-downtime restart.

        Performs a graceful reload of a cluster mode process without any
        downtime. This is the preferred method for updating cluster mode
        applications as it reloads instances one by one while maintaining
        service availability.

        Args:
            name (Optional[str]): Process name to reload
            pid (Optional[int]): System process ID to reload
            pm_id (Optional[int]): PM2 internal process ID to reload

        Returns:
            PM2Process: Updated process information after reloading

        Raises:
            PM2ValidationError: If no identifier is provided
            PM2ProcessNotFoundError: If the process doesn't exist
            PM2CommandError: If the reload command fails

        Note:
            Reload only works with cluster mode processes. For fork mode
            processes, use restart_process() instead.

        Example:
            >>> pm2 = PM2Manager()
            >>>
            >>> # Zero-downtime deployment
            >>> process = pm2.reload_process(name="web-server")
            >>> print(f"Reloaded {process.name} without downtime")
            >>>
            >>> # Reload all cluster processes after code update
            >>> processes = pm2.list_processes()
            >>> cluster_processes = [
            ...     p for p in processes
            ...     if p.exec_mode == ProcessMode.CLUSTER and p.is_online
            ... ]
            >>>
            >>> for proc in cluster_processes:
            ...     reloaded = pm2.reload_process(name=proc.name)
            ...     print(f"Reloaded {reloaded.name}")
        """
        process = self.get_process(name=name, pid=pid, pm_id=pm_id)
        self._execute(["reload", str(process.pm_id)])
        return self.get_process(pm_id=process.pm_id)

    async def reload_process_async(
        self,
        name: Optional[str] = None,
        pid: Optional[int] = None,
        pm_id: Optional[int] = None,
    ) -> PM2Process:
        """Reload a process with zero-downtime restart asynchronously.

        Asynchronous version of reload_process() that performs a graceful
        reload of a cluster mode process without any downtime or blocking.

        Args:
            name (Optional[str]): Process name to reload
            pid (Optional[int]): System process ID to reload
            pm_id (Optional[int]): PM2 internal process ID to reload

        Returns:
            PM2Process: Updated process information after reloading

        Raises:
            PM2ValidationError: If no identifier is provided
            PM2ProcessNotFoundError: If the process doesn't exist
            PM2CommandError: If the reload command fails

        Example:
            >>> async def zero_downtime_deployment():
            ...     async with PM2Manager() as pm2:
            ...         processes = await pm2.list_processes_async()
            ...
            ...         # Find cluster processes to reload
            ...         cluster_procs = [
            ...             p for p in processes
            ...             if p.exec_mode == ProcessMode.CLUSTER and p.is_online
            ...         ]
            ...
            ...         # Reload all cluster processes concurrently
            ...         reload_tasks = [
            ...             pm2.reload_process_async(name=proc.name)
            ...             for proc in cluster_procs
            ...         ]
            ...
            ...         if reload_tasks:
            ...             reloaded = await asyncio.gather(*reload_tasks)
            ...             print(f"Zero-downtime reload completed for {len(reloaded)} processes")
            ...
            ...             # Verify all processes are still healthy
            ...             for proc in reloaded:
            ...                 if proc.is_online:
            ...                     print(f"✅ {proc.name} reloaded successfully")
            ...                 else:
            ...                     print(f"❌ {proc.name} failed to reload")
        """
        process = await self.get_process_async(name=name, pid=pid, pm_id=pm_id)
        await self._execute_async(["reload", str(process.pm_id)])
        return await self.get_process_async(pm_id=process.pm_id)

    def save_process_list(self) -> bool:
        """Save the current process list to PM2's dump file.

        Creates a snapshot of all currently managed processes that can be
        restored later using resurrect_processes(). This is useful for
        creating backups or preparing for system restarts.

        Returns:
            bool: True if save operation was successful

        Raises:
            PM2CommandError: If the save command fails

        Note:
            The saved process list is stored in PM2's home directory and
            includes all process configurations and states.

        Example:
            >>> pm2 = PM2Manager()
            >>>
            >>> # Save current process state before maintenance
            >>> success = pm2.save_process_list()
            >>> if success:
            ...     print("Process list saved successfully")
            >>>
            >>> # Typical backup workflow
            >>> try:
            ...     # Save current state
            ...     pm2.save_process_list()
            ...     print("✅ Process list backed up")
            ...
            ...     # Perform maintenance operations
            ...     # ... update code, configuration, etc ...
            ...
            ...     # If something goes wrong, you can restore with:
            ...     # pm2.resurrect_processes()
            ... except Exception as e:
            ...     print(f"❌ Backup failed: {e}")
        """
        self._execute(["save"])
        return True

    async def save_process_list_async(self) -> bool:
        """Save the current process list to PM2's dump file asynchronously.

        Asynchronous version of save_process_list() that creates a snapshot
        of all currently managed processes without blocking.

        Returns:
            bool: True if save operation was successful

        Raises:
            PM2CommandError: If the save command fails

        Example:
            >>> async def automated_backup():
            ...     async with PM2Manager() as pm2:
            ...         # Regular backup schedule
            ...         while True:
            ...             try:
            ...                 success = await pm2.save_process_list_async()
            ...                 if success:
            ...                     print(f"✅ Backup created at {datetime.now()}")
            ...
            ...                 # Wait 1 hour before next backup
            ...                 await asyncio.sleep(3600)
            ...
            ...             except Exception as e:
            ...                 print(f"❌ Backup failed: {e}")
            ...                 await asyncio.sleep(300)  # Retry in 5 minutes
        """
        await self._execute_async(["save"])
        return True

    def resurrect_processes(self) -> List[PM2Process]:
        """Resurrect previously saved processes from PM2's dump file.

        Restores all processes that were previously saved using save_process_list().
        This is extremely useful for system recovery, deployment rollbacks,
        or restoring services after maintenance.

        Returns:
            List[PM2Process]: List of all processes after resurrection

        Raises:
            PM2CommandError: If the resurrect command fails

        Note:
            This will attempt to start all processes that were saved in the
            dump file, regardless of their previous state.

        Example:
            >>> pm2 = PM2Manager()
            >>>
            >>> # System recovery after restart
            >>> processes = pm2.resurrect_processes()
            >>> print(f"Restored {len(processes)} processes")
            >>>
            >>> # Verify resurrection success
            >>> online_count = len([p for p in processes if p.is_online])
            >>> print(f"✅ {online_count}/{len(processes)} processes are online")
            >>>
            >>> # Disaster recovery workflow
            >>> try:
            ...     print("Starting system recovery...")
            ...     processes = pm2.resurrect_processes()
            ...
            ...     # Check for failed processes
            ...     failed = [p for p in processes if not p.is_online]
            ...     if failed:
            ...         print(f"⚠️  {len(failed)} processes failed to start:")
            ...         for proc in failed:
            ...             print(f"   - {proc.name}: {proc.status.value}")
            ...     else:
            ...         print("🎉 All processes restored successfully!")
            ... except Exception as e:
            ...     print(f"❌ Recovery failed: {e}")
        """
        self._execute(["resurrect"])
        return self.list_processes()

    async def resurrect_processes_async(self) -> List[PM2Process]:
        """Resurrect previously saved processes from PM2's dump file asynchronously.

        Asynchronous version of resurrect_processes() that restores all processes
        that were previously saved without blocking the current thread.

        Returns:
            List[PM2Process]: List of all processes after resurrection

        Raises:
            PM2CommandError: If the resurrect command fails

        Example:
            >>> async def automated_recovery():
            ...     async with PM2Manager() as pm2:
            ...         try:
            ...             print("🔄 Starting automated recovery...")
            ...             processes = await pm2.resurrect_processes_async()
            ...
            ...             # Wait a moment for processes to fully start
            ...             await asyncio.sleep(5)
            ...
            ...             # Re-check process status
            ...             updated_processes = await pm2.list_processes_async()
            ...             online = [p for p in updated_processes if p.is_online]
            ...
            ...             print(f"📊 Recovery Summary:")
            ...             print(f"   Total processes: {len(updated_processes)}")
            ...             print(f"   Online processes: {len(online)}")
            ...             print(f"   Success rate: {len(online)/len(updated_processes)*100:.1f}%")
            ...
            ...             # Handle any failed processes
            ...             failed = [p for p in updated_processes if not p.is_online]
            ...             if failed:
            ...                 print(f"⚠️  Failed to start {len(failed)} processes:")
            ...                 for proc in failed:
            ...                     print(f"   - {proc.name}: {proc.status.value}")
            ...                     # Attempt individual restart
            ...                     try:
            ...                         await pm2.restart_process_async(name=proc.name)
            ...                         print(f"   ✅ Manually restarted {proc.name}")
            ...                     except Exception:
            ...                         print(f"   ❌ Failed to restart {proc.name}")
            ...
            ...             return updated_processes
            ...
            ...         except Exception as e:
            ...             print(f"❌ Recovery failed: {e}")
            ...             raise
        """
        await self._execute_async(["resurrect"])
        return await self.list_processes_async()

    def kill_daemon(self) -> bool:
        """Kill the PM2 daemon and all managed processes.

        Terminates the PM2 daemon and stops all processes under its management.
        This is a destructive operation that should be used with caution.

        Returns:
            bool: True if kill operation was successful

        Raises:
            PM2CommandError: If the kill command fails

        Warning:
            This will stop ALL PM2 processes and terminate the daemon.
            Use save_process_list() before this operation if you want
            to restore processes later.

        Example:
            >>> pm2 = PM2Manager()
            >>>
            >>> # Safe shutdown with backup
            >>> try:
            ...     # First, save current state
            ...     pm2.save_process_list()
            ...     print("✅ Process list backed up")
            ...
            ...     # Then kill daemon
            ...     success = pm2.kill_daemon()
            ...     if success:
            ...         print("🔴 PM2 daemon terminated")
            ...         print("   All processes have been stopped")
            ...         print("   Use 'pm2 resurrect' to restore processes")
            ... except Exception as e:
            ...     print(f"❌ Shutdown failed: {e}")
            >>>
            >>> # Emergency shutdown
            >>> pm2.kill_daemon()
            >>> print("💥 Emergency shutdown completed")
        """
        self._execute(["kill"])
        return True

    async def kill_daemon_async(self) -> bool:
        """Kill the PM2 daemon and all managed processes asynchronously.

        Asynchronous version of kill_daemon() that terminates the PM2 daemon
        and stops all processes without blocking the current thread.

        Returns:
            bool: True if kill operation was successful

        Raises:
            PM2CommandError: If the kill command fails

        Warning:
            This will stop ALL PM2 processes and terminate the daemon.

        Example:
            >>> async def graceful_system_shutdown():
            ...     async with PM2Manager() as pm2:
            ...         try:
            ...             print("🔄 Starting graceful shutdown sequence...")
            ...
            ...             # Step 1: Save current state
            ...             await pm2.save_process_list_async()
            ...             print("✅ Process state saved")
            ...
            ...             # Step 2: Get process list for logging
            ...             processes = await pm2.list_processes_async()
            ...             online_count = len([p for p in processes if p.is_online])
            ...             print(f"📊 Stopping {online_count} running processes")
            ...
            ...             # Step 3: Kill daemon
            ...             success = await pm2.kill_daemon_async()
            ...             if success:
            ...                 print("🔴 PM2 daemon terminated successfully")
            ...                 print("   System shutdown complete")
            ...                 return True
            ...
            ...         except Exception as e:
            ...             print(f"❌ Graceful shutdown failed: {e}")
            ...             print("   Attempting emergency shutdown...")
            ...             try:
            ...                 await pm2.kill_daemon_async()
            ...                 print("💥 Emergency shutdown completed")
            ...             except Exception:
            ...                 print("❌ Emergency shutdown also failed")
            ...                 raise
        """
        await self._execute_async(["kill"])
        return True


# Compatibility aliases for backward compatibility
PM2 = PM2Manager
AioPM2 = PM2Manager

# Export all public classes and functions
__all__ = [
    # Main classes
    "PM2Manager",
    "PM2Process",
    "ProcessMetrics",
    "ProcessEnvironment",
    "ProcessConfiguration",
    # Enums
    "ProcessStatus",
    "ProcessMode",
    "LogLevel",
    # Exceptions
    "PM2Error",
    "PM2ConnectionError",
    "PM2CommandError",
    "PM2ProcessError",
    "PM2ProcessNotFoundError",
    "PM2ProcessAlreadyExistsError",
    "PM2ProcessInvalidStateError",
    "PM2ConfigurationError",
    "PM2ValidationError",
    "PathIsFolderError",
    # Compatibility aliases
    "PM2",
    "AioPM2",
]
