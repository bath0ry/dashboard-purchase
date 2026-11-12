# Dashboard de Ganhos · Purchase (China Link)

Dashboard de KPIs do time de Purchase: ganho por projeto fechado (simulação × PI final), por segmento, tipo de produto, comprador e mês.

## Regra de cálculo
- **Valor inicial**: `VALOR FOB` (USD) da simulação de fechamento anexada na task (aba `CONVENCIONAL`, célula B10).
- **Valor final**: soma das PIs finais anexadas na task (última versão de cada fornecedor).
- **Ganho** = inicial − final. Se a PI está no SharePoint/RMB e o comprador escreveu o ganho no comentário, usa o valor do comentário.
- **⚠ Revisar**: PI acima da simulação, ganho > 35% ou PI parcial.

Fonte: Teamwork › projeto **Purchase** › lista **Projetos Fechados Purchase** (tasks nomeadas pelo cliente; anexos nos comentários).

## Estrutura
```
index.html                 dashboard pronto (arquivo único, abre no navegador / GitHub Pages)
data/projetos.json         dados extraídos do Teamwork
src/template.html          front-end (HTML/CSS/JS puro, sem dependências)
scripts/build.py           injeta o JSON no template -> index.html e dist/artifact.html
scripts/sim_fob.py         lê o VALOR FOB das simulações (.xlsx)
scripts/pi_total.py        acha o TOTAL das PIs (.xlsx/.xls); PDFs via `pdftotext -layout`
```

## Atualizar
```bash
# atualize data/projetos.json (rotina diária) e gere o index:
python3 scripts/build.py
```
A rotina diária (Claude, tarefa agendada) lê o Teamwork, atualiza `data/projetos.json` e republica o dashboard.

## Próximos passos
- Padronizar o comentário da PI: `Fornecedor X – Sim US$ … – PI US$ … – Ganho US$ …`
- Campos personalizados na task: Segmento e Tipo de produto
- Integração SharePoint (PIs salvas lá não são lidas hoje)
