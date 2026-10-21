"""MCP sunucusu testleri: gerçek stdio JSON-RPC alt süreci + CLI eşdeğerliği."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

from oracle import ROOT, SRC, VECTORS

from anova_clone import cli, mcp_server

N = cli.NAMES


def _env():
    env = dict(os.environ)
    env["PYTHONPATH"] = SRC + os.pathsep + env.get("PYTHONPATH", "")
    return env


class McpProcess:
    """Tek bir MCP sunucu sürecini açık tutan basit istemci."""

    def __init__(self, cmd=None):
        cmd = cmd or [sys.executable, "-m", "anova_clone.mcp_server"]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, encoding="utf-8",
                                     env=_env(), cwd=ROOT, bufsize=1)
        self._id = 0

    def send_raw(self, line: str):
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

    def notify(self, method, params=None):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self.send_raw(json.dumps(msg))

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        finally:
            for s in (self.proc.stdout, self.proc.stderr):
                s.close()


def handshake(client: McpProcess, version="2025-06-18"):
    r = client.request("initialize", {
        "protocolVersion": version, "capabilities": {},
        "clientInfo": {"name": "unittest", "version": "0"}})
    client.notify("notifications/initialized")
    return r


# --------------------------------------------------------------------------
# Vektör -> (CLI argümanları, MCP aracı ve argümanları)
# --------------------------------------------------------------------------
def cli_args_for(row):
    args = [N["opt_test"], N["test_anova_oneway"], N["opt_mode"], row["mode"],
            N["opt_f"], row["f"], N["opt_alpha"], row["alpha"],
            N["opt_groups"], row["k"]]
    if row["mode"] == "a-priori":
        args += [N["opt_power"], row["power_in"]]
    else:
        args += [N["opt_n"], row["n_in"]]
    # "--f -0.25" gibi negatif değerler argparse'ta seçenek sanılmasın diye "=" biçimi
    out = []
    it = iter(args)
    for opt in it:
        out.append(f"{opt}={next(it)}")
    return out


def mcp_call_for(row):
    args = {"f": float(row["f"]), "alpha": float(row["alpha"]), "groups": float(row["k"])}
    if row["mode"] == "a-priori":
        args["power"] = float(row["power_in"])
        return "anova_oneway_a_priori", args
    args["n_total"] = float(row["n_in"])
    return "anova_oneway_post_hoc", args


def run_cli(args):
    p = subprocess.run([sys.executable, "-m", "anova_clone.cli", *args],
                       capture_output=True, text=True, env=_env(), cwd=ROOT, timeout=60)
    return p


class TestMcpProtocol(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = McpProcess()
        cls.init = handshake(cls.client)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_initialize_el_sikisma(self):
        res = self.init["result"]
        self.assertEqual(self.init["jsonrpc"], "2.0")
        self.assertEqual(res["protocolVersion"], "2025-06-18")
        self.assertEqual(res["capabilities"], {"tools": {}})
        self.assertEqual(res["serverInfo"], {"name": "anova-power-clone", "version": "1.1.0"})

    def test_initialize_protocol_version_yankilanir_ve_varsayilan(self):
        self.assertEqual(self.client.request(
            "initialize", {"protocolVersion": "2024-11-05"})["result"]["protocolVersion"],
            "2024-11-05")
        self.assertEqual(self.client.request("initialize", {})["result"]["protocolVersion"],
                         "2025-06-18")

    def test_ping(self):
        self.assertEqual(self.client.request("ping")["result"], {})

    def test_tools_list(self):
        tools = self.client.request("tools/list")["result"]["tools"]
        names = [t["name"] for t in tools]
        self.assertEqual(names, ["anova_oneway_a_priori", "anova_oneway_post_hoc"])
        a, p = tools
        self.assertEqual(a["inputSchema"]["required"], ["f", "alpha", "power", "groups"])
        self.assertEqual(p["inputSchema"]["required"], ["f", "alpha", "n_total", "groups"])
        for t in tools:
            self.assertTrue(t["description"])
            self.assertNotIn("_mode", t)
            for name, prop in t["inputSchema"]["properties"].items():
                with self.subTest(tool=t["name"], prop=name):
                    self.assertEqual(prop["type"], "number")
                    self.assertTrue(prop["description"])

    def test_tools_call_basari(self):
        r = self.client.request("tools/call", {"name": "anova_oneway_a_priori", "arguments": {
            "f": 0.25, "alpha": 0.05, "power": 0.95, "groups": 10}})["result"]
        self.assertFalse(r["isError"])
        self.assertEqual(r["content"][0]["type"], "text")
        self.assertEqual(json.loads(r["content"][0]["text"]), r["structuredContent"])
        self.assertEqual(r["structuredContent"]["n_total"], 390)

    def test_tools_call_gecersiz_girdi_isError(self):
        r = self.client.request("tools/call", {"name": "anova_oneway_post_hoc", "arguments": {
            "f": 0.25, "alpha": 0.05, "n_total": 3, "groups": 3}})["result"]
        self.assertTrue(r["isError"])
        self.assertEqual(json.loads(r["content"][0]["text"]), {
            "error": "--n: Sample size must be greater than the number of groups (3)."})

    def test_bilinmeyen_arac(self):
        r = self.client.request("tools/call", {"name": "t_test", "arguments": {}})
        self.assertEqual(r["error"]["code"], -32602)
        self.assertIn("unknown tool", r["error"]["message"])

    def test_eksik_arguman(self):
        r = self.client.request("tools/call", {"name": "anova_oneway_a_priori", "arguments": {
            "f": 0.25, "alpha": 0.05, "groups": 3}})
        self.assertEqual(r["error"]["code"], -32602)
        self.assertIn("power", r["error"]["message"])

    def test_sayi_olmayan_arguman(self):
        r = self.client.request("tools/call", {"name": "anova_oneway_a_priori", "arguments": {
            "f": "abc", "alpha": 0.05, "power": 0.8, "groups": 3}})
        self.assertEqual(r["error"]["code"], -32602)

    def test_bilinmeyen_yontem(self):
        r = self.client.request("resources/list")
        self.assertEqual(r["error"]["code"], -32601)

    def test_bozuk_json(self):
        self.client.send_raw('{"jsonrpc": "2.0", "id": 99, "method": ')
        r = self.client.read()
        self.assertEqual(r["error"]["code"], -32700)
        self.assertIsNone(r["id"])
        # sunucu hâlâ çalışıyor
        self.assertEqual(self.client.request("ping")["result"], {})

    def test_bildirimlere_yanit_verilmez(self):
        self.client.notify("notifications/initialized")
        self.client.notify("notifications/cancelled", {"requestId": 1})
        # bir sonraki satır bildirime değil ping'e ait olmalı
        self.assertEqual(self.client.request("ping")["result"], {})


class TestMcpCliEquivalence(unittest.TestCase):
    """50 oracle vektörünün her biri için CLI (alt süreç) ve MCP tools/call
    çıktıları birebir eşit olmalı (hata vakaları dahil)."""

    @classmethod
    def setUpClass(cls):
        cls.client = McpProcess()
        handshake(cls.client)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_tum_vektorlerde_cli_ve_mcp_ayni(self):
        self.assertEqual(len(VECTORS), 50)
        n_ok = n_err = 0
        for vid, row in VECTORS.items():
            with self.subTest(vector=vid):
                p = run_cli(cli_args_for(row))
                lines = p.stdout.splitlines()
                self.assertEqual(len(lines), 1, p.stdout + p.stderr)
                cli_out = json.loads(lines[0])

                tool, args = mcp_call_for(row)
                r = self.client.request("tools/call", {"name": tool, "arguments": args})
                self.assertIn("result", r, r)
                res = r["result"]
                mcp_text = res["content"][0]["text"]

                self.assertEqual(json.loads(mcp_text), cli_out)
                self.assertEqual(res["structuredContent"], cli_out)
                self.assertEqual(mcp_text, lines[0])           # bayt düzeyinde aynı satır
                self.assertEqual(res["isError"], p.returncode != 0)
                if res["isError"]:
                    n_err += 1
                else:
                    n_ok += 1
        # 40 sayısal sonuç + 10 geçersiz girdi vektörü
        self.assertEqual((n_ok, n_err), (40, 10))


class TestMcpWrapper(unittest.TestCase):

    @unittest.skipIf(os.name == "nt", "Unix sarmalayıcısı")
    def test_anova_mcp_sarmalayicisi_kurulumsuz_calisir(self):
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        p = subprocess.run([os.path.join(ROOT, "anova-mcp")],
                           input='{"jsonrpc":"2.0","id":1,"method":"ping"}\n',
                           capture_output=True, text=True, env=env, cwd="/", timeout=30)
        self.assertEqual(json.loads(p.stdout), {"jsonrpc": "2.0", "id": 1, "result": {}})
        self.assertEqual(p.stdout.count("\n"), 1)   # stdout'ta protokol dışı çıktı yok

    def test_mcp_json_gecerli_ve_goreli_yol(self):
        with open(os.path.join(ROOT, ".mcp.json"), encoding="utf-8") as fh:
            cfg = json.load(fh)
        srv = cfg["mcpServers"]["anova-power"]
        self.assertEqual(srv["args"], ["/c", "anova-mcp.cmd"])   # "/c" cmd bayrağıdır
        script = srv["args"][-1]
        self.assertEqual(os.path.basename(script), script)      # göreli, dizinsiz
        self.assertTrue(os.path.exists(os.path.join(ROOT, script)))

    def test_mcp_schema_md_araclari_belgeler(self):
        with open(os.path.join(ROOT, "MCP_SCHEMA.md"), encoding="utf-8") as fh:
            doc = fh.read()
        for t in mcp_server.TOOLS:
            self.assertIn(t["name"], doc)
            for prop in t["inputSchema"]["properties"]:
                self.assertIn(f"`{prop}`", doc)
        for out in mcp_server.OUTPUT_SCHEMA["properties"]:
            self.assertIn(f"`{out}`", doc)


class TestMcpNoLogicDuplication(unittest.TestCase):
    def test_mcp_motoru_dogrudan_cagirmaz_ve_formul_icermez(self):
        with open(mcp_server.__file__, encoding="utf-8") as fh:
            src = fh.read()
        import ast
        tree = ast.parse(src)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported.update(a.name for a in node.names)
                imported.add(node.module or "")
            elif isinstance(node, ast.Import):
                imported.update(a.name for a in node.names)
        # Yalnızca cli adaptörü üzerinden; motor, scipy, numpy, math içe aktarılmaz
        for forbidden in ("engine", "scipy", "numpy", "math", "errors"):
            self.assertNotIn(forbidden, imported)
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        self.assertNotIn("round", names)


if __name__ == "__main__":
    unittest.main()
