"""Cálculos do portal: indicadores por estado, totais do Brasil e projeção do 2º turno.

Todos os números do portal saem das funções deste arquivo, a partir dos dados
oficiais do TSE em data/presidente_2026_por_uf.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

PASTA_DADOS = Path(__file__).parent / "data"
ARQ_RESULTADOS = PASTA_DADOS / "presidente_2026_por_uf.json"
ARQ_MALHA = PASTA_DADOS / "br_uf.geojson"

# Código IBGE da UF (usado na malha territorial) -> sigla
COD_IBGE_UF = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
    "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}


def carregar_resultados(caminho: Path = ARQ_RESULTADOS) -> pd.DataFrame:
    """Uma linha por UF (e exterior, 'ZZ') com os votos dos dois turnos."""
    with open(caminho, encoding="utf-8-sig") as f:
        return pd.DataFrame(json.load(f))


def _area(anel: list) -> float:
    """Área com sinal (fórmula do laço): negativa = sentido horário."""
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(anel, anel[1:])) / 2


def _orientar(poligono: list) -> list:
    """Contorno externo no sentido horário e buracos no anti-horário, como o Plotly espera.

    A malha do IBGE segue o padrão GeoJSON (externo anti-horário); sem isso o mapa sai invertido.
    """
    out = []
    for i, anel in enumerate(poligono):
        horario = _area(anel) < 0
        quer_horario = i == 0
        out.append(anel if horario == quer_horario else anel[::-1])
    return out


def carregar_malha(caminho: Path = ARQ_MALHA) -> dict:
    """GeoJSON dos estados do IBGE, com a sigla da UF em properties.uf."""
    with open(caminho, encoding="utf-8-sig") as f:
        malha = json.load(f)
    for feat in malha["features"]:
        feat["properties"]["uf"] = COD_IBGE_UF[feat["properties"]["codarea"]]
        geo = feat["geometry"]
        if geo["type"] == "Polygon":
            geo["coordinates"] = _orientar(geo["coordinates"])
        elif geo["type"] == "MultiPolygon":
            geo["coordinates"] = [_orientar(p) for p in geo["coordinates"]]
    return malha


def indicadores_por_estado(df: pd.DataFrame) -> pd.DataFrame:
    """Percentuais, vencedor, diferença e votos ganhos entre os turnos, por UF."""
    out = df[["uf", "estado", "regiao"]].copy()
    l1, f1, v1 = df["t1_lula"], df["t1_flavio"], df["t1_validos"]
    l2, f2, v2 = df["t2_lula"], df["t2_flavio"], df["t2_validos"]
    out["t1_lula"], out["t1_flavio"] = l1, f1
    out["t2_lula"], out["t2_flavio"] = l2, f2
    out["t1_lula_pct"], out["t1_flavio_pct"] = l1 / v1, f1 / v1
    out["t2_lula_pct"], out["t2_flavio_pct"] = l2 / v2, f2 / v2
    out["margem_t1"] = (l1 - f1) / v1
    out["margem_t2"] = (l2 - f2) / v2
    out["ganho_lula"] = l2 - l1
    out["ganho_flavio"] = f2 - f1
    out["lider_t1"] = np.where(l1 > f1, "Lula", "Flávio")
    out["vencedor_t2"] = np.where(l2 > f2, "Lula", "Flávio")
    out["dif_t1"] = (l1 - f1).abs()
    out["dif_t2"] = (l2 - f2).abs()
    out["virou"] = np.where((l1 > f1) != (l2 > f2), "Virou", "Manteve")
    out["comp_t2_pct"] = df["t2_comparecimento"] / df["t2_eleitorado"]
    return out


def totais_brasil(df: pd.DataFrame) -> dict:
    """Soma de todas as UFs e do exterior."""
    s = df.select_dtypes("number").sum()
    return {
        "t1_lula": int(s.t1_lula), "t1_flavio": int(s.t1_flavio),
        "t2_lula": int(s.t2_lula), "t2_flavio": int(s.t2_flavio),
        "t1_lula_pct": s.t1_lula / s.t1_validos, "t1_flavio_pct": s.t1_flavio / s.t1_validos,
        "t2_lula_pct": s.t2_lula / s.t2_validos, "t2_flavio_pct": s.t2_flavio / s.t2_validos,
        "t2_margem": int(s.t2_lula - s.t2_flavio), "t1_margem_flavio": int(s.t1_flavio - s.t1_lula),
        "ganho_lula": int(s.t2_lula - s.t1_lula), "ganho_flavio": int(s.t2_flavio - s.t1_flavio),
        "t1_comp_pct": s.t1_comparecimento / s.t1_eleitorado,
        "t2_comp_pct": s.t2_comparecimento / s.t2_eleitorado,
    }


def _ajuste_transferencia(df: pd.DataFrame) -> tuple[float, float]:
    """Regressão sem intercepto: ganho de Lula = a * outros_1T + b * variação de válidos.

    a = parcela dos votos dos demais candidatos que foi para Lula;
    b = parcela da variação de votos válidos (eleitores a mais no 2º turno) que foi para Lula.
    """
    outros = df["t1_validos"] - df["t1_lula"] - df["t1_flavio"]
    novos = df["t2_validos"] - df["t1_validos"]
    y = df["t2_lula"] - df["t1_lula"]
    X = np.column_stack([outros, novos]).astype(float)
    (a, b), *_ = np.linalg.lstsq(X, y.astype(float), rcond=None)
    return float(a), float(b)


def transferencia_brasil(df: pd.DataFrame) -> dict:
    a, b = _ajuste_transferencia(df)
    return {"transf_outros_lula": a, "transf_novos_lula": b}


def projecao(df: pd.DataFrame) -> pd.DataFrame:
    """Projeta o 2º turno de cada UF só com o 1º turno dela.

    - modelo: transferência ajustada nas OUTRAS UFs (a UF nunca entra no próprio cálculo);
    - ingenuo: mantém a proporção Lula x Flávio do 1º turno.
    Em ambos, os válidos do 2º turno = válidos do 1º x variação média das outras UFs.
    """
    linhas = []
    for _, s in df.iterrows():
        outras = df[df["uf"] != s["uf"]]
        a, b = _ajuste_transferencia(outras)
        razao = outras["t2_validos"].sum() / outras["t1_validos"].sum()
        v2_proj = s["t1_validos"] * razao
        outros = s["t1_validos"] - s["t1_lula"] - s["t1_flavio"]
        real = s["t2_lula"] / s["t2_validos"]
        cenarios = {
            "modelo": s["t1_lula"] + a * outros + b * (v2_proj - s["t1_validos"]),
            "ingenuo": v2_proj * s["t1_lula"] / (s["t1_lula"] + s["t1_flavio"]),
        }
        for cenario, lula in cenarios.items():
            pct = lula / v2_proj
            linhas.append({
                "uf": s["uf"], "estado": s["estado"], "regiao": s["regiao"], "cenario": cenario,
                "proj_lula": round(lula), "proj_flavio": round(v2_proj - lula),
                "proj_lula_pct": pct, "real_lula_pct": real, "erro_pp": pct - real,
                "acertou": "Acertou" if (pct > 0.5) == (real > 0.5) else "Errou",
            })
    return pd.DataFrame(linhas)


def precisao(proj: pd.DataFrame) -> pd.DataFrame:
    """Erro médio absoluto (em fração) e número de UFs com vencedor correto, por cenário."""
    return (
        proj.assign(erro_abs=proj["erro_pp"].abs(), ok=proj["acertou"].eq("Acertou"))
        .groupby("cenario")
        .agg(mae=("erro_abs", "mean"), acertos=("ok", "sum"), total=("uf", "count"))
        .reset_index()
    )


if __name__ == "__main__":
    dados = carregar_resultados()
    tot = totais_brasil(dados)
    print(f"Lula 2º turno: {tot['t2_lula']:,} ({tot['t2_lula_pct']:.2%})")
    print(f"Flávio 2º turno: {tot['t2_flavio']:,} ({tot['t2_flavio_pct']:.2%})")
    print(precisao(projecao(dados)))
