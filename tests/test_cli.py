"""CLI uçtan uca testleri (subprocess)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

from oracle import ROOT, SRC, vector

from anova_clone import cli

N = cli.NAMES


def run_cli(*args, via="module"):
    env = dict(os.environ)
    env["PYTHONPATH"] = SRC + os.pathsep + env.get("PYTHONPATH", "")
    if via == "module":
        cmd = [sys.executable, "-m", "anova_clone.cli", *args]
    else:
        cmd = [os.path.join(ROOT, "gpower-clone"), *args]
    return subprocess.run(cmd, capture_output=True, text=True, env=env,
                          cwd=ROOT, timeout=60)


def a_priori_args(f="0.25", alpha="0.05", power="0.95", groups="10"):
    return [N["opt_test"], N["test_anova_oneway"], N["opt_mode"], N["mode_a_priori"],
            N["opt_f"], f, N["opt_alpha"], alpha, N["opt_power"], power,
            N["opt_groups"], groups]


def post_hoc_args(f="0.25", alpha="0.05", n="390", groups="10"):
    return [N["opt_test"], N["test_anova_oneway"], N["opt_mode"], N["mode_post_hoc"],
            N["opt_f"], f, N["opt_alpha"], alpha, N["opt_n"], n,
            N["opt_groups"], groups]


class TestCli(unittest.TestCase):

    def assert_single_line_json(self, proc):
        lines = proc.stdout.splitlines()
        self.assertEqual(len(lines), 1, f"tek satır bekleniyordu: {proc.stdout!r}")
        return json.loads(lines[0])

    def test_a_priori_basari_tek_satir_json_cikis_0(self):
        p = run_cli(*a_priori_args())
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        out = self.assert_single_line_json(p)
        a01 = vector("A01")
        self.assertEqual(out[N["out_n_total"]], int(a01["n_total"]))
        self.assertEqual(out[N["out_n_per_group"]], 39)
        self.assertEqual(out[N["out_df1"]], int(a01["df1"]))
        self.assertEqual(out[N["out_df2"]], int(a01["df2"]))
        self.assertAlmostEqual(out[N["out_power_a_priori"]], float(a01["actual_power"]), places=7)
        self.assertAlmostEqual(out[N["out_critical"]], float(a01["critical_F"]), places=7)
        self.assertAlmostEqual(out[N["out_ncp"]], float(a01["lambda"]), places=7)
        self.assertNotIn(N["out_warning"], out)

    def test_post_hoc_basari_tek_satir_json(self):
        p = run_cli(*post_hoc_args())
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        out = self.assert_single_line_json(p)
        # Tur 2 sözleşmesi: güç her iki modda iki anahtarla yazılır
        self.assertIn(N["out_power_post_hoc"], out)
        self.assertIn(N["out_power_a_priori"], out)
        self.assertEqual(out[N["out_power_post_hoc"]], out[N["out_power_a_priori"]])

    def test_post_hoc_uyarili_basari(self):
        p = run_cli(*post_hoc_args(n="100", groups="3"))
        self.assertEqual(p.returncode, 0)
        out = self.assert_single_line_json(p)
        self.assertIn(N["out_warning"], out)
        self.assertIsNone(out[N["out_n_per_group"]])
        self.assertEqual(out[N["out_df2"]], 97)

    def test_ondalik_basamak_sabiti(self):
        p = run_cli(*post_hoc_args(n="100", groups="3"))
        out = self.assert_single_line_json(p)
        for key in (N["out_power_post_hoc"], N["out_critical"]):
            text = repr(out[key])
            decimals = len(text.split(".")[1]) if "." in text else 0
            self.assertLessEqual(decimals, cli.JSON_DECIMALS)

    def test_gecersiz_girdiler_hata_json_ve_sifirdan_farkli_cikis(self):
        cases = {
            "power<alpha": a_priori_args(power="0.04", groups="3"),
            "f=0 a priori": a_priori_args(f="0"),
            "f negatif": a_priori_args(f="-0.25"),
            "alpha=0": a_priori_args(alpha="0"),
            "alpha=1": a_priori_args(alpha="1"),
            "power=1": a_priori_args(power="1"),
            "k=1": a_priori_args(groups="1"),
            "k=2.5": a_priori_args(groups="2.5"),
            "N=k": post_hoc_args(n="3", groups="3"),
            "sayi degil": a_priori_args(f="abc"),
            "eksik --power": [a for a in a_priori_args()[:8]] + [N["opt_groups"], "3"],
            "bilinmeyen test": [N["opt_test"], "t-test"] + a_priori_args()[2:],
        }
        for name, args in cases.items():
            with self.subTest(case=name):
                p = run_cli(*args)
                self.assertNotEqual(p.returncode, 0)
                out = self.assert_single_line_json(p)
                self.assertEqual(list(out), [N["out_error"]])
                self.assertTrue(out[N["out_error"]])

    def test_hata_mesaji_sorunlu_alani_belirtir_R34(self):
        p = run_cli(*a_priori_args(alpha="0"))
        self.assertIn(N["opt_alpha"], json.loads(p.stdout)[N["out_error"]])
        p = run_cli(*a_priori_args(groups="1"))
        self.assertIn(N["opt_groups"], json.loads(p.stdout)[N["out_error"]])

    @unittest.skipIf(os.name == "nt", "Unix sarmalayıcısı")
    def test_gpower_clone_sarmalayicisi_kurulumsuz_calisir(self):
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        p = subprocess.run([os.path.join(ROOT, "gpower-clone"), *a_priori_args()],
                           capture_output=True, text=True, env=env, cwd="/", timeout=60)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.assert_single_line_json(p)[N["out_n_total"]], 390)


def run_main(args):
    """main()'i süreç içinde çalıştırır (takma ad matrisi için hızlı yol)."""
    import io
    buf = io.StringIO()
    code = cli.main(list(args), stdout=buf)
    return code, buf.getvalue()




class TestCliAliases(unittest.TestCase):
    """Tur 2: takma adlar, yok sayılan ek seçenekler, iki güç anahtarı."""

    @classmethod
    def setUpClass(cls):
        code, text = run_main(a_priori_args())
        assert code == 0, text
        cls.a01 = json.loads(text)
        code, text = run_main(post_hoc_args(n="100", groups="3"))
        assert code == 0, text
        cls.p02 = json.loads(text)

    def _replace(self, args, canonical, alias):
        out = list(args)
        out[out.index(canonical)] = alias
        return out

    def assert_same(self, args, expected):
        code, text = run_main(args)
        self.assertEqual(code, 0, text)
        self.assertEqual(len(text.splitlines()), 1)
        self.assertEqual(json.loads(text), expected)

    def test_alias_sozlugu_beklenen_adlari_icerir(self):
        expected = {
            "opt_groups": {"--groups", "--k", "--k-groups", "--num-groups", "--number-of-groups"},
            "opt_n": {"--n", "--n-total", "--n_total", "--total-n", "--sample-size", "--N"},
            "opt_f": {"--f", "--effect-size", "--es"},
            "opt_power": {"--power", "--target-power"},
            "mode_a_priori": {"a-priori", "apriori", "a_priori"},
            "mode_post_hoc": {"post-hoc", "posthoc", "post_hoc"},
            "test_anova_oneway": {"anova-oneway", "anova_oneway", "anova"},
        }
        for key, names in expected.items():
            with self.subTest(key=key):
                self.assertEqual(set(cli.ALIASES[key]), names)
                self.assertIn(N[key], cli.ALIASES[key])  # kanonik ad da takma ad listesinde

    def test_grup_sayisi_takma_adlari(self):
        for alias in cli.ALIASES["opt_groups"]:
            with self.subTest(alias=alias):
                self.assert_same(self._replace(a_priori_args(), N["opt_groups"], alias), self.a01)

    def test_toplam_n_takma_adlari(self):
        for alias in cli.ALIASES["opt_n"]:
            with self.subTest(alias=alias):
                self.assert_same(self._replace(post_hoc_args(n="100", groups="3"),
                                               N["opt_n"], alias), self.p02)

    def test_etki_buyuklugu_takma_adlari(self):
        for alias in cli.ALIASES["opt_f"]:
            with self.subTest(alias=alias):
                self.assert_same(self._replace(a_priori_args(), N["opt_f"], alias), self.a01)

    def test_guc_takma_adlari(self):
        for alias in cli.ALIASES["opt_power"]:
            with self.subTest(alias=alias):
                self.assert_same(self._replace(a_priori_args(), N["opt_power"], alias), self.a01)

    def test_mod_degerleri_buyuk_kucuk_harf_duyarsiz(self):
        for alias in cli.ALIASES["mode_a_priori"]:
            for variant in (alias, alias.upper(), alias.title()):
                with self.subTest(mode=variant):
                    self.assert_same(self._replace(a_priori_args(), N["mode_a_priori"], variant),
                                     self.a01)
        for alias in cli.ALIASES["mode_post_hoc"]:
            for variant in (alias, alias.upper(), alias.title()):
                with self.subTest(mode=variant):
                    self.assert_same(self._replace(post_hoc_args(n="100", groups="3"),
                                                   N["mode_post_hoc"], variant), self.p02)

    def test_test_degerleri_buyuk_kucuk_harf_duyarsiz(self):
        for alias in cli.ALIASES["test_anova_oneway"]:
            for variant in (alias, alias.upper(), alias.title()):
                with self.subTest(test=variant):
                    self.assert_same(self._replace(a_priori_args(), N["test_anova_oneway"], variant),
                                     self.a01)

    def test_gecersiz_mod_ve_test_degerleri_hala_hata(self):
        for args in (self._replace(a_priori_args(), N["mode_a_priori"], "sensitivity"),
                     self._replace(a_priori_args(), N["test_anova_oneway"], "t-test")):
            with self.subTest(args=args):
                code, text = run_main(args)
                self.assertNotEqual(code, 0)
                self.assertEqual(list(json.loads(text)), [N["out_error"]])

    def test_bilinmeyen_ek_secenekler_yok_sayilir(self):
        extras = [["--tails", "2"], ["--ratio", "1"], ["--tails=1", "--ratio=0.5"],
                  ["--tails", "2", "--ratio", "1", "--allocation", "equal"], ["--verbose"]]
        for extra in extras:
            with self.subTest(extra=extra):
                self.assert_same(a_priori_args() + extra, self.a01)
                self.assert_same(extra + a_priori_args(), self.a01)
                code, text = run_main(post_hoc_args(n="100", groups="3") + extra)
                out = json.loads(text)
                self.assertEqual(out, self.p02)
                for e in extra:
                    self.assertNotIn(e.lstrip("-").split("=")[0], out)

    def test_iki_guc_anahtari_ve_alan_sirasi(self):
        order_ok = ["n_total", "n_per_group", "actual_power", "power",
                    "critical", "df1", "df2", "ncp"]
        self.assertEqual(list(self.a01), order_ok)
        self.assertEqual(list(self.p02), order_ok + ["warning"])
        for out in (self.a01, self.p02):
            self.assertEqual(out["actual_power"], out["power"])
        self.assertAlmostEqual(self.a01["power"], float(vector("A01")["actual_power"]), places=7)

    def test_alias_ve_ek_secenek_uctan_uca_subprocess(self):
        args = [ "--test", "ANOVA", "--mode", "PostHoc", "--effect-size", "0.25",
                 "--alpha", "0.05", "--sample-size", "390", "--k", "10",
                 "--tails", "2", "--ratio", "1"]
        p = run_cli(*args)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        out = json.loads(p.stdout)
        self.assertEqual(len(p.stdout.splitlines()), 1)
        self.assertEqual(out["n_total"], 390)
        self.assertEqual(out["actual_power"], out["power"])
        self.assertAlmostEqual(out["power"], float(vector("A01")["actual_power"]), places=7)


if __name__ == "__main__":
    unittest.main()
