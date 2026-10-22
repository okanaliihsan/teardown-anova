"""MCP sunucusu testleri (sözleşme: tek araç `power_analysis`).

Gerçek stdio JSON-RPC alt süreci + CLI ≡ MCP eşdeğerliği (bayt düzeyinde).
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import unittest

from oracle import ROOT, SRC, VECTORS
from test_cli import REFERENCE_VECTORS, argv_from, oracle_params

from anova_clone import mcp_server


def _env():
    env = dict(os.environ)
    env["PYTHONPATH"] = SRC + os.pathsep + env.get("PYTHONPATH", "")
    return env


class McpProcess:
    def __init__(self, cmd=None):
        cmd = cmd or [sys.executable, "-m", "anova_clone.mcp_server"]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, encoding="utf-8",
                                     env=_env(), cwd=ROOT, bufsize=1)
        self._id = 0

    def send_raw(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read(self):
        line = self.proc.stdout.readline()
        if not line:
            raise RuntimeError("sunucu yanıt vermedi: " + self.proc.stderr.read())
        return json.loads(line)

    def request(self, method, params=None):
        self._id += 1
        msg = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params is not None:
            msg["params"] = params
        self.send_raw(json.dumps(msg))
        resp = self.read()
        assert resp.get("id") == self._id, resp
        return resp

    def notify(self, method):
        self.send_raw(json.dumps({"jsonrpc": "2.0", "method": method}))

    def call(self, arguments):
        return self.request("tools/call", {"name": "power_analysis", "arguments": arguments})

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        finally:
            self.proc.stdout.close()
            self.proc.stderr.close()


def handshake(client):
    r = client.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                      "clientInfo": {"name": "unittest", "version": "0"}})
    client.notify("notifications/initialized")
    return r


def run_cli(params):
    return subprocess.run([sys.executable, "-m", "anova_clone.cli", *argv_from(params)],
                          capture_output=True, text=True, env=_env(), cwd=ROOT, timeout=60)


def mcp_arguments(params: dict) -> dict:
    """CLI string değerlerini JSON sayılarına çevirir (test/mode string kalır;
    sayıya çevrilemeyenler string olarak gider — MCP de sözleşme hatası dönmeli)."""
    out = {}
    for k, v in params.items():
        if k in ("test", "mode"):
            out[k] = v
            continue
        try:
            x = float(v)
            out[k] = int(x) if x.is_integer() and "." not in v and "e" not in v.lower() else x
        except ValueError:
            out[k] = v
    return out


# Her hata kodundan en az bir vaka + başka aile
EXTRA_CASES = {
    "MISSING_PARAM": {"test": "anova-oneway", "mode": "a-priori", "f": "0.25",
                      "alpha": "0.05", "groups": "3"},
    "UNKNOWN_PARAM": {"test": "anova-oneway", "mode": "post-hoc", "f": "0.25",
                      "alpha": "0.05", "power": "0.8", "n_total": "100", "groups": "3"},
    "UNKNOWN_PARAM-2": {"test": "anova-oneway", "mode": "a-priori", "f": "0.25",
                        "alpha": "0.05", "power": "0.8", "groups": "3", "tails": "2"},
    "INVALID_VALUE": {"test": "anova-oneway", "mode": "a-priori", "f": "abc",
                      "alpha": "0.05", "power": "0.8", "groups": "3"},
    "INVALID_VALUE-int": {"test": "anova-oneway", "mode": "post-hoc", "f": "0.25",
                          "alpha": "0.05", "n_total": "159.6", "groups": "3"},
    "OUT_OF_RANGE": {"test": "anova-oneway", "mode": "a-priori", "f": "60",
                     "alpha": "0.05", "power": "0.8", "groups": "3"},
    "INCONSISTENT": {"test": "anova-oneway", "mode": "a-priori", "f": "0.25",
                     "alpha": "0.05", "power": "0.04", "groups": "3"},
    "UNSUPPORTED-test": {"test": "t2-indep", "mode": "a-priori", "d": "0.5",
                         "alpha": "0.05", "power": "0.8"},
    "UNSUPPORTED-mode": {"test": "anova-oneway", "mode": "sensitivity", "alpha": "0.05",
                         "power": "0.95", "n_total": "100", "groups": "5"},
    "warning": {"test": "anova-oneway", "mode": "post-hoc", "f": "0.25", "alpha": "0.05",
                "n_total": "100", "groups": "3"},
}


class TestMcpProtocol(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = McpProcess()
        cls.init = handshake(cls.client)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_initialize(self):
        res = self.init["result"]
        self.assertEqual(res["protocolVersion"], "2025-06-18")
        self.assertEqual(res["capabilities"], {"tools": {}})
        self.assertEqual(res["serverInfo"], {"name": "anova-power-clone", "version": "1.1.0"})
        self.assertEqual(self.client.request("initialize", {})["result"]["protocolVersion"],
                         "2025-06-18")

    def test_ping(self):
        self.assertEqual(self.client.request("ping")["result"], {})

    def test_tools_list_tek_arac(self):
        tools = self.client.request("tools/list")["result"]["tools"]
        self.assertEqual([t["name"] for t in tools], ["power_analysis"])
        schema = tools[0]["inputSchema"]
        self.assertEqual(schema["required"], ["test", "mode"])
        self.assertEqual(set(schema["properties"]),
                         {"test", "mode", "f", "alpha", "power", "groups", "n_total"})
        self.assertEqual(schema["properties"]["test"]["type"], "string")
        self.assertNotIn("enum", schema["properties"]["test"])
        for name in ("f", "alpha", "power", "groups", "n_total"):
            self.assertEqual(schema["properties"][name]["type"], "number")
        for name, prop in schema["properties"].items():
            self.assertTrue(prop["description"], name)
        self.assertIn("a-priori", tools[0]["description"])
        self.assertIn("post-hoc", tools[0]["description"])

    def test_basari_ve_structured(self):
        r = self.client.call({"test": "anova-oneway", "mode": "a-priori", "f": 0.25,
                              "alpha": 0.05, "power": 0.95, "groups": 5})["result"]
        self.assertFalse(r["isError"])
        self.assertEqual(json.loads(r["content"][0]["text"]), r["structuredContent"])
        self.assertEqual(r["structuredContent"]["n_total"], 305)

    def test_eksik_ve_bilinmeyen_arguman_sozlesme_hatasi_doner(self):
        r = self.client.call({"test": "anova-oneway", "mode": "a-priori"})["result"]
        self.assertTrue(r["isError"])
        self.assertEqual(r["structuredContent"]["code"], "MISSING_PARAM")
        r = self.client.call({"mode": "a-priori"})["result"]
        self.assertEqual(r["structuredContent"], {
            "error": "Missing required parameter: test.", "code": "MISSING_PARAM",
            "field": "test"})
        r = self.client.call({"test": "anova-oneway", "mode": "a-priori", "f": 0.25,
                              "alpha": 0.05, "power": 0.8, "groups": 3, "x": 1})["result"]
        self.assertEqual(r["structuredContent"]["code"], "UNKNOWN_PARAM")
        r = self.client.call({"test": "anova-oneway", "mode": "a-priori", "f": True,
                              "alpha": 0.05, "power": 0.8, "groups": 3})["result"]
        self.assertEqual(r["structuredContent"]["code"], "INVALID_VALUE")

    def test_bilinmeyen_arac_protokol_hatasi(self):
        for name in ("anova_oneway_a_priori", "anova_oneway_post_hoc", "t_test"):
            with self.subTest(tool=name):
                r = self.client.request("tools/call", {"name": name, "arguments": {}})
                self.assertEqual(r["error"]["code"], -32602)

    def test_arguments_nesne_degil(self):
        r = self.client.request("tools/call", {"name": "power_analysis", "arguments": [1]})
        self.assertEqual(r["error"]["code"], -32602)

    def test_bilinmeyen_yontem(self):
        self.assertEqual(self.client.request("resources/list")["error"]["code"], -32601)

    def test_bozuk_json(self):
        self.client.send_raw('{"jsonrpc": "2.0", "id": 99, "method": ')
        r = self.client.read()
        self.assertEqual(r["error"]["code"], -32700)
        self.assertIsNone(r["id"])
        self.assertEqual(self.client.request("ping")["result"], {})


class TestMcpCliEquivalence(unittest.TestCase):
    """CLI stdout satırı ≡ MCP content[0].text (bayt bayt), structuredContent eşit,
    çıkış kodu ≠ 0 ⇔ isError. 50 oracle + 5 sözleşme referansı + hata kodları."""

    @classmethod
    def setUpClass(cls):
        cls.client = McpProcess()
        handshake(cls.client)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def check(self, label, params):
        p = run_cli(params)
        lines = p.stdout.splitlines()
        self.assertEqual(len(lines), 1, f"{label}: {p.stdout!r} {p.stderr!r}")
        r = self.client.call(mcp_arguments(params))
        self.assertIn("result", r, r)
        res = r["result"]
        self.assertEqual(res["content"][0]["text"], lines[0], label)
        self.assertEqual(res["structuredContent"], json.loads(lines[0]), label)
        self.assertEqual(res["isError"], p.returncode != 0, label)
        return json.loads(lines[0])

    def test_oracle_vektorleri(self):
        self.assertEqual(len(VECTORS), 50)
        codes = {}
        for vid, row in VECTORS.items():
            with self.subTest(vector=vid):
                out = self.check(vid, oracle_params(row))
                codes[out.get("code", "OK")] = codes.get(out.get("code", "OK"), 0) + 1
        self.assertEqual(codes, {"OK": 35, "OUT_OF_RANGE": 8, "INVALID_VALUE": 4,
                                 "INCONSISTENT": 3})

    def test_sozlesme_referans_vektorleri(self):
        for name, (params, _) in REFERENCE_VECTORS.items():
            with self.subTest(vector=name):
                self.check(name, params)

    def test_hata_kodlari_ve_baska_aile(self):
        seen = set()
        for name, params in EXTRA_CASES.items():
            with self.subTest(case=name):
                seen.add(self.check(name, params).get("code", "OK"))
        self.assertTrue({"MISSING_PARAM", "UNKNOWN_PARAM", "INVALID_VALUE", "OUT_OF_RANGE",
                         "INCONSISTENT", "UNSUPPORTED"} <= seen)


class TestMcpFiles(unittest.TestCase):

    @unittest.skipIf(os.name == "nt", "Unix sarmalayıcısı")
    def test_anova_mcp_sarmalayicisi(self):
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        p = subprocess.run([os.path.join(ROOT, "anova-mcp")],
                           input='{"jsonrpc":"2.0","id":1,"method":"ping"}\n',
                           capture_output=True, text=True, env=env, cwd="/", timeout=30)
        self.assertEqual(json.loads(p.stdout), {"jsonrpc": "2.0", "id": 1, "result": {}})
        self.assertEqual(p.stdout.count("\n"), 1)

    def test_mcp_json(self):
        with open(os.path.join(ROOT, ".mcp.json"), encoding="utf-8") as fh:
            srv = json.load(fh)["mcpServers"]["anova-power"]
        self.assertEqual(srv["args"], ["/c", "anova-mcp.cmd"])
        self.assertTrue(os.path.exists(os.path.join(ROOT, srv["args"][-1])))

    def test_mcp_schema_md(self):
        with open(os.path.join(ROOT, "MCP_SCHEMA.md"), encoding="utf-8") as fh:
            doc = fh.read()
        self.assertIn("power_analysis", doc)
        for prop in mcp_server.TOOL["inputSchema"]["properties"]:
            self.assertIn(f"`{prop}`", doc)
        for key in ("ncp", "critical_f", "df1", "df2", "n_total", "actual_power", "power",
                    "n_per_group", "warning", "error", "code", "field"):
            self.assertIn(f"`{key}`", doc)
        for code in ("MISSING_PARAM", "UNKNOWN_PARAM", "INVALID_VALUE", "OUT_OF_RANGE",
                     "INCONSISTENT", "UNSUPPORTED", "NO_SOLUTION"):
            self.assertIn(code, doc)
        self.assertNotIn("anova_oneway_a_priori", doc)

    def test_mcp_mantik_kopyalamaz(self):
        with open(mcp_server.__file__, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported.update(a.name for a in node.names)
                imported.add(node.module or "")
            elif isinstance(node, ast.Import):
                imported.update(a.name for a in node.names)
        for forbidden in ("engine", "scipy", "numpy", "math", "errors"):
            self.assertNotIn(forbidden, imported)


if __name__ == "__main__":
    unittest.main()
