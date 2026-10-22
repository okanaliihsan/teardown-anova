"""CLI testleri — hocanın sözleşmesi (CONTRACT.md v1.0.0; özet CONTRACT_NOTES.md).

Uçtan uca testler subprocess ile; büyük matrisler hız için `cli.main` ile süreç içinde.
"""
from __future__ import annotations

import io
import json
import math
import os
import subprocess
import sys
import unittest

from oracle import ROOT, SRC, VECTORS

from anova_clone import cli

# Sözleşme §9 referans vektörleri (CONTRACT_NOTES.md tablosu), anova-oneway
REFERENCE_VECTORS = {
    "REF-a-priori": (
        {"test": "anova-oneway", "mode": "a-priori", "f": ".25", "alpha": ".05",
         "power": ".95", "groups": "5"},
        {"ncp": 19.0625000, "critical_f": 2.4017397, "df1": 4, "df2": 300,
         "n_total": 305, "actual_power": 0.9521313}),
    "REF-post-hoc": (
        {"test": "anova-oneway", "mode": "post-hoc", "f": ".25", "alpha": ".05",
         "n_total": "100", "groups": "5"},
        {"ncp": 6.2500000, "critical_f": 2.4674936, "df1": 4, "df2": 95,
         "power": 0.4663312}),
    # Bonus modlar: bu motor desteklemiyor -> UNSUPPORTED
    "REF-compromise": (
        {"test": "anova-oneway", "mode": "compromise", "f": ".25",
         "beta_alpha_ratio": "1", "n_total": "100", "groups": "5"}, None),
    "REF-criterion": (
        {"test": "anova-oneway", "mode": "criterion", "f": ".25", "power": ".95",
         "n_total": "100", "groups": "5"}, None),
    "REF-sensitivity": (
        {"test": "anova-oneway", "mode": "sensitivity", "alpha": ".05", "power": ".95",
         "n_total": "100", "groups": "5"}, None),
}
INTEGER_KEYS = {"df1", "df2", "n_total"}


def argv_from(params: dict) -> list[str]:
    """Sözleşme biçiminde argv: --test X --mode Y --alan değer ... ('=' biçimi,
    negatif değerler için güvenli)."""
    order = [k for k in ("test", "mode") if k in params] + \
        [k for k in params if k not in ("test", "mode")]
    return [f"--{k}={params[k]}" for k in order]


def run_proc(args, env_extra=None, cwd=ROOT):
    env = dict(os.environ)
    env["PYTHONPATH"] = SRC + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run([sys.executable, "-m", "anova_clone.cli", *args],
                          capture_output=True, text=True, env=env, cwd=cwd, timeout=60)


def run_main(args):
    out, err = io.StringIO(), io.StringIO()
    code = cli.main(list(args), stdout=out, stderr=err)
    return code, out.getvalue(), err.getvalue()


def ap(**kw):
    p = {"test": "anova-oneway", "mode": "a-priori", "f": "0.25", "alpha": "0.05",
         "power": "0.8", "groups": "3"}
    p.update(kw)
    return {k: v for k, v in p.items() if v is not None}


def ph(**kw):
    p = {"test": "anova-oneway", "mode": "post-hoc", "f": "0.25", "alpha": "0.05",
         "n_total": "100", "groups": "5"}
    p.update(kw)
    return {k: v for k, v in p.items() if v is not None}


def oracle_params(row) -> dict:
    p = {"test": "anova-oneway", "mode": row["mode"], "f": row["f"], "alpha": row["alpha"]}
    if row["mode"] == "a-priori":
        p["power"] = row["power_in"]
    else:
        p["n_total"] = row["n_in"]
    p["groups"] = row["k"]
    return p


def close(actual: float, expected: float, tol=1e-6) -> bool:
    d = abs(actual - expected)
    return d <= tol or d <= tol * abs(expected)


class ContractCase(unittest.TestCase):
    def call(self, params):
        code, out, err = run_main(argv_from(params))
        lines = out.splitlines()
        self.assertEqual(len(lines), 1, out)
        return code, json.loads(lines[0]), err

    def assert_error(self, params, code_name, field, exit_code=2):
        code, out, _ = self.call(params)
        self.assertEqual(code, exit_code, out)
        self.assertEqual(set(out), {"error", "code", "field"})
        self.assertEqual(out["code"], code_name, out)
        self.assertEqual(out["field"], field, out)
        self.assertTrue(out["error"])
        return out


# --------------------------------------------------------------------------
class TestContractSuccess(ContractCase):

    def test_referans_vektorleri_tolerans_1e6(self):
        for name, (params, expected) in REFERENCE_VECTORS.items():
            if expected is None:
                continue
            with self.subTest(vector=name):
                code, out, _ = self.call(params)
                self.assertEqual(code, 0)
                for key, exp in expected.items():
                    if key in INTEGER_KEYS:
                        self.assertIsInstance(out[key], int)
                        self.assertEqual(out[key], exp)
                    else:
                        self.assertTrue(close(out[key], exp), f"{key}: {out[key]} vs {exp}")

    def test_bonus_mod_referanslari_unsupported(self):
        for name, (params, expected) in REFERENCE_VECTORS.items():
            if expected is not None:
                continue
            with self.subTest(vector=name):
                self.assert_error(params, "UNSUPPORTED", "mode")

    def test_a_priori_anahtar_seti(self):
        code, out, err = self.call(ap())
        self.assertEqual(code, 0)
        self.assertEqual(list(out), ["ncp", "critical_f", "df1", "df2", "n_total",
                                     "actual_power", "n_per_group"])
        self.assertEqual(err, "")

    def test_post_hoc_anahtar_seti(self):
        code, out, err = self.call(ph())
        self.assertEqual(code, 0)
        self.assertEqual(list(out), ["ncp", "critical_f", "df1", "df2", "power",
                                     "n_total", "n_per_group"])
        for old in ("critical", "actual_power"):
            self.assertNotIn(old, out)
        self.assertEqual(err, "")

    def test_yuvarlama_yok_tam_double(self):
        from anova_clone import engine
        _, out, _ = self.call(ph(groups="3"))
        r = engine.post_hoc(0.25, 0.05, 100, 3)
        self.assertEqual(out["power"], r.power)
        self.assertEqual(out["critical_f"], r.critical_f)
        self.assertEqual(out["ncp"], 6.25)
        self.assertGreater(len(repr(out["power"]).split(".")[1]), 7)

    def test_uyari_json_ve_stderr(self):
        code, out, err = self.call(ph(groups="3"))
        self.assertEqual(code, 0)
        self.assertEqual(out["warning"], err.strip())
        self.assertIn("(100)", err)
        self.assertIsNone(out["n_per_group"])

    def test_tam_sayi_degerli_ondalik_kabul(self):
        _, a, _ = self.call(ph(n_total="100.0", groups="5.0"))
        _, b, _ = self.call(ph())
        self.assertEqual(a, b)
        self.assertIsInstance(a["n_total"], int)

    def test_guc_alphaya_esit_kabul_edilir_gpower(self):
        code, out, _ = self.call(ap(power="0.05"))
        self.assertEqual(code, 0)
        self.assertEqual(out["n_total"], 6)

    def test_bosluklu_bicim_ve_negatif_deger(self):
        args = ["--test", "anova-oneway", "--mode", "post-hoc", "--f", "-1",
                "--alpha", "0.05", "--n_total", "100", "--groups", "3"]
        code, out, _ = run_main(args)
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out)["code"], "OUT_OF_RANGE")


class TestContractErrors(ContractCase):

    def test_missing_param(self):
        self.assert_error(ap(power=None), "MISSING_PARAM", "power")
        self.assert_error(ph(n_total=None), "MISSING_PARAM", "n_total")
        self.assert_error(ap(test=None), "MISSING_PARAM", "test")
        self.assert_error(ap(mode=None), "MISSING_PARAM", "mode")

    def test_unknown_param_taninmayan_ve_ilgisiz(self):
        self.assert_error(ap(tails="2"), "UNKNOWN_PARAM", "tails")
        self.assert_error(ap(power="0.8", n_total="100"), "UNKNOWN_PARAM", "n_total")
        self.assert_error(ph(power="0.8"), "UNKNOWN_PARAM", "power")
        # Tur 2 takma adları artık tanınmıyor
        for alias in ("n", "k", "n-total", "effect-size", "es", "target-power"):
            with self.subTest(alias=alias):
                self.assert_error(ph(**{alias: "3"}), "UNKNOWN_PARAM", alias)

    def test_invalid_value(self):
        self.assert_error(ap(f="abc"), "INVALID_VALUE", "f")
        self.assert_error(ap(alpha="0,05"), "INVALID_VALUE", "alpha")
        self.assert_error(ap(f="nan"), "INVALID_VALUE", "f")
        self.assert_error(ap(f="inf"), "INVALID_VALUE", "f")
        self.assert_error(ap(groups="2.5"), "INVALID_VALUE", "groups")
        self.assert_error(ph(n_total="159.6", groups="3"), "INVALID_VALUE", "n_total")

    def test_out_of_range(self):
        cases = [(ap(alpha="0"), "alpha"), (ap(alpha="1"), "alpha"),
                 (ap(power="1"), "power"), (ap(f="0"), "f"), (ap(f="-1"), "f"),
                 (ph(f="0"), "f"), (ap(groups="1"), "groups"), (ph(n_total="1"), "n_total"),
                 (ap(f="60"), "f"), (ap(alpha="1e-8", power="0.5"), "alpha")]
        for params, field in cases:
            with self.subTest(params=params):
                self.assert_error(params, "OUT_OF_RANGE", field)

    def test_inconsistent(self):
        out = self.assert_error(ap(power="0.04"), "INCONSISTENT", "power")
        self.assertEqual(out["error"], "Power must be greater than or equal to alpha.")
        out = self.assert_error(ph(n_total="3", groups="3"), "INCONSISTENT", "n_total")
        self.assertEqual(out["error"],
                         "Sample size must be greater than the number of groups (3).")

    def test_unsupported(self):
        for t in ("t2-indep", "t-paired", "chi2-contingency", "multireg-r2", "foo",
                  "ANOVA-ONEWAY", "anova"):
            with self.subTest(test=t):
                self.assert_error(ap(test=t), "UNSUPPORTED", "test")
        for m in ("compromise", "criterion", "sensitivity", "posthoc"):
            with self.subTest(mode=m):
                self.assert_error(ap(mode=m), "UNSUPPORTED", "mode")

    def test_no_solution_cikis_1(self):
        from unittest import mock
        from anova_clone.errors import SolverError
        with mock.patch.object(cli.engine, "a_priori", side_effect=SolverError("x")):
            out = self.assert_error(ap(), "NO_SOLUTION", None, exit_code=1)
        self.assertEqual(out["field"], None)

    def test_dogrulama_sirasi(self):
        # test/mode > alan kümesi > değer > aralık > motor
        self.assert_error(ap(test="t2-indep", f="abc", tails="1"), "UNSUPPORTED", "test")
        self.assert_error(ap(f="abc", tails="1"), "UNKNOWN_PARAM", "tails")
        self.assert_error(ap(f="abc", power=None), "MISSING_PARAM", "power")
        self.assert_error(ap(alpha="0", f="abc"), "INVALID_VALUE", "f")


class TestOracleVectorsViaCli(ContractCase):
    """gpower_vectors.csv vektörleri CLI üzerinden (sözleşme kabuğu dahil)."""

    # Sözleşme <-> G*Power ayrılığı: bu 5 vektörde G*Power sonuç verir ama sözleşme
    # reddeder. G*Power davranışı motor düzeyinde test_spec.py'de doğrulanır.
    CONTRACT_DIVERGENT = {"X07": ("INVALID_VALUE", "groups"),
                          "X09": ("INVALID_VALUE", "groups"),
                          "P13": ("INVALID_VALUE", "n_total"),
                          "P14": ("INVALID_VALUE", "n_total"),
                          "P07": ("OUT_OF_RANGE", "f")}
    EXPECTED_ERRORS = {"A22": ("INCONSISTENT", "power"), "X01": ("OUT_OF_RANGE", "f"),
                       "X02": ("OUT_OF_RANGE", "f"), "X03": ("OUT_OF_RANGE", "alpha"),
                       "X04": ("OUT_OF_RANGE", "alpha"), "X05": ("OUT_OF_RANGE", "power"),
                       "X06": ("OUT_OF_RANGE", "groups"), "X08": ("OUT_OF_RANGE", "groups"),
                       "P04": ("INCONSISTENT", "n_total"), "P08": ("INCONSISTENT", "n_total")}
    COLS = {"lambda": "ncp", "critical_F": "critical_f", "df1": "df1", "df2": "df2"}

    def test_tum_oracle_vektorleri(self):
        self.assertEqual(len(VECTORS), 50)
        for vid, row in VECTORS.items():
            with self.subTest(vector=vid):
                params = oracle_params(row)
                if vid in self.CONTRACT_DIVERGENT:
                    self.assert_error(params, *self.CONTRACT_DIVERGENT[vid])
                    continue
                if vid in self.EXPECTED_ERRORS:
                    self.assert_error(params, *self.EXPECTED_ERRORS[vid])
                    continue
                code, out, _ = self.call(params)
                self.assertEqual(code, 0, out)
                power_key = "actual_power" if row["mode"] == "a-priori" else "power"
                cols = dict(self.COLS, n_total="n_total", actual_power=power_key)
                for col, key in cols.items():
                    text = row[col]
                    if key in INTEGER_KEYS:
                        self.assertEqual(out[key], int(text))
                    else:
                        d = len(text.split(".")[1]) if "." in text else 0
                        self.assertTrue(math.isclose(round(out[key], d), float(text),
                                                     abs_tol=10 ** -d * 1e-6),
                                        f"{vid}.{col}: {out[key]} vs {text}")


class TestCliProcess(unittest.TestCase):
    """Gerçek alt süreçle: tek satır stdout, çıkış kodları, --version, sarmalayıcı."""

    def test_version(self):
        p = run_proc(["--version"])
        self.assertEqual(p.returncode, 0)
        self.assertEqual(len(p.stdout.splitlines()), 1)
        v = json.loads(p.stdout)
        self.assertEqual(v["contract_version"], "1.0.0")
        self.assertEqual(v["name"], "teardown-anova")
        self.assertRegex(v["engine"], r"^Python \d+\.\d+\.\d+ \+ scipy \d+\.\d+\.\d+")

    def test_basari_tek_satir_cikis_0(self):
        p = run_proc(argv_from(REFERENCE_VECTORS["REF-a-priori"][0]))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(len(p.stdout.splitlines()), 1)
        self.assertEqual(json.loads(p.stdout)["n_total"], 305)
        self.assertEqual(p.stderr, "")

    def test_uyari_stderr_e_gider_stdout_tek_satir(self):
        p = run_proc(argv_from(ph(groups="3")))
        self.assertEqual(p.returncode, 0)
        self.assertEqual(len(p.stdout.splitlines()), 1)
        self.assertIn("not a multiple", p.stderr)

    def test_hatalar_tek_satir_json_sifirdan_farkli(self):
        for args in (argv_from(ap(f="abc")), ["--help"], ["-x"], [], ["--test"],
                     ["--test", "anova-oneway", "--mode", "a-priori", "positional"]):
            with self.subTest(args=args):
                p = run_proc(args)
                self.assertEqual(p.returncode, 2, p.stdout)
                lines = p.stdout.splitlines()
                self.assertEqual(len(lines), 1, p.stdout)
                self.assertEqual(set(json.loads(lines[0])), {"error", "code", "field"})

    @unittest.skipIf(os.name == "nt", "Unix sarmalayıcısı")
    def test_gpower_clone_sarmalayicisi(self):
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        p = subprocess.run([os.path.join(ROOT, "gpower-clone"),
                            *argv_from(REFERENCE_VECTORS["REF-post-hoc"][0])],
                           capture_output=True, text=True, env=env, cwd="/", timeout=60)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(json.loads(p.stdout)["df2"], 95)


if __name__ == "__main__":
    unittest.main()
