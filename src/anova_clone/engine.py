"""Tek yönlü sabit etkili ANOVA omnibus güç analizi motoru (SPEC R01-R34).

Saf fonksiyonlar; G/Ç yok; tüm değerler tam duyarlıklı float/int döner.
Gösterim (yuvarlama, anlamlı basamak) bu modülün işi değildir (R12).
"""
from __future__ import annotations

import math
import numbers
from dataclasses import dataclass
from typing import Optional

from scipy import optimize, stats

from .errors import (AlphaRangeError, EffectSizeRangeError, GroupCountError,
                     PowerBelowAlphaError, PowerRangeError, SampleSizeError,
                     SolverError)

# --- Girdi aralıkları (R05, R06, R08) -------------------------------------
PROB_MIN = 1e-07
PROB_MAX = 0.9999999
F_MAX = 50.0
F_MIN_A_PRIORI = 1e-06
F_MIN_POST_HOC = 0.0
K_MIN = 2

# --- Merkezi dağılıma geçiş eşiği (R19; tam değer bilinmiyor, ASSUMPTIONS U01)
NCP_CENTRAL_THRESHOLD = 1e-12

# --- Çözücü sabitleri (R21, R22) -----------------------------------------
BRACKET_SPAN = 100.0            # ilk üst uç: k + 100
BRACKET_GROWTH = 1.6            # geometrik genişletme çarpanı
SOLVER_MAX_ITER = 300
SOLVER_RTOL = 4.0 * 2.220446049250313e-16   # bağıl makine duyarlığı mertebesi
SOLVER_XTOL = 1e-10             # mutlak tolerans (U02)
MAX_EXPANSIONS = 200            # U03: ~1.6^200 ≈ 1e40; pratikte sınırsız

# --- G*Power'da gözlenen metinler (SPEC v1.1 R36) ----------------------
# Aralıklar G*Power'ın gösterdiği biçimde yazılır: üst sınır 0.9999999 iken
# metinde "1" görünür (oracle X03-X05).
MSG_F_RANGE = "Effect size f is outside the admissible range ({lo:g}, {hi:g})."
MSG_ALPHA_RANGE = "Alpha is outside the admissible range (1e-07, 1)."
MSG_POWER_RANGE = "Power is outside the admissible range (1e-07, 1)."
MSG_POWER_BELOW_ALPHA = "Power must be greater than or equal to alpha."
MSG_GROUPS = "There must be at least 2 groups."
MSG_SAMPLE_SIZE = "Sample size must be greater than the number of groups ({k})."
NON_MULTIPLE_WARNING = (
    "The total sample size ({n}) is not a multiple of the number of groups ({k}). "
    "The analysis was based on the average group size."
)


@dataclass(frozen=True)
class Result:
    ncp: float
    critical_f: float
    df1: int
    df2: int
    n_total: int
    n_per_group: Optional[int]
    power: float
    warning: Optional[str] = None


# ---------------------------------------------------------------------------
# Doğrulama
# ---------------------------------------------------------------------------
def _as_real(value, field, exc_type, message):
    """Sayı olmayan / sonlu olmayan girdi, alanın G*Power metniyle reddedilir."""
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise exc_type(field, message)
    x = float(value)
    if math.isnan(x) or math.isinf(x):
        raise exc_type(field, message)
    return x


def round_half_up(x: float) -> int:
    """En yakın tam sayıya yuvarlar; tam .5 yukarı gider (R35).

    Python'un round() fonksiyonu bankacı yuvarlaması yapar (2.5 -> 2), bu yüzden
    kullanılmaz. `x - floor(x)` kayan noktada kesindir; `floor(x + 0.5)`'in
    0.49999999999999994 gibi değerlerdeki hatası burada oluşmaz.
    """
    lo = math.floor(x)
    return int(lo + 1 if x - lo >= 0.5 else lo)


def _as_int(value, field, exc_type, message):
    """R35: k ve N doğrulamadan önce en yakın tam sayıya (.5 yukarı) yuvarlanır."""
    return round_half_up(_as_real(value, field, exc_type, message))


def _check_k(k) -> int:
    k_int = _as_int(k, "k", GroupCountError, MSG_GROUPS)
    if k_int < K_MIN:
        raise GroupCountError("k", MSG_GROUPS)
    return k_int


def _check_prob(x, field, exc_type, message) -> float:
    v = _as_real(x, field, exc_type, message)
    if not (PROB_MIN <= v <= PROB_MAX):
        raise exc_type(field, message)
    return v


def _check_f(f, f_min) -> float:
    message = MSG_F_RANGE.format(lo=f_min, hi=F_MAX)
    v = _as_real(f, "f", EffectSizeRangeError, message)
    if not (f_min <= v <= F_MAX):
        raise EffectSizeRangeError("f", message)
    return v


# ---------------------------------------------------------------------------
# Çekirdek hesap (R14-R19)
# ---------------------------------------------------------------------------
def degrees_of_freedom(n_total: float, k: int):
    """R14, R15. Sürekli N için df2 de sürekli olur (çözücü kullanımı)."""
    return k - 1, n_total - k


def noncentrality(f: float, n_total: float) -> float:
    """R16: λ = f² · N (toplam N)."""
    return f * f * n_total


def critical_f(alpha: float, df1: float, df2: float) -> float:
    """R17: merkezi F'nin 1-α kantili. `isf(α)` = `ppf(1-α)`, küçük α'da daha doğru."""
    return float(stats.f.isf(alpha, df1, df2))


def _right_tail(x: float, df1: float, df2: float, ncp: float) -> float:
    """R18, R19: λ ihmal edilebilirse merkezi F'ye geçilir."""
    if ncp < NCP_CENTRAL_THRESHOLD:
        return float(stats.f.sf(x, df1, df2))
    return float(stats.ncf.sf(x, df1, df2, ncp))


def power_continuous(f: float, alpha: float, n_total: float, k: int) -> float:
    """Gücü (sürekli) N'in fonksiyonu olarak verir; a priori hedef fonksiyonu (R20)."""
    df1, df2 = degrees_of_freedom(n_total, k)
    crit = critical_f(alpha, df1, df2)
    return _right_tail(crit, df1, df2, noncentrality(f, n_total))


def _compute(f: float, alpha: float, n_total: int, k: int,
             warning: Optional[str] = None) -> Result:
    df1, df2 = degrees_of_freedom(n_total, k)
    ncp = noncentrality(f, n_total)
    crit = critical_f(alpha, df1, df2)
    pw = _right_tail(crit, df1, df2, ncp)
    n_per_group = n_total // k if n_total % k == 0 else None   # R30
    return Result(ncp=ncp, critical_f=crit, df1=df1, df2=df2, n_total=n_total,
                  n_per_group=n_per_group, power=pw, warning=warning)


# ---------------------------------------------------------------------------
# A priori çözücü (R20-R27)
# ---------------------------------------------------------------------------
def _find_bracket(g, k: int):
    """R22: [k+1, k+100]; gerekirse üst uç 1.6 ile büyütülür, alt uç önceki üst uca kayar.

    Dönüş: (lo, hi) ya da kök alt sınırda/altındaysa (lo, None).
    """
    lower_bound = k + 1.0
    lo, hi = lower_bound, k + BRACKET_SPAN
    g_lo = g(lo)
    if g_lo >= 0.0:
        return lo, None                 # kök alt sınırda ya da altında (R24)
    g_hi = g(hi)
    expansions = 0
    while g_hi < 0.0:
        if expansions >= MAX_EXPANSIONS or not math.isfinite(hi):
            raise SolverError("Could not bracket the required sample size "
                              "(target power not reachable).")
        lo = hi                         # parantez aşağı doğru daraltılır
        hi = hi * BRACKET_GROWTH
        g_hi = g(hi)
        expansions += 1
    return lo, hi


def solve_continuous_n(f: float, alpha: float, target_power: float, k: int) -> float:
    """g(N) = güç(N) − hedef = 0 denkleminin sürekli kökü (R20, R21).

    Kök alt sınırın (k+1) altındaysa k+1 döner.
    """
    def g(n):
        return power_continuous(f, alpha, n, k) - target_power

    lo, hi = _find_bracket(g, k)
    if hi is None:
        return lo
    try:
        root, info = optimize.brentq(g, lo, hi, xtol=SOLVER_XTOL, rtol=SOLVER_RTOL,
                                     maxiter=SOLVER_MAX_ITER, full_output=True,
                                     disp=False)
    except ValueError as exc:            # işaret değişimi yok
        raise SolverError(f"Root finder failed: {exc}") from exc
    if not info.converged:
        raise SolverError("Root finder did not converge within "
                          f"{SOLVER_MAX_ITER} iterations.")
    return float(root)


def round_up_to_multiple(n_continuous: float, k: int) -> int:
    """R23, R24: grup başına n'yi yukarı yuvarla, toplam N = n_grup · k; alt sınır k+1."""
    lower_bound = k + 1
    n_group = math.ceil(n_continuous / k)
    n_total = n_group * k
    if n_total < lower_bound:
        n_total = math.ceil(lower_bound / k) * k
    return int(n_total)


def a_priori(f: float, alpha: float, power: float, k: int) -> Result:
    """A priori: gücü hedefe ulaştıran en küçük k katı N (R20-R26)."""
    k = _check_k(k)
    alpha = _check_prob(alpha, "alpha", AlphaRangeError, MSG_ALPHA_RANGE)
    power = _check_prob(power, "power", PowerRangeError, MSG_POWER_RANGE)
    if power < alpha:
        raise PowerBelowAlphaError("power", MSG_POWER_BELOW_ALPHA)
    f = _check_f(f, F_MIN_A_PRIORI)

    n_cont = solve_continuous_n(f, alpha, power, k)
    n_total = round_up_to_multiple(n_cont, k)
    # R25: gerçek güç yuvarlanmış N ile yeniden hesaplanır; R26: uyarı yok.
    return _compute(f, alpha, n_total, k)


# ---------------------------------------------------------------------------
# Post hoc (R28-R30)
# ---------------------------------------------------------------------------
def post_hoc(f: float, alpha: float, n_total: int, k: int) -> Result:
    k = _check_k(k)
    alpha = _check_prob(alpha, "alpha", AlphaRangeError, MSG_ALPHA_RANGE)
    f = _check_f(f, F_MIN_POST_HOC)
    n = _as_int(n_total, "n_total", SampleSizeError, MSG_SAMPLE_SIZE.format(k=k))
    if not n > k:
        raise SampleSizeError("n_total", MSG_SAMPLE_SIZE.format(k=k))
    warning = None
    if n % k != 0:                      # R29; R38: f = 0 iken de eklenir
        warning = NON_MULTIPLE_WARNING.format(n=n, k=k)
    return _compute(f, alpha, n, k, warning=warning)
