# !/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""PM2 Python Library for Process Management

This exports:
    - PM2
    - AioPM2
    - PM2Process
    - PathIsFolderError
    
Example:
    ```python
    from pm2 import PM2, AioPM2, PM2Process, PathIsFolderError
    import asyncio

    async def main() -> PM2Process:
        pm2 = AioPM2()
        try:
            process = await pm2.start("path/to/your/file.py", name="my-process")
        except PathIsFolderError as e:
            print(e)
        print(process)
        await pm2.restart(name="my-process")
        return process
    ```
"""

import asyncio
import os
import subprocess
from json import dumps, loads
from time import time
from typing import Any, List, Optional

import aiofiles
from aylak.rich.console import Console

console = Console()

__version__ = "0.0.4"


class PathIsFolderError(Exception):
    pass


class PM2Process:
    pid: int = 0
    name: str = ""
    status: str = "online"
    pm_id: int = 0
    monit: dict = {}
    autorestart: bool = False
    namespace: str = "default"
    version: str = "N/A"
    mode: str = "fork"
    uptime: int = 0
    created_at: int = 0
    restart: int = 0
    user: str = ""
    cwd: str = ""
    exec_path: str = ""
    virtual_env: str = ""
    out_log: str = ""
    err_log: str = ""
    full_json: dict = {}

    def __init__(self, json_data: dict) -> None:
        self.name = json_data["name"]
        if json_data["pid"]:
            self.pid = json_data["pid"]
        if json_data["pm_id"]:
            self.pm_id = json_data["pm_id"]
        self.monit = json_data["monit"]
        self.autorestart = json_data["pm2_env"]["autorestart"]
        self.namespace = json_data["pm2_env"]["namespace"]
        if "versioning" in json_data["pm2_env"]:
            self.version = json_data["pm2_env"]["versioning"]
        self.mode = json_data["pm2_env"]["exec_mode"]
        self.uptime = int(time() - round(json_data["pm2_env"]["pm_uptime"] / 1000))
        if json_data["pm2_env"]["created_at"]:
            self.created_at = int(round(json_data["pm2_env"]["created_at"] / 1000))
        self.restart = json_data["pm2_env"]["restart_time"]
        self.status = json_data["pm2_env"]["status"]
        self.user = json_data["pm2_env"]["username"]
        self.json_data = json_data
        self.cwd = json_data["pm2_env"].get("pw_cwd")
        self.exec_path = json_data["pm2_env"].get("pm_exec_path")
        self.virtual_env = json_data["pm2_env"].get("env", {}).get("VIRTUAL_ENV")
        self.out_log = json_data["pm2_env"].get("pm_out_log_path")
        self.err_log = json_data["pm2_env"].get("pm_err_log_path")
        self.full_json = json_data

    def __str__(self):
        return f"{self.json()}"

    def __repr__(self):
        return f"<PM2Process {self.name} ({self.pid}) ({self.status})>"

    def json(self, markup_print: bool = False):
        if markup_print:
            console.print_json(data=self.full_json)
        return dumps(self.full_json, indent=4, ensure_ascii=True)


class AioPM2:
    def __init__(self, command_path: str = "pm2") -> None:
        self.COMMAND = [command_path]
        pass

    async def execute_command(self, cmd: List[str]) -> tuple[str, str]:
        process = await asyncio.create_subprocess_shell(
            " ".join(cmd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise Exception(f"Command failed with error: {stderr.decode()}")
        return stdout.decode(), stderr.decode()

    async def list(self) -> List[PM2Process]:
        stdout, stderr = await self.execute_command(self.COMMAND + ["jlist"])
        return [PM2Process(process) for process in loads(stdout)]

    async def get(
        self,
        pid: int = None,
        pm_id: int = None,
        name: str = None,
    ) -> PM2Process:
        processes = await self.list()
        for process in processes:
            if (
                (pid and process.pid == pid)
                or (pm_id and process.pm_id == pm_id)
                or (name and process.name == name)
            ):
                return process
        return None

    async def start(
        self, path: str, name: str = None, extra_args: List[str] = None
    ) -> Optional[PM2Process]:
        extra_args = extra_args or []
        if os.path.isdir(path):
            if "__main__.py" in os.listdir(path):
                path = os.path.join(path, "__main__.py")
            else:
                raise PathIsFolderError("Path is a folder; a file is expected.")
        cmd = (
            self.COMMAND
            + ["start", path]
            + (["--name", name] if name else [])
            + extra_args
        )
        await self.execute_command(cmd)
        return await self.get(
            pm_id=max([process.pm_id for process in await self.list()])
        )

    async def modify_process(
        self,
        action: str,
        pid: int = None,
        pm_id: int = None,
        name: str = None,
        extra_args: List[str] = None,
    ) -> bool:
        extra_args = extra_args or []
        process = await self.get(pid=pid, pm_id=pm_id, name=name)
        if process:
            cmd = self.COMMAND + [action, str(process.pm_id)] + extra_args
            await self.execute_command(cmd)
            return await self.get(pid=pid, pm_id=pm_id, name=name)
        return False

    async def stop(
        self, pid: int = None, pm_id: int = None, name: str = None
    ) -> PM2Process:
        return await self.modify_process("stop", pid, pm_id, name)

    async def restart(
        self, pid: int = None, pm_id: int = None, name: str = None
    ) -> PM2Process:
        return await self.modify_process("restart", pid, pm_id, name)

    async def delete(
        self, pid: int = None, pm_id: int = None, name: str = None
    ) -> PM2Process:
        return await self.modify_process("delete", pid, pm_id, name)

    async def logs(
        self,
        lines: int = 500,
        pid: int = None,
        pm_id: int = None,
        name: str = None,
        errors: bool = False,
    ) -> str:
        process = await self.get(pid=pid, pm_id=pm_id, name=name)
        async with aiofiles.open(process.out_log, "r", encoding="utf-8") as f:
            out_log = "\n".join(await f.readlines()[-lines:])
        async with aiofiles.open(process.err_log, "r", encoding="utf-8") as f:
            err_log = "\n".join(await f.readlines()[-lines:])
        return (out_log, err_log) if errors else out_log


# sync PM2
class PM2:
    def __init__(self, command_path: str = "pm2") -> None:
        self.COMMAND = [command_path]
        pass

    def execute_command(self, cmd: List[str]) -> tuple[str, str]:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise Exception(f"Command failed with error: {stderr.decode()}")
        return stdout.decode(), stderr.decode()

    def list(self) -> List[PM2Process]:
        stdout, stderr = self.execute_command(self.COMMAND + ["jlist"])
        return [PM2Process(process) for process in loads(stdout)]

    def get(
        self,
        pid: int = None,
        pm_id: int = None,
        name: str = None,
    ) -> PM2Process:
        processes = self.list()
        for process in processes:
            if (
                (pid and process.pid == pid)
                or (pm_id and process.pm_id == pm_id)
                or (name and process.name == name)
            ):
                return process
        return None

    def start(
        self, path: str, name: str = None, extra_args: List[str] = None
    ) -> Optional[PM2Process]:
        extra_args = extra_args or []
        if os.path.isdir(path):
            if "__main__.py" in os.listdir(
                path
            ):  # TODO: Folder initialization for languages ​​other than Python will be added
                path = os.path.join(path, "__main__.py")
            else:
                raise PathIsFolderError("Path is a folder; a file is expected.")
        cmd = (
            self.COMMAND
            + ["start", path]
            + (["--name", name] if name else [])
            + extra_args
        )
        self.execute_command(cmd)
        return self.get(pm_id=max([process.pm_id for process in self.list()]))

    def modify_process(
        self,
        action: str,
        pid: int = None,
        pm_id: int = None,
        name: str = None,
        extra_args: List[str] = None,
    ) -> bool:
        extra_args = extra_args or []
        process = self.get(pid=pid, pm_id=pm_id, name=name)
        if process:
            cmd = self.COMMAND + [action, str(process.pm_id)] + extra_args
            self.execute_command(cmd)
            return self.get(pid=pid, pm_id=pm_id, name=name)
        return False

    def stop(self, pid: int = None, pm_id: int = None, name: str = None) -> bool:
        return self.modify_process("stop", pid, pm_id, name)

    def restart(self, pid: int = None, pm_id: int = None, name: str = None) -> bool:
        return self.modify_process("restart", pid, pm_id, name)

    def delete(self, pid: int = None, pm_id: int = None, name: str = None) -> bool:
        return self.modify_process("delete", pid, pm_id, name)

    def logs(
        self,
        lines: int = 500,
        pid: int = None,
        pm_id: int = None,
        name: str = None,
        errors: bool = False,
    ) -> str:
        process = self.get(pid=pid, pm_id=pm_id, name=name)
        with open(process.out_log, "r", encoding="utf-8") as f:
            out_log = "\n".join(f.readlines()[-lines:])
        with open(process.err_log, "r", encoding="utf-8") as f:
            err_log = "\n".join(f.readlines()[-lines:])
        return (out_log, err_log) if errors else out_log
