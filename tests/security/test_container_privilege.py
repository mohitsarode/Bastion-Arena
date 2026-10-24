"""Verification of container privilege boundaries and hardening (SECURITY_MODEL.md)."""

from __future__ import annotations

import json
from pathlib import Path

import yaml


def _root_dir() -> Path:
    return Path(__file__).parents[2]


def _load_compose() -> dict:
    compose_path = _root_dir() / "docker-compose.yml"
    with open(compose_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_no_docker_socket_mounts() -> None:
    """Audit test asserting that no cell mounts the host Docker socket."""
    data = _load_compose()
    services = data.get("services", {})

    forbidden_socket_strings = ["docker.sock", "dockerDesktopLinuxEngine"]

    for svc_name, svc_cfg in services.items():
        volumes = svc_cfg.get("volumes", [])
        for vol in volumes:
            vol_str = str(vol)
            for forbidden in forbidden_socket_strings:
                assert forbidden not in vol_str, (
                    f"Security violation: Service '{svc_name}' mounts Docker socket: {vol_str}"
                )


def test_capabilities_dropped_all_services() -> None:
    """Verify that cap_drop: [ALL] is enforced across every container."""
    data = _load_compose()
    services = data.get("services", {})

    for svc_name, svc_cfg in services.items():
        cap_drop = svc_cfg.get("cap_drop", [])
        assert "ALL" in cap_drop, f"Service '{svc_name}' must drop ALL Linux capabilities"


def test_no_new_privileges_enforced() -> None:
    """Verify that no-new-privileges is configured for every container."""
    data = _load_compose()
    services = data.get("services", {})

    for svc_name, svc_cfg in services.items():
        sec_opt = svc_cfg.get("security_opt", [])
        assert "no-new-privileges:true" in sec_opt, (
            f"Service '{svc_name}' must enforce 'no-new-privileges:true'"
        )


def test_read_only_root_filesystem_with_tmpfs() -> None:
    """Verify read-only root filesystems and constrained tmpfs mounts."""
    data = _load_compose()
    services = data.get("services", {})

    for svc_name, svc_cfg in services.items():
        assert svc_cfg.get("read_only") is True, (
            f"Service '{svc_name}' must use a read-only root filesystem"
        )

        tmpfs = svc_cfg.get("tmpfs", [])
        assert len(tmpfs) > 0, f"Service '{svc_name}' must specify a temporary tmpfs mount"
        tmpfs_entry = str(tmpfs[0])
        assert "noexec" in tmpfs_entry, f"Service '{svc_name}' tmpfs mount must have 'noexec'"
        assert "nosuid" in tmpfs_entry, f"Service '{svc_name}' tmpfs mount must have 'nosuid'"


def test_non_root_user_enforced() -> None:
    """Verify that containers run as non-root user (UID 10001)."""
    data = _load_compose()
    services = data.get("services", {})

    for svc_name, svc_cfg in services.items():
        user = svc_cfg.get("user")
        assert user == "10001:10001", (
            f"Service '{svc_name}' must run as unprivileged user 10001:10001"
        )

    # Also verify Dockerfile.worker
    dockerfile_path = _root_dir() / "infra" / "docker" / "Dockerfile.worker"
    assert dockerfile_path.is_file()
    content = dockerfile_path.read_text(encoding="utf-8")
    assert "USER 10001:10001" in content, (
        "Dockerfile.worker must drop privileges with USER 10001:10001"
    )


def test_resource_limits_configured() -> None:
    """Verify memory, CPU, and PID limits are configured for denial-of-service defense."""
    data = _load_compose()
    services = data.get("services", {})

    for svc_name, svc_cfg in services.items():
        limits = svc_cfg.get("deploy", {}).get("resources", {}).get("limits", {})
        assert "cpus" in limits, f"Service '{svc_name}' must specify CPU limit"
        assert "memory" in limits, f"Service '{svc_name}' must specify memory limit"
        assert "pids" in limits, f"Service '{svc_name}' must specify PID limit"


def test_seccomp_profile_restricts_dangerous_syscalls() -> None:
    """Verify seccomp profile JSON blocks kernel exploitation syscalls."""
    seccomp_path = _root_dir() / "infra" / "docker" / "seccomp_profile.json"
    assert seccomp_path.is_file(), "seccomp_profile.json must exist"

    with open(seccomp_path, encoding="utf-8") as f:
        profile = json.load(f)

    blocked_syscalls: set[str] = set()
    for rule in profile.get("syscalls", []):
        if rule.get("action") == "SCMP_ACT_ERRNO":
            blocked_syscalls.update(rule.get("names", []))

    critical_forbidden = {
        "ptrace",
        "process_vm_readv",
        "process_vm_writev",
        "kexec_load",
        "bpf",
        "mount",
        "umount2",
        "reboot",
        "sys_chroot",
    }
    for syscall in critical_forbidden:
        assert syscall in blocked_syscalls, (
            f"Seccomp profile must block critical dangerous syscall '{syscall}'"
        )
