# Dashboard de Ganhos · Purchase (China Link)

Dashboard de KPIs do time de Purchase (identidade visual China Link): resultado financeiro por projeto fechado (simulação × PI final), por segmento, tipo de produto, comprador e mês. Atualizado 1x por dia.

## KPIs — 1. Resultado financeiro
| KPI | Cálculo | Meta inicial |
|---|---|---|
| Saving total (USD) | Σ (FOB simulado − PI final) dos projetos com ganho | baseline após o piloto |
| Saving % | Saving total ÷ Σ valor da mercadoria (USD) fechado com o cliente | 3–5% |
| Taxa de ganho | Projetos com ganho ÷ projetos fechados | ≥ 60% |
| Ganho médio por projeto | Saving total ÷ projetos fechados | tendência mensal |

## Regra de cálculo
- **Valor inicial**: `VALOR FOB` (USD) da simulação de fechamento anexada na task (aba `CONVENCIONAL`, célula B10).
- **Valor final**: soma das PIs finais anexadas na task (última versão de cada fornecedor).
- **Ganho** = inicial − final. Se a PI está no SharePoint/RMB e o comprador escreveu o ganho no comentário, usa o valor do comentário.
- **⚠ Revisar**: PI acima da simulação, ganho > 35% ou PI parcial.

Fonte: Teamwork › **Sales Support** › listas **Handover - Delivery** (um formulário por projeto fechado) e **Purchase - Ganho**, a partir de 01/07/2026. Valor da mercadoria (USD) lido da planilha de simulação anexada na task de handover: soma da coluna "VALOR MERCADORIA (DÓLAR)" na aba do cenário fechado (Direto → CONVENCIONAL, Conta e Ordem, Compra e Venda), em qualquer incoterm.

## Estrutura
```
index.html                 dashboard pronto (arquivo único, abre no navegador / GitHub Pages)
data/projetos.json         dados extraídos do Teamwork
src/template.html          front-end (HTML/CSS/JS puro, sem dependências)
scripts/extract_forms.py   lê os formulários de handover -> data/projetos.json
scripts/valor_mercadoria.py lê o valor da mercadoria em USD da simulação
scripts/build.py           injeta o JSON no template -> index.html e dist/artifact.html
scripts/sim_fob.py         lê o VALOR FOB das simulações (.xlsx)
scripts/pi_total.py        acha o TOTAL das PIs (.xlsx/.xls); PDFs via `pdftotext -layout`
assets/logo-white.png      logo (manual de marca 2026)
```

## Atualizar
```bash
# atualize data/projetos.json (rotina diária) e gere o index:
python3 scripts/build.py
```
A rotina diária (Claude, tarefa agendada) lê o Teamwork, atualiza `data/projetos.json` e republica o dashboard.

## Próximos passos
- Campos personalizados na task: Segmento e Tipo de produto
- Integração SharePoint (PIs salvas lá não são lidas hoje)
