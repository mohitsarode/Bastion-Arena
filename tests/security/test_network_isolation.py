"""Verification of Docker Compose network isolation and boundaries (SECURITY_MODEL.md)."""

from __future__ import annotations

from pathlib import Path

import yaml


def _load_compose() -> dict:
    compose_path = Path(__file__).parents[2] / "docker-compose.yml"
    assert compose_path.is_file(), f"docker-compose.yml not found at {compose_path}"
    with open(compose_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_four_isolated_internal_networks() -> None:
    """Verify that exactly four internal networks exist with no external gateway."""
    data = _load_compose()
    networks = data.get("networks", {})

    expected_networks = {"net_red", "net_blue", "net_model", "net_eval"}
    assert set(networks.keys()) == expected_networks

    for net_name, net_cfg in networks.items():
        assert net_cfg.get("internal") is True, (
            f"Network {net_name} must have 'internal: true' to block outbound internet egress"
        )


def test_arbiter_is_sole_network_intermediary() -> None:
    """Verify Arbiter bridges all 4 networks while worker cells are isolated."""
    data = _load_compose()
    services = data.get("services", {})

    # Arbiter must connect to all 4 networks
    arbiter_nets = set(services["arbiter"].get("networks", []))
    assert arbiter_nets == {"net_red", "net_blue", "net_model", "net_eval"}

    # Worker cells must connect ONLY to their dedicated network
    expected_memberships = {
        "red_worker": {"net_red"},
        "blue_worker": {"net_blue"},
        "model_worker": {"net_model"},
        "evaluator_worker": {"net_eval"},
    }

    for svc_name, expected_net in expected_memberships.items():
        svc_nets = set(services[svc_name].get("networks", []))
        assert svc_nets == expected_net, (
            f"Cell '{svc_name}' has networks {svc_nets}, expected strictly {expected_net}"
        )


def test_no_cross_cell_network_overlap() -> None:
    """Verify that no two worker cells share any network interface directly."""
    data = _load_compose()
    services = data.get("services", {})

    workers = ["red_worker", "blue_worker", "model_worker", "evaluator_worker"]
    for i in range(len(workers)):
        for j in range(i + 1, len(workers)):
            w1 = workers[i]
            w2 = workers[j]
            net1 = set(services[w1].get("networks", []))
            net2 = set(services[w2].get("networks", []))
            overlap = net1.intersection(net2)
            assert len(overlap) == 0, (
                f"Forbidden network overlap between '{w1}' and '{w2}': {overlap}"
            )


def test_host_port_binding_restricted_to_loopback() -> None:
    """Verify that no worker cell exposes ports, and Arbiter binds strictly to 127.0.0.1."""
    data = _load_compose()
    services = data.get("services", {})

    # Workers must not expose any host ports
    workers = ["red_worker", "blue_worker", "model_worker", "evaluator_worker"]
    for w in workers:
        assert "ports" not in services[w], (
            f"Worker cell '{w}' must not expose ports on host interfaces"
        )

    # Arbiter ports must be bound to 127.0.0.1 (loopback)
    arbiter_ports = services["arbiter"].get("ports", [])
    assert len(arbiter_ports) > 0, "Arbiter must expose port for local invocation"
    for port_binding in arbiter_ports:
        assert str(port_binding).startswith("127.0.0.1:"), (
            f"Port binding '{port_binding}' must be restricted strictly to loopback (127.0.0.1)"
        )


def test_simulated_packet_routing_isolation() -> None:
    """Simulate packet routing logic: Red cannot deliver packets to Blue or Model cells."""
    data = _load_compose()
    services = data.get("services", {})

    def can_route_directly(source_svc: str, dest_svc: str) -> bool:
        src_nets = set(services[source_svc].get("networks", []))
        dst_nets = set(services[dest_svc].get("networks", []))
        return len(src_nets.intersection(dst_nets)) > 0

    # Permitted routing (through Arbiter)
    assert can_route_directly("red_worker", "arbiter") is True
    assert can_route_directly("arbiter", "blue_worker") is True
    assert can_route_directly("arbiter", "model_worker") is True
    assert can_route_directly("arbiter", "evaluator_worker") is True

    # Forbidden direct routing
    assert can_route_directly("red_worker", "blue_worker") is False
    assert can_route_directly("red_worker", "model_worker") is False
    assert can_route_directly("red_worker", "evaluator_worker") is False
    assert can_route_directly("blue_worker", "model_worker") is False
    assert can_route_directly("blue_worker", "evaluator_worker") is False
    assert can_route_directly("model_worker", "evaluator_worker") is False
