import asyncio
import shutil
from dataclasses import dataclass

from .config import Settings
from .models import AegisDispatchRequest


@dataclass(frozen=True)
class AegisResult:
    return_code: int
    stdout: str
    stderr: str
    command: list[str]


class AegisUnavailable(RuntimeError):
    pass


async def dispatch_aegis(request: AegisDispatchRequest, settings: Settings) -> AegisResult:
    if not settings.aegis_execution_enabled:
        raise AegisUnavailable("AEGIS execution is disabled by policy.")

    script = settings.aegis_path
    if script is None or not script.is_file():
        raise AegisUnavailable("Configured AEGIS script path does not exist.")

    executable = shutil.which(settings.aegis_powershell_executable)
    if not executable:
        raise AegisUnavailable("PowerShell executable is unavailable on this host.")

    command = [
        executable,
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-File",
        str(script),
        "-Mode",
        request.mode,
    ]
    if request.mode in {"Audit", "Hunt", "Enterprise"}:
        command.extend(["-ScanMinutes", str(request.scan_minutes)])
    if request.generate_report and request.mode in {"Audit", "Hunt", "Enterprise"}:
        command.append("-GenerateReport")

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=settings.aegis_timeout_seconds)
    except TimeoutError as exc:
        process.kill()
        await process.communicate()
        raise AegisUnavailable("AEGIS execution exceeded the configured timeout.") from exc

    return AegisResult(
        return_code=process.returncode or 0,
        stdout=stdout.decode("utf-8", errors="replace")[-20_000:],
        stderr=stderr.decode("utf-8", errors="replace")[-20_000:],
        command=command,
    )
