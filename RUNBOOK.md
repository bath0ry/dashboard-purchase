# Rotina diária — KPIs de Purchase (China Link)

- Artifact: https://claude.ai/artifact/BB3fXKdgHa4MNVV6HwiQmW (republicar com `url` = este link)
- GitHub: https://github.com/bath0ry/dashboard-purchase (privado, branch `master`)
- Período: projetos com handover a partir de **2026-07-01** (sem data final).
- Identidade visual: manual de marca China Link 2026 (azul #001489, vermelho #E10600; títulos Anton/Brunson, corpo Montserrat).

## Arquivos no projeto Claude (claude/dashboard-purchase/)
RUNBOOK.md, projetos.json, fob.json, ganhos_comentarios.json, template.html, build.py, extract_forms.py, valor_mercadoria.py, logo-white.b64

Montar localmente:
```
dash/src/template.html  dash/scripts/build.py  dash/scripts/extract_forms.py  dash/scripts/valor_mercadoria.py
dash/data/projetos.json dash/data/fob.json dash/data/ganhos_comentarios.json dash/assets/logo-white.b64
```

## 1. Fonte dos dados (Teamwork, projeto Sales Support id 414644)
| Lista | id | Conteúdo |
|---|---|---|
| Handover - Delivery | 1638997 | **lista mestre**: 1 formulário por projeto fechado (cliente, comercial entre parênteses, nº pedido, qtd fornecedores, operação, "Tem ganho?", "Se tiver ganho, quanto?", off, certificação, China Member, benefício, "Sourcing responsável", links Wufoo da simulação/PIs) |
| Purchase - Ganho | 1639147 | mesmo formulário enviado ao Purchase; **prevalece no valor do ganho** |

Os links Wufoo (chinalinktrading.wufoo.com/cabinet/...) não abrem pela nuvem. A planilha de simulação costuma estar anexada nos **comentários da task de Handover** (arquivo "(CLT) PLANILHA CUSTOS…" ou "SIMULAÇÃO…").

## 2. Passos
1. `twprojects-list_tasks(tasklist_id=1638997, show_completed=true, created_after=2026-07-01, fields=[id,name,createdAt,status,description], page_size=500)` → salvar a resposta inteira como `handover.json`.
2. Idem para `tasklist_id=1639147` → `ganho.json`.
3. `python3 scripts/extract_forms.py handover.json ganho.json data/projetos.json data/fob.json data/ganhos_comentarios.json`
   (preserva valor da mercadoria, incoterm e notas já levantados; recalcula status e ganho).
4. **Backlog do valor da mercadoria** (até 15 projetos por dia, os mais recentes sem `valorMercadoriaUSD` e sem `simTentado`):
   - `twprojects-list_comments(task_id=<id>, updated_after=2026-06-01, fields=[id,body,postedDateTime,files])`
   - `twprojects-list_files(ids=[...])` para ver nome/tamanho; escolher o xlsx mais recente com "PLANILHA", "SIMULA", "CEN" ou "FECHAD" no nome e ≤ 10 MB.
   - `twprojects-download_file` → `python3 scripts/valor_mercadoria.py planilha.xlsx "<operacao do formulário>"`. O script escolhe a aba do cenário fechado (Direto → CONVENCIONAL, Conta e Ordem, Compra e Venda) e soma a coluna "VALOR MERCADORIA (DÓLAR)" (só linhas de item). Vale para FOB, EXW etc. — **não usar o rótulo "VALOR FOB" como conceito**, é o valor da mercadoria fechado com o cliente.
   - Gravar em `data/fob.json`: `{"<task_id>": {"valorMercadoriaUSD": 12345, "incoterm": "EXW", "simFile": <file_id>}}`. Se não achar/arquivo > 10 MB: `{"simTentado": "AAAA-MM-DD", "nota": "simulação > 10 MB"}`.
   - Rodar de novo o passo 3 com o fob.json atualizado.
4b. **Ganho e colchão nas conversas das tasks**. Fontes: task de Handover, task Purchase - Ganho, Purchase › Projetos Fechados, **SOURCING TASK (projeto 49784)** e o **projeto de importação do cliente** ("Importação - Pn - CLIENTE"), onde ficam as conversas depois do handover.
   - `twprojects-search(search_term="ganho", types=["taskcomments"], include_completed_items=true, updated_after=<última rodada − 2 dias>, limit=100, sideload=["comments"])` em TODOS os projetos (paginar com `cursor`). Ignorar ruído: "ganho CLT" de frete (Ressimulação de Embarque), "ganho de massa", descrições de produto.
   - Casar o comentário com o projeto do painel pelo nome do cliente (projeto "Importação - Pn - CLIENTE" ou task "Pn - CLIENTE") e ler a conversa inteira com `twprojects-list_comments(task_id=..., updated_after=2026-07-01)`; textos truncados → `twprojects-get_comment`.
   - Para cada `ganho_sem_valor`, buscar também `twprojects-search(search_term="<cliente>")` e ler as tasks de importação/sourcing encontradas.
   - **Regra**: o último valor dito na conversa prevalece. Guardar a linha do tempo em `historico`.
   - **Colchão**: se depois do ganho negociado parte ou todo o valor foi abatido/usado para cobrir um problema (fornecedor mudou preço, custo não previsto, comissão, frete, reembolso, "seguir sem ganho"...), gravar `colchao: {valor, motivo, autor, data, texto, link}` e `ganhoUSD` = o que sobrou. Ganho que AUMENTOU não é colchão (só histórico).
   - Gravar em `data/ganhos_comentarios.json`: `{"<id handover>": {"ganhoInicialUSD": 680, "ganhoUSD": 0, "autor","data","texto","link","nota", "historico":[{data,valor,autor,texto,link}], "colchao":{valor,motivo,autor,data,texto,link}}}` e rodar o passo 3 de novo.
   - As tasks de Purchase › Projetos Fechados costumam vir sem comentários pela API (acesso restrito); se vierem, aplicar a mesma regra.
5. `python3 scripts/build.py` → index.html e dist/artifact.html.
6. Publicar dist/artifact.html no Artifact (url acima). `project_write` de projetos.json e fob.json.

## 2b. Mudanças automáticas (sem pedir ao usuário)
- Virada de mês: o filtro de mês e o gráfico mensal são montados a partir das datas dos handovers; o mês novo aparece sozinho na primeira rodada após o dia 1º.
- Compradores, comerciais e segmentos novos: entram nos filtros e rankings automaticamente. Se surgir uma grafia nova de um nome já conhecido (ex.: "Rhaissa" × "Rhaissa Max"), incluir no ALIAS do extract_forms.py e gravar o script atualizado no projeto e no GitHub (scripts/).
- Qualquer correção de regra feita pelo usuário vale para as rodadas seguintes: atualizar o RUNBOOK e os scripts no projeto.

## 3. Regras de cálculo (feitas pelo extract_forms.py e pelo template)
- Saving total = Σ ganho em USD dos formulários com "Tem ganho? Sim". Valor em % → converte com o valor da mercadoria.
- "Sim" sem valor → status `ganho_sem_valor` (⚠ no painel).
- Saving % = saving ÷ Σ valor da mercadoria (USD), só nos projetos com valor lido (o card mostra a cobertura; "Em coleta" se < 50%).
- Saving não-preço: **fora do painel por enquanto** (decisão do usuário).
- Fonte do ganho, em ordem de prioridade: conversa da task (ganhos_comentarios.json) > formulário Purchase - Ganho > formulário de Handover.
- Saving total = ganho LÍQUIDO (negociado − colchão). Status `consumido` = ganho negociado todo usado como colchão.
- Taxa de ganho = projetos com ganho negociado ÷ projetos fechados (todos; fornecedor do cliente não tem tratamento especial no painel).
- Ganho médio = saving líquido ÷ projetos com ganho líquido > 0 (não divide pelos fechados).
- Off, certificação e fornecedor do cliente não aparecem como contagem no painel.
- Nomenclatura no painel: "Ganho abatido" (nunca "colchão"); status de ganho todo abatido = "Ganho abatido". O campo interno continua `colchao` no JSON.
- Comprador = "Sourcing responsável" (nomes padronizados no script).

## 4. Commit diário no GitHub (Claude in Chrome, usuário já logado como bath0ry)
1. `tabs_context_mcp(createIfEmpty=true)`; navegar para https://github.com/bath0ry/dashboard-purchase/upload/master/data
2. `javascript_tool`: montar os arquivos e anexar no input de upload:
   - Para não colar texto grande: no Python, `base64(gzip(json.dumps({"projetos.json":...,"fob.json":...})))`; no navegador
     `new Response(new Blob([Uint8Array.from(atob(B),c=>c.charCodeAt(0))]).stream().pipeThrough(new DecompressionStream('gzip'))).text()`
   - `const dt=new DataTransfer(); dt.items.add(new File([TEXTO],'projetos.json',{type:'application/json'})); … const i=document.querySelector('input[type=file]'); i.files=dt.files; i.dispatchEvent(new Event('change',{bubbles:true}));`
   - Esperar 3 s, conferir os nomes na página, preencher `#commit-summary-input` com "Atualização diária AAAA-MM-DD" e clicar em "Commit changes".
3. Commitar também o index.html (template + dados embutidos; logo via assets/logo-white.png) na raiz: https://github.com/bath0ry/dashboard-purchase/upload/master
4. Se o Chrome não responder: não insistir; avisar no resumo que o commit ficou pendente. Fechar a aba criada.

## 5. Resumo final (português, curto)
Projetos novos, saving total, taxa de ganho, valores de mercadoria lidos hoje / cobertura, ganhos sem valor, status do commit.
