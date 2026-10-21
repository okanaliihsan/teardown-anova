"""Geçersiz girdi istisnaları (SPEC R31, R34).

Her istisna sorunlu girdi alanının adını `field` özniteliğinde taşır. Alan adları
motorun parametre adlarıdır (f, alpha, power, k, n_total); dış dünyaya hangi adla
gösterileceği adaptörün (cli) işidir.
"""
from __future__ import annotations


class InvalidInputError(ValueError):
    """Tüm geçersiz girdi hatalarının tabanı."""

    field: str = ""

    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field
        self.message = message


class GroupCountError(InvalidInputError):
    """R04/R32: k tam sayı değil ya da k < 2."""


class AlphaRangeError(InvalidInputError):
    """R05: α izinli aralığın dışında."""


class PowerRangeError(InvalidInputError):
    """R06: hedef güç izinli aralığın dışında."""


class PowerBelowAlphaError(InvalidInputError):
    """R07: hedef güç < α."""


class EffectSizeRangeError(InvalidInputError):
    """R08: f izinli aralığın dışında (negatif ayrı ele alınmaz, R31/L47)."""


class SampleSizeError(InvalidInputError):
    """R09/R33: post hoc'ta N ≤ k ya da N tam sayı değil."""


class SolverError(RuntimeError):
    """A priori çözücü bir kök parantezleyemedi ya da yakınsayamadı (U03).

    Bu bir girdi hatası değil, hesaplanamama durumudur.
    """
