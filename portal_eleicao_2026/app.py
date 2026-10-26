"""Portal de transparência — Eleição Presidencial 2026 (1º e 2º turno).

Rodar localmente:  streamlit run app.py
Desenvolvido por João Pedro Silva de Morais e Marcos Vinicius Ananias Silva.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import calculos as calc

LULA, FLAVIO, PERDA, NEUTRO = "#d62839", "#2563c9", "#e08a00", "#eceef1"
CFG_GRAFICO = {"scrollZoom": False, "displaylogo": False, "modeBarButtonsToRemove": ["select2d", "lasso2d"]}
CREDITOS = "Desenvolvido por João Pedro Silva de Morais e Marcos Vinicius Ananias Silva"

st.set_page_config(page_title="Eleição Presidencial 2026", page_icon="🗳️", layout="wide")

st.markdown(
    """
    <style>
    .block-container {max-width: 1200px; padding-top: 2rem;}
    [data-testid="stMetricValue"] {font-size: 1.8rem;}
    .kpi-lula {border-top: 4px solid #d62839; padding-top: .4rem;}
    .kpi-flavio {border-top: 4px solid #2563c9; padding-top: .4rem;}
    .rodape {color: #6b7280; font-size: .85rem; border-top: 1px solid #e5e7eb; margin-top: 2rem; padding-top: 1rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- formatação pt-BR ----------
def fint(v: float) -> str:
    return f"{int(round(v)):,}".replace(",", ".")


def fsig(v: float) -> str:
    return ("+" if v > 0 else "−" if v < 0 else "") + fint(abs(v))


def fpct(v: float, casas: int = 2) -> str:
    return f"{v * 100:.{casas}f}%".replace(".", ",")


def fpp(v: float) -> str:
    return ("+" if v > 0 else "−" if v < 0 else "") + f"{abs(v) * 100:.1f} pp".replace(".", ",")


# ---------- dados ----------
@st.cache_data
def carregar():
    df = calc.carregar_resultados()
    return df, calc.indicadores_por_estado(df), calc.totais_brasil(df), calc.projecao(df), calc.carregar_malha()


dados, estados, tot, proj, malha = carregar()
prec = calc.precisao(proj).set_index("cenario")
transf = calc.transferencia_brasil(dados)

# ---------- cabeçalho ----------
st.caption("PORTAL DE TRANSPARÊNCIA · ELEIÇÕES 2026")
st.title("Eleição Presidencial 2026")
st.markdown(
    f"Lula venceu o 2º turno com **{fpct(tot['t2_lula_pct'])}** dos votos válidos, "
    f"**{fint(tot['t2_margem'])}** votos à frente de Flávio Bolsonaro. "
    f"No 1º turno, Flávio havia terminado **{fint(tot['t1_margem_flavio'])}** votos à frente."
)

regiao = st.selectbox(
    "Região", ["Brasil", "Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"], index=0
)


def filtrar(df: pd.DataFrame) -> pd.DataFrame:
    return df if regiao == "Brasil" else df[df["regiao"] == regiao]


est_uf = estados[estados["uf"] != "ZZ"]  # o exterior não aparece no mapa

aba_geral, aba_estados, aba_proj, aba_metodo = st.tabs(["Visão geral", "Estados", "Projeção", "Metodologia"])


def mapa(valores: pd.Series, cores, faixa, titulo_cor: str, hover: pd.DataFrame, altura: int = 520):
    fig = px.choropleth(
        hover.assign(valor=valores.values),
        geojson=malha, locations="uf", featureidkey="properties.uf", color="valor",
        color_continuous_scale=cores, range_color=faixa,
        hover_name="estado",
        hover_data={"uf": False, "valor": False, "1º turno": True, "2º turno": True, "Lula 1º → 2º": True, "Flávio 1º → 2º": True},
    )
    fig.update_geos(visible=False, projection_type="mercator", lonaxis_range=[-74.5, -34.2], lataxis_range=[-34.2, 5.8])
    fig.update_traces(marker_line_color="white", marker_line_width=0.8)
    fig.update_layout(
        height=altura, margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(title=titulo_cor, thickness=12, len=0.6),
        paper_bgcolor="rgba(0,0,0,0)", geo_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def hover_estados(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(
        **{
            "1º turno": df["lider_t1"] + " à frente por " + df["dif_t1"].map(fint) + " votos",
            "2º turno": df["vencedor_t2"] + " venceu por " + df["dif_t2"].map(fint) + " votos"
                        + np.where(df["virou"] == "Virou", " (virou)", ""),
            "Lula 1º → 2º": df["t1_lula"].map(fint) + " → " + df["t2_lula"].map(fint) + " (" + df["ganho_lula"].map(fsig) + ")",
            "Flávio 1º → 2º": df["t1_flavio"].map(fint) + " → " + df["t2_flavio"].map(fint) + " (" + df["ganho_flavio"].map(fsig) + ")",
        },
    )[["uf", "estado", "1º turno", "2º turno", "Lula 1º → 2º", "Flávio 1º → 2º"]]


def apagar_fora_da_regiao(df: pd.DataFrame, valores: pd.Series) -> pd.Series:
    if regiao == "Brasil":
        return valores
    return valores.where(df["regiao"] == regiao, np.nan)


# ---------- Visão geral ----------
with aba_geral:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="kpi-lula"></div>', unsafe_allow_html=True)
        st.metric("Lula (PT)", fint(tot["t2_lula"]), f"{fpct(tot['t2_lula_pct'])} no 2º turno", delta_color="off", delta_arrow="off")
    with c2:
        st.markdown('<div class="kpi-flavio"></div>', unsafe_allow_html=True)
        st.metric("Flávio Bolsonaro (PL)", fint(tot["t2_flavio"]), f"{fpct(tot['t2_flavio_pct'])} no 2º turno", delta_color="off", delta_arrow="off")
    with c3:
        st.metric("Votos ganhos por Lula entre os turnos", fsig(tot["ganho_lula"]),
                  f"Flávio: {fsig(tot['ganho_flavio'])}", delta_color="off", delta_arrow="off")
    with c4:
        st.metric("Comparecimento no 2º turno", fpct(tot["t2_comp_pct"], 1),
                  f"{fpct(tot['t1_comp_pct'], 1)} no 1º turno", delta_color="off", delta_arrow="off")

    st.subheader("Mapa por estado")
    opcao = st.radio(
        "Mostrar", ["Vencedor do 2º turno", "Vencedor do 1º turno", "Mudança da vantagem entre os turnos"],
        horizontal=True, label_visibility="collapsed",
    )
    campo = {"Vencedor do 2º turno": est_uf["margem_t2"], "Vencedor do 1º turno": est_uf["margem_t1"],
             "Mudança da vantagem entre os turnos": est_uf["margem_t2"] - est_uf["margem_t1"]}[opcao]
    lim = float(campo.abs().max())
    escala = [[0, FLAVIO], [0.5, NEUTRO], [1, LULA]]
    fig = mapa(apagar_fora_da_regiao(est_uf, campo * 100), escala, (-lim * 100, lim * 100),
               "pp (+ Lula)", hover_estados(est_uf))
    st.plotly_chart(fig, width="stretch", config=CFG_GRAFICO)
    st.caption("Vermelho: vantagem de Lula. Azul: vantagem de Flávio. Valores em pontos percentuais dos votos válidos.")

    st.subheader("Onde cada um ganhou votos do 1º para o 2º turno")
    st.caption("Mesma escala nos dois mapas. Laranja: o candidato perdeu votos naquele estado.")
    maximo = float(max(est_uf["ganho_lula"].max(), est_uf["ganho_flavio"].max()))
    m1, m2 = st.columns(2)
    for col, nome, cor, campo_g in [(m1, "Lula", LULA, "ganho_lula"), (m2, "Flávio", FLAVIO, "ganho_flavio")]:
        with col:
            st.markdown(f"**Votos ganhos por {nome}: {fsig(tot[campo_g])}**")
            # raiz quadrada para São Paulo não apagar os estados menores
            v = est_uf[campo_g]
            transformado = np.sign(v) * np.sqrt(v.abs() / maximo)
            menor = float(min(transformado.min(), 0))
            corte = (0 - menor) / (1 - menor) if menor < 0 else 0
            cores = ([[0, PERDA], [max(corte - 1e-6, 0), "#fbe3bf"]] if menor < 0 else []) + [[corte, NEUTRO], [1, cor]]
            figg = mapa(apagar_fora_da_regiao(est_uf, transformado), cores, (menor, 1), "", hover_estados(est_uf), altura=420)
            figg.update_layout(coloraxis_showscale=False)
            st.plotly_chart(figg, width="stretch", config=CFG_GRAFICO)
            top = filtrar(est_uf).nlargest(5, campo_g)[["estado", campo_g]]
            st.dataframe(
                top.assign(**{campo_g: top[campo_g].map(fsig)}).rename(columns={"estado": "Estado", campo_g: "Votos ganhos"}),
                hide_index=True, width="stretch",
            )
            visiveis = filtrar(est_uf)
            perdas = visiveis[visiveis[campo_g] < 0]
            if len(perdas):
                st.caption(f"{nome} perdeu votos em: " + ", ".join(f"{r.estado} ({fsig(r[campo_g])})" for _, r in perdas.iterrows()))

# ---------- Estados ----------
with aba_estados:
    st.subheader("Resultado e variação de votos por estado")
    st.caption("Diferença = votos do vencedor menos os do 2º colocado. Variação = votos no 2º turno menos votos no 1º. Clique no cabeçalho para ordenar.")
    tab = filtrar(estados).sort_values("dif_t2", ascending=False)
    exib = pd.DataFrame({
        "Estado": tab["estado"], "Vencedor": tab["vencedor_t2"], "Lula %": tab["t2_lula_pct"] * 100,
        "Diferença": tab["dif_t2"], "Liderança": tab["virou"],
        "Lula 1º": tab["t1_lula"], "Lula 2º": tab["t2_lula"], "Var. Lula": tab["ganho_lula"],
        "Flávio 1º": tab["t1_flavio"], "Flávio 2º": tab["t2_flavio"], "Var. Flávio": tab["ganho_flavio"],
    })

    def cor_var(v):
        return f"color: {PERDA}; font-weight: 600" if v < 0 else ""

    def cor_venc(v):
        return f"color: {LULA if v == 'Lula' else FLAVIO}; font-weight: 600"

    estilo = (
        exib.style.format({"Lula %": lambda x: f"{x:.1f}%".replace(".", ","),
                           **{c: fint for c in ["Diferença", "Lula 1º", "Lula 2º", "Flávio 1º", "Flávio 2º"]},
                           "Var. Lula": fsig, "Var. Flávio": fsig})
        .map(cor_var, subset=["Var. Lula", "Var. Flávio"])
        .map(cor_venc, subset=["Vencedor"])
    )
    st.dataframe(estilo, hide_index=True, width="stretch", height=560)
    st.download_button("Baixar tabela (CSV)", tab.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       "resultado_por_estado_2026.csv", "text/csv")

    st.subheader("Vantagem de Lula sobre Flávio, 1º → 2º turno")
    d = filtrar(estados).sort_values("margem_t2")
    figd = go.Figure()
    for _, r in d.iterrows():
        figd.add_trace(go.Scatter(x=[r.margem_t1 * 100, r.margem_t2 * 100], y=[r.estado] * 2, mode="lines",
                                  line=dict(color="#c4c8cf", width=2), showlegend=False, hoverinfo="skip"))
    figd.add_trace(go.Scatter(x=d["margem_t1"] * 100, y=d["estado"], mode="markers", name="1º turno",
                              marker=dict(color="white", size=9, line=dict(color="#9aa0a8", width=2)),
                              hovertemplate="%{y}: %{x:+.1f} pp no 1º turno<extra></extra>"))
    figd.add_trace(go.Scatter(x=d["margem_t2"] * 100, y=d["estado"], mode="markers", name="2º turno",
                              marker=dict(color=np.where(d["margem_t2"] > 0, LULA, FLAVIO), size=11),
                              hovertemplate="%{y}: %{x:+.1f} pp no 2º turno<extra></extra>"))
    figd.add_vline(x=0, line_color="#9aa0a8")
    figd.update_layout(height=max(360, 24 * len(d) + 80), margin=dict(l=0, r=10, t=10, b=10),
                       xaxis_title="pontos percentuais (+ Lula / − Flávio)", legend=dict(orientation="h", y=1.05),
                       plot_bgcolor="rgba(0,0,0,0)")
    figd.update_xaxes(gridcolor="#eceef1", zeroline=False)
    st.plotly_chart(figd, width="stretch", config=CFG_GRAFICO)

# ---------- Projeção ----------
with aba_proj:
    st.subheader("Projeção do 2º turno a partir do 1º turno")
    st.caption("Cada estado é projetado só com o próprio 1º turno e o padrão de transferência de votos dos outros estados.")
    nome_cen = st.radio("Modelo", ["Transferência de votos", "Base simples (proporção do 1º turno)"], horizontal=True)
    cen = "modelo" if nome_cen.startswith("Transferência") else "ingenuo"
    p1, p2, p3 = st.columns(3)
    p1.metric("Erro médio por estado", f"{prec.loc[cen, 'mae'] * 100:.1f} pp".replace(".", ","))
    p2.metric("Vencedor acertado", f"{int(prec.loc[cen, 'acertos'])} de {int(prec.loc[cen, 'total'])}")
    p3.metric("Votos dos demais candidatos que foram para Lula", fpct(transf["transf_outros_lula"], 0))

    pr = filtrar(proj[proj["cenario"] == cen])
    g1, g2 = st.columns([1, 1])
    with g1:
        lo = min(pr["proj_lula_pct"].min(), pr["real_lula_pct"].min()) * 100 - 2
        hi = max(pr["proj_lula_pct"].max(), pr["real_lula_pct"].max()) * 100 + 2
        cor = np.where(pr["acertou"] == "Errou", PERDA, np.where(pr["real_lula_pct"] > 0.5, LULA, FLAVIO))
        figs = go.Figure(go.Scatter(
            x=pr["proj_lula_pct"] * 100, y=pr["real_lula_pct"] * 100, mode="markers+text", text=pr["uf"],
            textposition="top center", textfont=dict(size=9, color="#6b7280"),
            marker=dict(color=cor, size=10, line=dict(color="white", width=1)),
            customdata=pr[["estado"]], hovertemplate="%{customdata[0]}<br>Projetado: %{x:.2f}%<br>Apurado: %{y:.2f}%<extra></extra>",
        ))
        figs.add_shape(type="line", x0=lo, y0=lo, x1=hi, y1=hi, line=dict(color="#9aa0a8", dash="dot"))
        figs.update_layout(height=460, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="rgba(0,0,0,0)",
                           xaxis_title="Lula projetado (%)", yaxis_title="Lula apurado (%)")
        figs.update_xaxes(range=[lo, hi], gridcolor="#eceef1")
        figs.update_yaxes(range=[lo, hi], gridcolor="#eceef1")
        st.plotly_chart(figs, width="stretch", config=CFG_GRAFICO)
        st.caption("Sobre a diagonal, a projeção acertou em cheio. Laranja: errou o vencedor.")
    with g2:
        tp = pr.sort_values("proj_lula", ascending=False)
        st.dataframe(
            pd.DataFrame({
                "Estado": tp["estado"], "Lula proj.": tp["proj_lula"].map(fint), "Flávio proj.": tp["proj_flavio"].map(fint),
                "Proj. %": tp["proj_lula_pct"].map(fpct), "Real %": tp["real_lula_pct"].map(fpct), "Erro": tp["erro_pp"].map(fpp),
            }),
            hide_index=True, width="stretch", height=460,
        )

# ---------- Metodologia ----------
with aba_metodo:
    st.subheader("Metodologia")
    st.markdown(
        """
**Fonte dos dados.** Votos por estado e exterior vêm da totalização oficial do Tribunal Superior Eleitoral
(resultados.tse.jus.br), com 100% das seções apuradas no 1º turno (4/out/2026) e no 2º turno (25/out/2026).
Os contornos dos estados vêm da malha territorial do IBGE. Percentuais são sobre os votos válidos.

**Votos ganhos entre os turnos.** Votos no 2º turno menos votos no 1º turno, por candidato e estado.
Um valor negativo indica que o candidato recebeu menos votos no 2º turno naquele estado.

**Modelo de transferência de votos.** Para cada estado, estimamos nas outras unidades uma regressão sem intercepto:
votos ganhos por Lula = a × votos dos demais candidatos no 1º turno + b × variação de votos válidos.
O restante vai para Flávio. Os válidos do 2º turno são projetados com a variação média das outras unidades,
de modo que o estado nunca entra no próprio cálculo.

**Base simples.** Mantém no 2º turno a proporção entre Lula e Flávio do 1º turno.

**Limitações.** A projeção foi feita depois da eleição: mostra quanto o 1º turno já explicava o 2º,
e não é uma previsão feita antes da votação.

**Reprodutibilidade.** Todo o cálculo está em `calculos.py`, e `baixar_dados.py` baixa novamente os dados do TSE e do IBGE.
        """
    )
    st.download_button("Baixar dados oficiais por UF (JSON)", calc.ARQ_RESULTADOS.read_bytes(),
                       "presidente_2026_por_uf.json", "application/json")

st.markdown(f'<div class="rodape">{CREDITOS} · Dados: TSE (resultados oficiais) e IBGE (malha territorial)</div>',
            unsafe_allow_html=True)
