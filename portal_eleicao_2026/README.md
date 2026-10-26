# Eleição Presidencial 2026 — Portal de transparência

Portal aberto com os resultados oficiais da eleição presidencial de 2026 por estado,
no 1º e no 2º turno: vencedor e vantagem em cada estado, votos ganhos e perdidos por
candidato entre os turnos, mapas e uma projeção do 2º turno a partir do 1º.

**Desenvolvido por João Pedro Silva de Morais e Marcos Vinicius Ananias Silva.**

## O que tem no portal

- **Visão geral:** totais do Brasil, mapa de quem venceu em cada estado e dois mapas
  (Lula em vermelho, Flávio em azul) com os votos que cada um ganhou do 1º para o 2º turno.
- **Estados:** tabela ordenável com vencedor, diferença de votos e variação de cada
  candidato, com download em CSV, e gráfico da vantagem nos dois turnos.
- **Projeção:** projeção do 2º turno de cada estado usando só o 1º turno, comparada
  com o resultado real.
- **Metodologia:** fontes, fórmulas e limitações.

## Fontes

- Tribunal Superior Eleitoral: resultados oficiais em `resultados.tse.jus.br` (100% das seções).
- IBGE: malha territorial dos estados (`servicodados.ibge.gov.br`).

## Como rodar no computador

Requer Python 3.11 ou mais novo.

```bash
python -m venv .venv
.venv\Scripts\activate          # no Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

O portal abre em `http://localhost:8501`.

No Windows, se aparecer o erro `DLL load failed while importing lib` (pyarrow), a pasta
do projeto está num caminho longo demais. Mova o projeto para um caminho curto, como
`C:\projetos\portal_eleicao_2026`.

## Como atualizar os dados

```bash
python baixar_dados.py
```

O script baixa de novo os resultados do TSE e a malha do IBGE para a pasta `data/`.
Para conferir os números sem abrir o portal: `python calculos.py`.

## Como publicar na internet

O jeito mais simples é o **Streamlit Community Cloud** (gratuito):

1. Suba esta pasta para um repositório público no GitHub.
2. Entre em https://share.streamlit.io com a conta do GitHub.
3. Clique em *Create app*, escolha o repositório e o arquivo `app.py`.

Também funciona em qualquer servidor com Python (Render, Railway, Azure, uma VM própria)
com o comando `streamlit run app.py --server.port 80`.

## Arquivos

| Arquivo | Para que serve |
|---|---|
| `app.py` | O portal (telas, mapas, tabelas) |
| `calculos.py` | Todos os cálculos: indicadores, totais, projeção |
| `baixar_dados.py` | Baixa os dados oficiais do TSE e do IBGE |
| `data/presidente_2026_por_uf.json` | Votos por estado nos dois turnos |
| `data/br_uf.geojson` | Contornos dos estados |

## Método da projeção

Para cada estado, ajustamos nas outras unidades uma regressão sem intercepto:
votos ganhos por Lula = a × votos dos demais candidatos no 1º turno + b × variação de votos válidos.
O restante vai para Flávio. O estado projetado nunca entra no próprio cálculo.
Resultado: erro médio de 1,0 ponto percentual por estado e vencedor correto em 27 de 28 unidades.
A projeção foi feita depois da eleição e não é uma previsão feita antes da votação.
