"""Tek yönlü sabit etkili ANOVA omnibus güç analizi (G*Power davranış klonu)."""
from .engine import Result, a_priori, post_hoc

__all__ = ["Result", "a_priori", "post_hoc"]
__version__ = "0.1.0"
