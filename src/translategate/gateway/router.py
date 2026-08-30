"""Route requests to translategate microservices through the registry."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from translategate.gateway.circuit import CircuitBreaker
from translategate.gateway.middleware import GatewayMiddleware
from translategate.observability.metrics import MetricsRegistry
from translategate.observability.tracer import Tracer

SERVICES: tuple[str, ...] = ("translate", "qa", "glossary")


class GatewayRouter:
    def __init__(self) -> None:
        self.middleware = GatewayMiddleware()
        self.metrics = MetricsRegistry()
        self.tracer = Tracer()
        self.circuits = {name: CircuitBreaker() for name in SERVICES}
        self.handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            name: self._echo(name) for name in SERVICES
        }

    @staticmethod
    def _echo(name: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
        def handler(payload: dict[str, Any]) -> dict[str, Any]:
            return {"service": name, "ok": True, "echo": dict(payload)}

        return handler

    def dispatch(self, service: str, payload: dict[str, Any]) -> dict[str, Any]:
        if service not in self.handlers:
            raise KeyError(f"unknown service {service!r}")
        circuit = self.circuits[service]
        if not circuit.allow():
            self.metrics.inc("gateway_rejected_total", service=service)
            raise RuntimeError(f"circuit open for {service}")
        envelope = self.middleware.wrap(service, payload)
        span = self.tracer.start(service, envelope["request_id"])
        try:
            result = self.handlers[service](envelope["payload"])
            circuit.record_success()
            self.metrics.inc("gateway_ok_total", service=service)
            span.finish("ok")
            return {**envelope, "result": result}
        except Exception:
            circuit.record_failure()
            self.metrics.inc("gateway_error_total", service=service)
            span.finish("error")
            raise
