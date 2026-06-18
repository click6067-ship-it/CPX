"""
하네스 지표 — 이분법 채점 일치도. (sklearn 없이 투명하게 구현 = 원리 이해용)

Cohen's kappa = 우연 일치를 보정한 일치도.
  po = 실제 일치율, pe = 우연히 일치할 확률,  kappa = (po - pe) / (1 - pe)
  해석: <0 우연이하 · 0~.2 미미 · .2~.4 약함 · .4~.6 보통 · .6~.8 상당 · .8~1 거의완벽
"""
from __future__ import annotations


def accuracy(a: list[bool], b: list[bool]) -> float:
    return sum(x == y for x, y in zip(a, b)) / len(a) if a else 0.0


def cohen_kappa(a: list[bool], b: list[bool]) -> float:
    """두 이분법 라벨열의 Cohen's kappa."""
    n = len(a)
    if n == 0:
        return 0.0
    po = sum(x == y for x, y in zip(a, b)) / n
    pa = sum(a) / n          # a가 True인 비율
    pb = sum(b) / n          # b가 True인 비율
    pe = pa * pb + (1 - pa) * (1 - pb)   # 우연 일치 확률
    if pe >= 1.0:
        return 1.0           # 둘 다 모두 True(또는 모두 False) → 완전 일치로 처리
    return (po - pe) / (1 - pe)


def prf(pred: list[bool], gold: list[bool]) -> dict:
    """precision/recall/F1. positive = '도달(reached)=True'.
    precision = AI가 '도달'이라 한 것 중 맞은 비율 (헛點 안 주나)
    recall    = 실제 도달 중 AI가 잡은 비율 (놓치지 않나)
    """
    tp = sum(p and g for p, g in zip(pred, gold))
    fp = sum(p and not g for p, g in zip(pred, gold))
    fn = sum((not p) and g for p, g in zip(pred, gold))
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}
