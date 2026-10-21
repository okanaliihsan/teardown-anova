"""SPEC.md bölüm 9 Gherkin senaryolarının unittest karşılıkları.

Her test adı senaryoyu ve dayandığı kural numaralarını içerir. Sayısal beklenen
değerler yalnızca oracle/gpower_vectors.csv'den okunur. Çıkış sütunları boş
olan bir vektörün sayısal karşılaştırması `skipTest` ile atlanır; aynı
senaryonun oracle'a ihtiyaç duymayan, doğrudan SPEC kuralından gelen
iddiaları (ör. df2 = N - k, uyarı üretilmesi, hata sınıfı) ayrı testlerde
koşturulur.
"""
from __future__ import annotations

import math
import unittest

from oracle import (EXACT_COLUMNS, NUMERIC_OUTPUTS, has_oracle_output, inputs,
                    matches_display, vector)

from anova_clone import engine
from anova_clone.errors import (AlphaRangeError, EffectSizeRangeError,
                                GroupCountError, InvalidInputError,
                                PowerBelowAlphaError, PowerRangeError,
                                SampleSizeError)

SKIP_MSG = "oracle değeri henüz toplanmadı"

# CSV sütunu -> Result alanı
FIELD = {
    "lambda": "ncp",
    "critical_F": "critical_f",
    "df1": "df1",
    "df2": "df2",
    "n_total": "n_total",
    "actual_power": "power",
}


def run_vector(vid: str):
    row = inputs(vector(vid))
    if row["mode"] == "a-priori":
        return engine.a_priori(f=row["f"], alpha=row["alpha"],
                               power=row["power"], k=row["k"])
    return engine.post_hoc(f=row["f"], alpha=row["alpha"],
                           n_total=row["n"], k=row["k"])


class OracleMixin:
    def require_oracle(self, vid: str) -> dict:
        row = vector(vid)
        if not has_oracle_output(row):
            self.skipTest(SKIP_MSG)
        return row

    def assert_matches(self, vid: str, result, columns=NUMERIC_OUTPUTS):
        row = self.require_oracle(vid)
        for col in columns:
            text = row[col].strip()
            if not text:
                continue
            actual = getattr(result, FIELD[col])
            with self.subTest(vector=vid, column=col):
                if col in EXACT_COLUMNS:
                    self.assertEqual(actual, int(text),
                                     f"{vid}.{col}: {actual} != {text}")
                else:
                    self.assertTrue(matches_display(actual, text),
                                    f"{vid}.{col}: {actual!r} ekranda {text} olmalı")


# --------------------------------------------------------------------------
# A priori
# --------------------------------------------------------------------------
class TestAPriori(OracleMixin, unittest.TestCase):

    def test_kilavuz_ornegi_a_priori_sonucu_R14_R18_R20_R25(self):
        row = self.require_oracle("A01")
        r = run_vector("A01")
        self.assert_matches("A01", r)
        k = int(float(row["k"]))
        self.assertEqual(r.n_total % k, 0)
        self.assertGreaterEqual(r.power, float(row["power_in"]))

    def test_en_kucuk_gecerli_grup_sayisi_k2_R04_R14_R15_R23(self):
        self.require_oracle("A11")
        r = run_vector("A11")
        self.assert_matches("A11", r)
        self.assertEqual(r.df1, 1)
        self.assertEqual(r.n_total % 2, 0)

    def test_tipik_uc_grup_durumu_k3_R23(self):
        self.require_oracle("A02")
        r = run_vector("A02")
        self.assert_matches("A02", r)
        self.assertEqual(r.n_total % 3, 0)

    def test_N_k_katina_yukari_yuvarlanir_en_kucuk_tamsayiya_degil_R23(self):
        for vid in ("A02", "A03", "A04", "A08", "A09"):
            with self.subTest(vector=vid):
                row = self.require_oracle(vid)
                k = int(float(row["k"]))
                r = run_vector(vid)
                self.assertEqual(r.n_total, int(row["n_total"]))
                self.assertEqual(r.n_total % k, 0)
                # Sürekli çözümün k katına yukarı yuvarlanmış hali
                n_cont = engine.solve_continuous_n(
                    float(row["f"]), float(row["alpha"]),
                    float(row["power_in"]), k)
                self.assertEqual(r.n_total, math.ceil(n_cont / k) * k)
                # Ayırt edicilik: k katı olmayan en küçük tam sayı daha küçüktür
                self.assertLessEqual(math.ceil(n_cont), r.n_total)

    def test_gercek_guc_yuvarlanmis_N_ile_yeniden_hesaplanir_R25(self):
        row = self.require_oracle("A03")
        r = run_vector("A03")
        self.assert_matches("A03", r, columns=("actual_power",))
        self.assertGreaterEqual(r.power, float(row["power_in"]))
        self.assertEqual(r.power, engine.post_hoc(
            float(row["f"]), float(row["alpha"]), r.n_total, int(row["k"])).power)

    def test_cok_kucuk_etki_buyuklugu_buyuk_orneklem_uretir_R22_R27(self):
        self.require_oracle("A13")
        r = run_vector("A13")  # hata vermeden tamamlanmalı
        self.assert_matches("A13", r)

    def test_asiri_kucuk_etki_buyuklugu_cozucu_sinirlarini_yoklar_R22_R27_U03(self):
        self.require_oracle("A14")
        r = run_vector("A14")
        self.assert_matches("A14", r)

    def test_cok_buyuk_etki_buyuklugu_grup_basina_alt_sinira_dayanir_R24(self):
        self.require_oracle("A16")
        r = run_vector("A16")
        self.assert_matches("A16", r)
        self.assertGreaterEqual(r.n_per_group, 2)

    def test_asiri_buyuk_etki_buyuklugu_R08_ust_sinir_R24(self):
        self.require_oracle("A17")
        r = run_vector("A17")
        self.assert_matches("A17", r)

    def test_guc_alphaya_tam_esit_oldugunda_hesap_yapilir_R07(self):
        self.require_oracle("A21")
        try:
            r = run_vector("A21")
        except InvalidInputError as exc:  # pragma: no cover
            self.fail(f"geçersiz girdi hatası beklenmiyordu: {exc}")
        self.assert_matches("A21", r)

    def test_guc_alphadan_kucuk_oldugunda_gecersiz_girdi_hatasi_R07(self):
        row = vector("A22")
        with self.assertRaises(PowerBelowAlphaError) as ctx:
            run_vector("A22")
        self.assertEqual(ctx.exception.field, "power")
        # G*Power mesajı oracle'da kayıtlı: aynı anlamı taşımalı
        self.assertIn("Power must be greater than or equal to alpha",
                      row["gpower_message"])
        self.assertIn("greater than or equal to alpha", str(ctx.exception))

    def test_guc_alphanin_hemen_ustunde_kabul_edilir_R07(self):
        self.require_oracle("A23")
        r = run_vector("A23")
        self.assert_matches("A23", r)

    def test_tum_a_priori_oracle_vektorleri_uyusur_R14_R25(self):
        """Senaryolarda adı geçmeyen A vektörleri için ek regresyon testi."""
        from oracle import VECTORS
        for vid, row in VECTORS.items():
            if row["mode"] != "a-priori" or not vid.startswith("A"):
                continue
            if row["df1"].strip() in ("", "?"):
                continue
            with self.subTest(vector=vid):
                self.assert_matches(vid, run_vector(vid))


# --------------------------------------------------------------------------
# Geçersiz girdiler (beklenen davranış SPEC R31 tablosundan gelir)
# --------------------------------------------------------------------------
class TestInvalidInputs(unittest.TestCase):

    def assert_error(self, vid, exc_type, field):
        with self.assertRaises(exc_type) as ctx:
            run_vector(vid)
        self.assertEqual(ctx.exception.field, field)
        return ctx.exception

    def test_a_priori_sifir_etki_buyuklugu_reddedilir_R08_R31_U07(self):
        self.assert_error("X01", EffectSizeRangeError, "f")

    def test_negatif_etki_buyuklugu_reddedilir_R08_R31(self):
        exc = self.assert_error("X02", EffectSizeRangeError, "f")
        self.assertIn("range", str(exc))

    def test_alpha_sinir_disi_degerleri_reddedilir_R05_R31(self):
        for vid in ("X03", "X04"):
            with self.subTest(vector=vid):
                self.assert_error(vid, AlphaRangeError, "alpha")

    def test_guc_birim_degeri_reddedilir_R06_R31(self):
        self.assert_error("X05", PowerRangeError, "power")

    def test_gecersiz_grup_sayilari_reddedilir_R04_R31__X07_cikarildi_R35(self):
        # SPEC v1.1: R32 yerine R35 geçti. X07 (k=2.5) artık hata değil, k=3'e
        # yuvarlanıp hesaplanır (bkz. TestSpecV11). Burada yalnızca X06, X08 kalır.
        for vid in ("X06", "X08"):
            with self.subTest(vector=vid):
                self.assert_error(vid, GroupCountError, "k")

    def test_hata_metinleri_gpower_ile_ayni_R36(self):
        """'Input error: ...' kaydı olan her vektörde motor aynı metni üretir."""
        from oracle import VECTORS
        prefix = "Input error: "
        checked = 0
        for vid, row in VECTORS.items():
            msg = row["gpower_message"].strip()
            if not msg.startswith(prefix):
                continue
            expected = msg[len(prefix):].split(" | ")[0].strip()
            with self.subTest(vector=vid):
                with self.assertRaises(InvalidInputError) as ctx:
                    run_vector(vid)
                self.assertEqual(str(ctx.exception), expected)
                checked += 1
        self.assertGreaterEqual(checked, 9)


# --------------------------------------------------------------------------
# SPEC v1.1 (bölüm 10): diferansiyel test bulguları
# --------------------------------------------------------------------------
class TestSpecV11(OracleMixin, unittest.TestCase):

    def test_kesirli_grup_sayisi_en_yakin_tamsayiya_yuvarlanir_R35(self):
        for vid in ("X07", "X09"):
            with self.subTest(vector=vid):
                self.require_oracle(vid)
                try:
                    r = run_vector(vid)
                except InvalidInputError as exc:
                    self.fail(f"{vid}: geçersiz girdi hatası beklenmiyordu: {exc}")
                self.assert_matches(vid, r)

    def test_kesirli_toplam_orneklem_en_yakin_tamsayiya_yuvarlanir_R35_R29(self):
        for vid in ("P13", "P14"):
            with self.subTest(vector=vid):
                row = self.require_oracle(vid)
                r = run_vector(vid)
                self.assert_matches(vid, r)
                # toplam örneklem alanı yuvarlanmış değeri gösterir
                self.assertEqual(r.n_total, int(row["n_total"]))
                self.assertIsInstance(r.n_total, int)

    def test_yarim_yukari_yuvarlama_bankaci_yuvarlamasi_degil_R35(self):
        cases = {2.5: 3, 3.5: 4, 4.5: 5, 2.4: 2, 2.6: 3, 3.0: 3, 159.4: 159, 159.6: 160}
        for x, expected in cases.items():
            with self.subTest(x=x):
                self.assertEqual(engine.round_half_up(x), expected)
        # 4.5 -> 5 ile k=5 (post hoc): bölünebilir, uyarı yok; 2.5 -> 3 grup
        r = engine.post_hoc(0.25, 0.05, 100.0, 4.5)
        self.assertEqual(r.df1, 4)
        self.assertIsNone(r.warning)

    def test_yuvarlama_dogrulamadan_once_yapilir_R35_R04_R09(self):
        with self.assertRaises(GroupCountError):
            engine.a_priori(0.25, 0.05, 0.8, 1.4)        # -> 1
        engine.a_priori(0.25, 0.05, 0.8, 1.5)            # -> 2, geçerli
        with self.assertRaises(SampleSizeError):
            engine.post_hoc(0.25, 0.05, 3.4, 3)          # -> 3 = k
        self.assertEqual(engine.post_hoc(0.25, 0.05, 3.5, 3).n_total, 4)

    def test_uyari_metni_gpower_ile_ayni_ve_yuvarlanmis_N_icerir_R36_R29(self):
        from oracle import VECTORS
        prefix = "Please note: "
        checked = 0
        for vid, row in VECTORS.items():
            msg = row["gpower_message"].strip()
            if not msg.startswith(prefix):
                continue
            expected = msg[len(prefix):].split(" | ")[0].strip()
            with self.subTest(vector=vid):
                self.assertEqual(run_vector(vid).warning, expected)
                checked += 1
        self.assertGreaterEqual(checked, 5)
        self.assertIn("(160)", run_vector("P14").warning)

    def test_uyarisiz_vektorlerde_uyari_yok_R26_R29(self):
        from oracle import VECTORS
        for vid, row in VECTORS.items():
            if row["df1"].strip() in ("", "?"):
                continue
            if row["gpower_message"].strip().startswith("Please note: "):
                continue
            with self.subTest(vector=vid):
                self.assertIsNone(run_vector(vid).warning)

    def test_post_hoc_f_sifir_guc_alpha_ve_uyari_R38(self):
        row = self.require_oracle("P07")
        r = run_vector("P07")
        self.assertEqual(r.ncp, 0.0)
        self.assertAlmostEqual(r.power, float(row["alpha"]), places=12)
        self.assertIsNotNone(r.warning)
        self.assert_matches("P07", r)

    def test_tum_oracle_vektorleri_uyusur_R14_R38(self):
        """Sayısal çıktısı olan 40 vektörün tümü (A, P, X07, X09) için regresyon."""
        from oracle import VECTORS
        count = 0
        for vid, row in VECTORS.items():
            if row["df1"].strip() in ("", "?"):
                continue
            with self.subTest(vector=vid):
                self.assert_matches(vid, run_vector(vid))
                count += 1
        self.assertEqual(count, 40)  # 26 A + X07, X09 + 12 P


# --------------------------------------------------------------------------
# Post hoc
# --------------------------------------------------------------------------
class TestPostHoc(OracleMixin, unittest.TestCase):

    def test_post_hoc_a_priori_sonucuyla_tutarlidir_R28__oracle(self):
        self.require_oracle("P01")
        self.assert_matches("P01", run_vector("P01"))

    def test_post_hoc_a_priori_sonucuyla_tutarlidir_R28__A02_gucu(self):
        a02 = vector("A02")
        r = run_vector("P01")
        self.assertTrue(matches_display(r.power, a02["actual_power"]))

    def test_kilavuz_ornegiyle_post_hoc_tutarliligi_R28__oracle(self):
        self.require_oracle("P09")
        self.assert_matches("P09", run_vector("P09"))

    def test_kilavuz_ornegiyle_post_hoc_tutarliligi_R28__A01_gucu(self):
        a01 = vector("A01")
        r = run_vector("P09")
        self.assertTrue(matches_display(r.power, a01["actual_power"]))

    def test_post_hoc_k_ya_bolunmeyen_orneklem_R10_R29__uyari(self):
        for vid in ("P02", "P11"):
            with self.subTest(vector=vid):
                row = inputs(vector(vid))
                try:
                    r = run_vector(vid)
                except InvalidInputError as exc:  # pragma: no cover
                    self.fail(f"hata beklenmiyordu: {exc}")
                self.assertEqual(r.df2, int(row["n"]) - int(row["k"]))
                self.assertIsNotNone(r.warning)
                self.assertIn("multiple", r.warning)
                self.assertIn("average group size", r.warning)
                self.assertIsNone(r.n_per_group)
                # Uyarısız başarıdan ayırt edilebilir
                ok = engine.post_hoc(0.25, 0.05, 159, 3)
                self.assertIsNone(ok.warning)

    def test_post_hoc_k_ya_bolunmeyen_orneklem_R10_R29__oracle(self):
        for vid in ("P02", "P11"):
            with self.subTest(vector=vid):
                self.require_oracle(vid)
                self.assert_matches(vid, run_vector(vid),
                                    columns=("lambda", "critical_F", "df1",
                                             "df2", "actual_power"))

    def test_post_hoc_sifir_etki_buyuklugu_guc_alphaya_esit_R08_R19(self):
        row = inputs(vector("P07"))
        r = run_vector("P07")
        self.assertEqual(r.ncp, 0.0)
        self.assertAlmostEqual(r.power, row["alpha"], places=12)

    def test_post_hoc_sifir_etki_buyuklugu_R08_R19__oracle(self):
        self.require_oracle("P07")
        self.assert_matches("P07", run_vector("P07"), columns=("actual_power",))

    def test_payda_df_birime_indiginde_hesap_yapilir_R09(self):
        r = run_vector("P03")
        self.assertEqual(r.df2, 1)

    def test_payda_df_birime_indiginde_hesap_yapilir_R09__oracle(self):
        self.require_oracle("P03")
        self.assert_matches("P03", run_vector("P03"))

    def test_payda_df_sifira_indiginde_hata_R09_R31(self):
        with self.assertRaises(SampleSizeError) as ctx:
            run_vector("P04")
        self.assertEqual(ctx.exception.field, "n_total")

    def test_toplam_orneklem_grup_sayisindan_kucuk_hata_R09_R31(self):
        with self.assertRaises(SampleSizeError) as ctx:
            run_vector("P08")
        self.assertEqual(ctx.exception.field, "n_total")

    def test_cok_buyuk_toplam_orneklemde_hassasiyet_korunur_R18_U01(self):
        self.require_oracle("P12")
        self.assert_matches("P12", run_vector("P12"))


# --------------------------------------------------------------------------
# Çıktı biçimi
# --------------------------------------------------------------------------
class TestOutputFormat(unittest.TestCase):

    def test_cikti_tam_duyarlikla_uretilir_kisaltma_sunumdadir_R12(self):
        from scipy import stats
        from anova_clone import cli
        r = run_vector("P01")
        # Motor kısaltmadan döndürür: doğrudan dağılım çağrısıyla bit-bit aynı
        crit = stats.f.isf(0.05, 2, 156)
        self.assertEqual(r.critical_f, crit)
        self.assertEqual(r.ncp, 0.25 ** 2 * 159)
        self.assertNotEqual(r.power, round(r.power, cli.JSON_DECIMALS))
        # Sunum katmanı biçimlendirir
        payload = cli.format_result(r, mode="post-hoc")
        self.assertEqual(payload[cli.NAMES["out_power_post_hoc"]],
                         round(r.power, cli.JSON_DECIMALS))


if __name__ == "__main__":
    unittest.main()
