"""Baixa os resultados oficiais de presidente 2026 do TSE e a malha dos estados do IBGE.

Uso:  python baixar_dados.py
Gera data/presidente_2026_por_uf.json e data/br_uf.geojson.
"""

from __future__ import annotations

import json
from pathlib import Path

import requests

PASTA = Path(__file__).parent / "data"
TSE = "https://resultados.tse.jus.br/oficial/ele2026/{ele}/dados/{uf}/{uf}-c0001-e00{ele}-u.json"
ELEICOES = {"t1": 6257, "t2": 6258}  # 1º e 2º turno, presidente
IBGE = ("https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
        "?formato=application/vnd.geo%2Bjson&intrarregiao=UF&qualidade=minima")

UFS = {
    "AC": ("Acre", "Norte"), "AL": ("Alagoas", "Nordeste"), "AM": ("Amazonas", "Norte"),
    "AP": ("Amapá", "Norte"), "BA": ("Bahia", "Nordeste"), "CE": ("Ceará", "Nordeste"),
    "DF": ("Distrito Federal", "Centro-Oeste"), "ES": ("Espírito Santo", "Sudeste"),
    "GO": ("Goiás", "Centro-Oeste"), "MA": ("Maranhão", "Nordeste"), "MG": ("Minas Gerais", "Sudeste"),
    "MS": ("Mato Grosso do Sul", "Centro-Oeste"), "MT": ("Mato Grosso", "Centro-Oeste"),
    "PA": ("Pará", "Norte"), "PB": ("Paraíba", "Nordeste"), "PE": ("Pernambuco", "Nordeste"),
    "PI": ("Piauí", "Nordeste"), "PR": ("Paraná", "Sul"), "RJ": ("Rio de Janeiro", "Sudeste"),
    "RN": ("Rio Grande do Norte", "Nordeste"), "RO": ("Rondônia", "Norte"), "RR": ("Roraima", "Norte"),
    "RS": ("Rio Grande do Sul", "Sul"), "SC": ("Santa Catarina", "Sul"), "SE": ("Sergipe", "Nordeste"),
    "SP": ("São Paulo", "Sudeste"), "TO": ("Tocantins", "Norte"), "ZZ": ("Exterior", "Exterior"),
}

# Nome de urna no TSE -> nome da coluna
CANDIDATOS = {
    "LULA": "lula", "FLAVIO BOLSONARO": "flavio", "RONALDO CAIADO": "caiado",
    "ESCRITOR AUGUSTO CURY": "cury", "RENAN SANTOS": "renan", "ZEMA": "zema", "SAMARA": "samara",
    "HERTZ DIAS": "hertz", "EDMILSON COSTA": "edmilson", "CLARIANA BARAO": "clariana",
    "VETERINÁRIO WILSON GRASSI": "grassi", "RUI COSTA PIMENTA": "rui",
}


def resultado_uf(sessao: requests.Session, uf: str, ele: int) -> dict:
    r = sessao.get(TSE.format(ele=ele, uf=uf.lower()), timeout=60)
    r.raise_for_status()
    j = r.json()
    linha = {
        "eleitorado": int(j["e"]["te"]), "comparecimento": int(j["e"]["c"]), "abstencao": int(j["e"]["a"]),
        "validos": int(j["v"]["vv"]), "brancos": int(j["v"]["vb"]), "nulos": int(j["v"]["tvn"]),
    }
    for agr in j["carg"][0]["agr"]:
        for par in agr["par"]:
            for cand in par["cand"]:
                col = CANDIDATOS.get(cand["nmu"])
                if col is None:
                    raise ValueError(f"Candidato sem coluna: {cand['nmu']} ({uf})")
                linha[col] = int(cand["vap"])
    return linha


def main() -> None:
    PASTA.mkdir(exist_ok=True)
    linhas = []
    with requests.Session() as s:
        for uf, (estado, regiao) in UFS.items():
            linha = {"uf": uf, "estado": estado, "regiao": regiao}
            for turno, ele in ELEICOES.items():
                for k, v in resultado_uf(s, uf, ele).items():
                    linha[f"{turno}_{k}"] = v
            linhas.append(linha)
            print(f"{uf} ok")
        (PASTA / "presidente_2026_por_uf.json").write_text(json.dumps(linhas, ensure_ascii=False, indent=1), encoding="utf-8")
        malha = s.get(IBGE, timeout=60)
        malha.raise_for_status()
        (PASTA / "br_uf.geojson").write_bytes(malha.content)
    total_lula = sum(l["t2_lula"] for l in linhas)
    print(f"Pronto: {len(linhas)} unidades. Lula no 2º turno: {total_lula:,}".replace(",", "."))


if __name__ == "__main__":
    main()
