"""Também aplica as "outras negociações" (naoPreco) de ganhos_comentarios.json em todos os projetos.

Projetos com ganho registrado só na SOURCING TASK › Purchase/Projeto Fechado (ainda sem Handover - Delivery).

Regra do usuário (26/11/2026): o ganho fechado na sourcing task conta no painel no dia em que é registrado,
mesmo antes de o comercial abrir o Handover - Delivery.

Uso (sempre DEPOIS do extract_forms.py, inclusive do --reaplicar):
    python3 scripts/sourcing_extra.py data/projetos.json data/sourcing_extra.json data/ganhos_comentarios.json

data/sourcing_extra.json = {"<id da sourcing task>": {projeto completo no formato do painel, origem "SOURCING TASK"}}
- Se já existe no painel um projeto do Handover - Delivery do mesmo cliente (nome normalizado) criado até 20 dias
  depois / 5 antes do ganho, o ganho passa para ganhos_comentarios.json (chave = id do handover) e a entrada é
  removida do sourcing_extra.json (vira projeto normal; rode o --reaplicar de novo).
- Senão, o projeto entra no painel com origem "SOURCING TASK (sem handover)".
"""
import json, sys, re, unicodedata, datetime

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().upper()
    s = re.sub(r'\b(LTDA|ME|EIRELI|EPP|S\.?A\.?|COMERCIO|E|DE|DA|DO|SERVICOS)\b', ' ', s)
    return re.sub(r'[^A-Z0-9]', '', s)

def main(proj_path, extra_path, coment_path):
    d = json.load(open(proj_path)); extra = json.load(open(extra_path)); coment = json.load(open(coment_path))
    projs = [p for p in d["projetos"] if p.get("origem") != "SOURCING TASK (sem handover)"]
    mudou_coment = False
    for sid, e in list(extra.items()):
        ed = datetime.date.fromisoformat(e["data"]); alvo = norm(e["cliente"])[:12]
        achou = None
        for p in projs:
            if p.get("origem") != "Handover - Delivery" or not alvo or alvo not in norm(p["cliente"]): continue
            dd = (datetime.date.fromisoformat(p["data"]) - ed).days
            if -5 <= dd <= 20: achou = p; break
        if achou:
            k = str(achou["id"])
            if k not in coment:
                coment[k] = {"temGanho": True, "ganhoUSD": e["ganho"], "fonte": e["ganhoFonte"],
                             **{f: e["ganhoComentario"][f] for f in ("autor", "data", "texto", "link")},
                             "historico": e.get("historicoGanho", []), "nota": e.get("nota", ""),
                             "naoPreco": e.get("naoPreco", [])}
                mudou_coment = True
            del extra[sid]
            print(f"{e['cliente']}: handover {k} encontrado, ganho movido para ganhos_comentarios.json")
        else:
            projs.append(e)
    # outras negociações (não numéricas): termo de pagamento, peças/amostras grátis, frete, prazo etc.
    # ficam em ganhos_comentarios.json["<id handover>"]["naoPreco"] = [{tipo, descricao, autor, data, link}]
    for p in projs:
        c = coment.get(str(p["id"])) or {}
        p["naoPreco"] = c.get("naoPreco") or p.get("naoPreco") or []
    projs.sort(key=lambda x: (x["data"], x["id"]), reverse=True)
    d["projetos"] = projs
    json.dump(d, open(proj_path, "w"), ensure_ascii=False, indent=1)
    json.dump(extra, open(extra_path, "w"), ensure_ascii=False, indent=1)
    if mudou_coment:
        json.dump(coment, open(coment_path, "w"), ensure_ascii=False, indent=1)
        print("rode de novo: extract_forms.py --reaplicar e depois este script")
    print(f"{len(extra)} projeto(s) só da sourcing task no painel")

if __name__ == "__main__":
    main(*sys.argv[1:4])
