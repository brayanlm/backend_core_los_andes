from datetime import datetime, timedelta, timezone
from typing import List, Tuple


def calcular_cuota_mensual(monto: float, plazo_meses: int, tea: float = 0.25) -> float:
    if plazo_meses <= 0:
        return 0.0
    tem = (1 + tea) ** (1 / 12) - 1
    if tem == 0:
        return monto / plazo_meses
    factor = (tem * (1 + tem) ** plazo_meses) / ((1 + tem) ** plazo_meses - 1)
    return round(monto * factor, 2)


def generar_cronograma(
    monto: float,
    plazo_meses: int,
    tea: float = 0.25,
    fecha_desembolso: str = None,
) -> Tuple[List[dict], float, float]:
    tem = (1 + tea) ** (1 / 12) - 1
    cuota = calcular_cuota_mensual(monto, plazo_meses, tea)
    saldo = monto

    if fecha_desembolso:
        try:
            base = datetime.fromisoformat(fecha_desembolso)
        except (ValueError, TypeError):
            base = datetime.now(timezone.utc)
    else:
        base = datetime.now(timezone.utc)

    cronograma = []
    for i in range(1, plazo_meses + 1):
        interes = round(saldo * tem, 2)
        capital = round(cuota - interes, 2)
        if capital < 0:
            capital = 0.0
        saldo = round(saldo - capital, 2)
        if saldo < 0:
            saldo = 0.0
        vencimiento = base + timedelta(days=30 * i)
        cronograma.append({
            "nro_cuota": i,
            "fecha_vencimiento": vencimiento.date().isoformat(),
            "monto_cuota": round(cuota, 2),
            "monto_capital": capital,
            "monto_interes": interes,
            "saldo": saldo,
            "estado_cuota": "pendiente",
        })

    total_interes = sum(c["monto_interes"] for c in cronograma)
    total_pagar = round(cuota * plazo_meses, 2)
    return cronograma, round(total_interes, 2), total_pagar


def calcular_score(ingreso: float, monto: float, plazo: int) -> int:
    cuota = calcular_cuota_mensual(monto, plazo)
    ratio = cuota / ingreso if ingreso > 0 else 1
    score = 100
    if ratio > 0.30:
        score -= 20
    if ratio > 0.35:
        score -= 15
    if monto / ingreso > 6:
        score -= 15
    if plazo > 60:
        score -= 10
    if plazo <= 12:
        score += 10
    return max(0, min(100, score))
