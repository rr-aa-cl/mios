"""Small shared types; the host tool requires only Python's standard library."""
from dataclasses import asdict, dataclass, field
from pathlib import Path
import subprocess


@dataclass
class Check:
    id: str
    status: str
    message: str
    remediation: str = ""
    details: dict = field(default_factory=dict)

    def __post_init__(self):
        self.status = self.status.upper()
        if self.status not in {"PASS", "WARN", "FAIL", "UNKNOWN"}:
            raise ValueError(f"Invalid check status: {self.status}")

    def to_dict(self):
        return asdict(self)


@dataclass
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False


class Runner:
    def run(self, argv, timeout=10, input=None, env=None):
        try:
            result = subprocess.run(
                list(argv), input=input, text=True, capture_output=True,
                timeout=timeout, check=False, env=env,
            )
            return CommandResult(result.returncode, result.stdout, result.stderr)
        except FileNotFoundError:
            return CommandResult(127, stderr=f"Command not found: {argv[0]}")
        except PermissionError as error:
            return CommandResult(126, stderr=str(error))
        except subprocess.TimeoutExpired:
            return CommandResult(124, stderr=f"Command exceeded {timeout} seconds", timed_out=True)
        except OSError as error:
            return CommandResult(126, stderr=str(error))


@dataclass
class Context:
    repo_root: Path
    profile: str = "motion"
    robot_ip: str = "192.168.4.100"
    control_cpu: int = 6
    controller_priority: int = 80
    irq_priority: int = 90
    worker_cpus: str = "0-5,8-19"
    nonrt_cpus: str = "0-5,8-19"
    ping: bool = True
    sys_root: Path = Path("/sys")
    proc_root: Path = Path("/proc")
    kernel_config_path: Path | None = None
    images: dict = field(default_factory=dict)
    contract_version: str = "0.1.0"
    docker_arch: str = "amd64"
    compose: dict = field(default_factory=dict)
