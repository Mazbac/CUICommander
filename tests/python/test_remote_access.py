from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call, patch

from cuicommander.action_gateway import ActionGateway
from cuicommander import remote_access
from cuicommander.remote_access import (
    _choose_funnel_port,
    _funnel_matches,
    _occupied_funnel_ports,
    _public_origin,
)


class RemoteAccessPlanningTests(unittest.TestCase):
    def test_remote_state_loader_accepts_utf8_bom(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "remote.json"
            path.write_text(
                '\ufeff{"mode":"action-node","enabled":true}',
                encoding="utf-8",
            )
            with patch.object(remote_access, "_state_path", return_value=path):
                state = remote_access._load_state()
        self.assertEqual(state["mode"], "action-node")
        self.assertTrue(state["enabled"])

    def test_existing_tailscale_services_are_not_selected(self) -> None:
        config = {
            "TCP": {"443": {"HTTPS": True}, "8443": {"HTTPS": True}},
            "Web": {},
            "AllowFunnel": {},
        }
        self.assertEqual(_occupied_funnel_ports(config), {443, 8443})
        self.assertEqual(_choose_funnel_port(config), 10000)

    def test_web_entries_also_reserve_funnel_ports(self) -> None:
        config = {
            "Web": {
                "pc.example.ts.net:443": {"Handlers": {}},
                "pc.example.ts.net:8443": {"Handlers": {}},
            }
        }
        self.assertEqual(_occupied_funnel_ports(config), {443, 8443})
        self.assertEqual(_choose_funnel_port(config), 10000)

    def test_all_funnel_ports_in_use_fails_closed(self) -> None:
        config = {"TCP": {"443": {}, "8443": {}, "10000": {}}}
        with self.assertRaises(RuntimeError):
            _choose_funnel_port(config)

    def test_funnel_match_requires_exact_owned_mapping(self) -> None:
        config = {
            "Web": {
                "pc.example.ts.net:10000": {
                    "Handlers": {"/": {"Proxy": "http://127.0.0.1:8766"}}
                }
            },
            "AllowFunnel": {"pc.example.ts.net:10000": True},
        }
        self.assertTrue(
            _funnel_matches(
                config,
                "pc.example.ts.net",
                10000,
                "http://127.0.0.1:8766",
            )
        )
        self.assertFalse(
            _funnel_matches(
                config,
                "pc.example.ts.net",
                10000,
                "http://127.0.0.1:9999",
            )
        )

    def test_public_origin_uses_standard_and_nonstandard_https_ports(self) -> None:
        self.assertEqual(_public_origin("pc.example.ts.net", 443), "https://pc.example.ts.net")
        self.assertEqual(
            _public_origin("pc.example.ts.net", 10000),
            "https://pc.example.ts.net:10000",
        )


class ActionGatewayTests(unittest.TestCase):
    def test_openapi_payload_is_rewritten_to_public_origin(self) -> None:
        gateway = ActionGateway()
        gateway._public_origin = "https://pc.example.ts.net:10000"
        raw, content_type = gateway._rewrite_public_payload(
            "/cuicommander/v1/openapi",
            json.dumps({"servers": [{"url": "http://127.0.0.1:8188"}]}).encode(),
            "application/json",
        )
        payload = json.loads(raw)
        self.assertEqual(
            payload["servers"],
            [{"url": "https://pc.example.ts.net:10000"}],
        )
        self.assertIn("application/json", content_type)


class RemoteAccessLifecycleTests(unittest.IsolatedAsyncioTestCase):
    def test_configured_mapping_remains_repairable_when_gateway_is_down(self) -> None:
        state = {
            "provider": "tailscale",
            "enabled": True,
            "gatewayPort": 8766,
            "funnelPort": 10000,
            "publicBaseUrl": "https://pc.example.ts.net:10000",
        }
        snapshot = {
            "installed": True,
            "version": "1.0",
            "connected": True,
            "dnsName": "pc.example.ts.net",
            "funnel": {
                "TCP": {"443": {}, "8443": {}},
                "Web": {
                    "pc.example.ts.net:443": {
                        "Handlers": {"/": {"Proxy": "http://127.0.0.1:8766"}}
                    }
                },
                "AllowFunnel": {"pc.example.ts.net:443": True},
            },
        }
        with (
            patch.object(remote_access, "_load_state", return_value=state),
            patch.object(remote_access, "_tailscale_snapshot", return_value=snapshot),
        ):
            status = remote_access._status_payload()
        self.assertIsNone(status["recommendedFunnelPort"])
        self.assertFalse(status["active"])
        self.assertFalse(status["customGptCompatible"])

    async def test_enable_rolls_back_public_url_and_owned_funnel_on_state_write_failure(self) -> None:
        initial = {
            "installed": True,
            "connected": True,
            "dnsName": "pc.example.ts.net",
            "funnel": {
                "TCP": {"8443": {}},
                "Web": {},
                "AllowFunnel": {},
            },
        }
        refreshed = {
            **initial,
            "funnel": {
                "TCP": {"443": {}, "8443": {}},
                "Web": {
                    "pc.example.ts.net:443": {
                        "Handlers": {"/": {"Proxy": "http://127.0.0.1:8766"}}
                    }
                },
                "AllowFunnel": {"pc.example.ts.net:443": True},
            },
        }
        command_result = SimpleNamespace(returncode=0, stdout="", stderr="")
        set_public = MagicMock()
        with (
            patch.object(remote_access, "_tailscale_snapshot", side_effect=[initial, refreshed]),
            patch.object(remote_access, "_load_state", return_value={}),
            patch.object(remote_access, "_choose_gateway_port", return_value=8766),
            patch.object(remote_access, "public_base_url", return_value="https://manual.example"),
            patch.object(remote_access, "set_public_base_url", set_public),
            patch.object(remote_access, "_write_state", side_effect=RuntimeError("disk write failed")),
            patch.object(remote_access, "_run_tailscale", return_value=command_result) as run_ts,
            patch.object(remote_access, "_verify_public_gateway", new=AsyncMock()),
            patch.object(remote_access.GATEWAY, "start", new=AsyncMock()),
            patch.object(remote_access.GATEWAY, "stop", new=AsyncMock()) as stop_gateway,
        ):
            with self.assertRaisesRegex(RuntimeError, "disk write failed"):
                await remote_access.enable_tailscale_remote_access()

        self.assertEqual(
            set_public.call_args_list,
            [call("https://pc.example.ts.net"), call("https://manual.example")],
        )
        self.assertEqual(run_ts.call_count, 2)
        stop_gateway.assert_awaited_once()

    async def test_enable_uses_isolated_action_node_when_system_443_is_occupied(self) -> None:
        system = {
            "installed": True,
            "version": "1.0",
            "connected": True,
            "dnsName": "pc.example.ts.net",
            "funnel": {"TCP": {"443": {}}, "Web": {}, "AllowFunnel": {}},
        }
        action_initial = {
            "installed": True,
            "version": "1.0",
            "connected": True,
            "dnsName": "cuicommander-pc.example.ts.net",
            "funnel": {"TCP": {}, "Web": {}, "AllowFunnel": {}},
        }
        action_refreshed = {
            **action_initial,
            "funnel": {
                "TCP": {"443": {}},
                "Web": {
                    "cuicommander-pc.example.ts.net:443": {
                        "Handlers": {"/": {"Proxy": "http://127.0.0.1:8766"}}
                    }
                },
                "AllowFunnel": {"cuicommander-pc.example.ts.net:443": True},
            },
        }
        command_result = SimpleNamespace(returncode=0, stdout="", stderr="")
        write_state = MagicMock()
        set_public = MagicMock()
        with (
            patch.object(remote_access, "_load_state", return_value={}),
            patch.object(remote_access, "_tailscale_snapshot", side_effect=[system, action_refreshed]),
            patch.object(remote_access, "_try_action_node_snapshot", return_value=action_initial),
            patch.object(remote_access, "_choose_gateway_port", return_value=8766),
            patch.object(remote_access, "public_base_url", return_value=""),
            patch.object(remote_access, "set_public_base_url", set_public),
            patch.object(remote_access, "_write_state", write_state),
            patch.object(remote_access, "_run_tailscale", return_value=command_result) as run_ts,
            patch.object(remote_access, "_verify_public_gateway", new=AsyncMock()),
            patch.object(remote_access, "_status_payload", return_value={"active": True}),
            patch.object(remote_access.GATEWAY, "start", new=AsyncMock()),
            patch.object(remote_access.GATEWAY, "stop", new=AsyncMock()),
        ):
            result = await remote_access.enable_tailscale_remote_access()

        self.assertEqual(result, {"active": True})
        written = write_state.call_args.args[0]
        self.assertEqual(written["mode"], "action-node")
        self.assertEqual(written["funnelPort"], 443)
        self.assertEqual(
            written["publicBaseUrl"],
            "https://cuicommander-pc.example.ts.net",
        )
        set_public.assert_called_once_with("https://cuicommander-pc.example.ts.net")
        self.assertEqual(run_ts.call_args.args[-1], remote_access._ACTION_NODE_SOCKET)

    async def test_enable_refuses_port_10000_fallback_for_custom_gpt(self) -> None:
        system = {
            "installed": True,
            "version": "1.0",
            "connected": True,
            "dnsName": "pc.example.ts.net",
            "funnel": {"TCP": {"443": {}, "8443": {}}, "Web": {}, "AllowFunnel": {}},
        }
        with (
            patch.object(remote_access, "_load_state", return_value={}),
            patch.object(remote_access, "_tailscale_snapshot", return_value=system),
            patch.object(remote_access, "_try_action_node_snapshot", return_value=None),
            patch.object(remote_access, "public_base_url", return_value=""),
        ):
            with self.assertRaisesRegex(RuntimeError, "isolated Custom GPT endpoint"):
                await remote_access.enable_tailscale_remote_access()

    def test_prepare_action_node_starts_login_when_needed(self) -> None:
        with (
            patch.object(remote_access, "_install_action_node_task") as install,
            patch.object(remote_access, "_start_action_node_task") as start_task,
            patch.object(remote_access, "_wait_for_action_node", return_value={"connected": False}),
            patch.object(remote_access, "_begin_action_node_login", return_value="https://login.tailscale.com/a/test") as begin_login,
            patch.object(remote_access, "_status_payload", return_value={"actionNodeRunning": True}),
        ):
            result = remote_access.prepare_tailscale_action_node()

        self.assertEqual(result, {"actionNodeRunning": True})
        install.assert_called_once_with()
        start_task.assert_called_once_with()
        begin_login.assert_called_once_with()

    async def test_disable_restores_previous_manual_https_origin(self) -> None:
        state = {
            "provider": "tailscale",
            "enabled": True,
            "gatewayPort": 8766,
            "funnelPort": 10000,
            "publicBaseUrl": "https://pc.example.ts.net:10000",
            "previousPublicBaseUrl": "https://manual.example",
            "ownsFunnel": True,
        }
        snapshot = {
            "installed": True,
            "connected": True,
            "dnsName": "pc.example.ts.net",
            "funnel": {
                "Web": {
                    "pc.example.ts.net:10000": {
                        "Handlers": {"/": {"Proxy": "http://127.0.0.1:8766"}}
                    }
                },
                "AllowFunnel": {"pc.example.ts.net:10000": True},
            },
        }
        command_result = SimpleNamespace(returncode=0, stdout="", stderr="")
        set_public = MagicMock()
        write_state = MagicMock()
        with (
            patch.object(remote_access, "_load_state", return_value=state),
            patch.object(remote_access, "_tailscale_snapshot", return_value=snapshot),
            patch.object(
                remote_access,
                "public_base_url",
                return_value="https://pc.example.ts.net:10000",
            ),
            patch.object(remote_access, "set_public_base_url", set_public),
            patch.object(remote_access, "_write_state", write_state),
            patch.object(remote_access, "_run_tailscale", return_value=command_result) as run_ts,
            patch.object(remote_access, "_status_payload", return_value={"active": False}),
            patch.object(remote_access.GATEWAY, "stop", new=AsyncMock()) as stop_gateway,
        ):
            result = await remote_access.disable_tailscale_remote_access()

        self.assertEqual(result, {"active": False})
        set_public.assert_called_once_with("https://manual.example")
        self.assertEqual(run_ts.call_count, 1)
        stop_gateway.assert_awaited_once()
        written = write_state.call_args.args[0]
        self.assertFalse(written["enabled"])
        self.assertFalse(written["ownsFunnel"])

    async def test_disable_never_removes_matching_funnel_it_does_not_own(self) -> None:
        state = {
            "provider": "tailscale",
            "enabled": True,
            "gatewayPort": 8766,
            "funnelPort": 10000,
            "publicBaseUrl": "https://pc.example.ts.net:10000",
            "previousPublicBaseUrl": "",
            "ownsFunnel": False,
        }
        snapshot = {
            "installed": True,
            "connected": True,
            "dnsName": "pc.example.ts.net",
            "funnel": {
                "Web": {
                    "pc.example.ts.net:10000": {
                        "Handlers": {"/": {"Proxy": "http://127.0.0.1:8766"}}
                    }
                },
                "AllowFunnel": {"pc.example.ts.net:10000": True},
            },
        }
        run_ts = MagicMock()
        with (
            patch.object(remote_access, "_load_state", return_value=state),
            patch.object(remote_access, "_tailscale_snapshot", return_value=snapshot),
            patch.object(
                remote_access,
                "public_base_url",
                return_value="https://pc.example.ts.net:10000",
            ),
            patch.object(remote_access, "set_public_base_url"),
            patch.object(remote_access, "_write_state"),
            patch.object(remote_access, "_run_tailscale", run_ts),
            patch.object(remote_access, "_status_payload", return_value={"active": False}),
            patch.object(remote_access.GATEWAY, "stop", new=AsyncMock()),
        ):
            await remote_access.disable_tailscale_remote_access()

        run_ts.assert_not_called()


if __name__ == "__main__":
    unittest.main()
