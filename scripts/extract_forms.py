"""Monta data/projetos.json a partir dos formulários de handover do Teamwork.

Fonte principal: Sales Support (414644) › "Handover - Delivery" (1638997) — um formulário por projeto fechado.
Complemento:     Sales Support (414644) › "Purchase - Ganho" (1639147) — mesmo formulário, enviado ao Purchase.
Corte: tasks criadas a partir de 2026-07-01.

Uso: python3 scripts/extract_forms.py handover.json ganho.json [data/projetos.json] [fob.json]
  handover.json / ganho.json = saída de twprojects-list_tasks (fields id,name,createdAt,status,description)
  data/projetos.json existente (opcional) = preserva FOB/PI/não-preço/segmento já levantados
  fob.json (opcional) = {task_id: {"valorMercadoriaUSD":..., "incoterm":..., "piUSD":..., "fornecedores":[...], "simFile":..., "seg":..., "tipo":...}}
"""
import json, re, sys, datetime, unicodedata, zoneinfo, pathlib

CORTE = "2026-07-01"
TW = "https://project.chinalinktrading.com/app/tasks/"

def campo(desc, rotulo):
    m = re.search(r'^\s*' + re.escape(rotulo) + r'[ \t]*([^\n]*)', desc, re.M)
    return (m.group(1).strip().rstrip('\\').strip() if m else "")

def num_usd(txt):
    """'$2,030.00' '320,00 USD' '$13.110' 'USD 3.410' '280 DOL' -> float; '1%' -> None"""
    if not txt or "%" in txt: return None
    s = re.sub(r'[^\d.,]', '', txt)
    if not s: return None
    if "," in s and "." in s:
        dec = "," if s.rfind(",") > s.rfind(".") else "."
        s = s.replace("." if dec == "," else ",", "").replace(dec, ".")
    elif "," in s or "." in s:
        sep = "," if "," in s else "."
        tail = s.split(sep)[-1]
        s = s.replace(sep, "") if len(tail) == 3 else s.replace(sep, ".")
    try: return float(s)
    except ValueError: return None

def pct(txt):
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*%', txt or "")
    return float(m.group(1).replace(",", ".")) if m else None

def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()
    return re.sub(r'[^A-Z0-9]', '', s)

SEG = [  # palavra-chave no nome do cliente -> segmento (palpite inicial; o FOB/arquivo pode corrigir)
    (r'ACADEMIA|FITNESS|GYM|FIT\b|WELLNESS|CONDICIONAMENTO|ESPORT|PILATES|CROSS', "Fitness / Academia"),
    (r'MOTO|AUTO ?PE|AUTOMOT|PECAS|DIESEL|VEICUL|SELANTE|ROLAMENT|CORREIA', "Autopeças / Motos"),
    (r'CONSTRU|FERRAG|PARAFUS|MATERIA(L|IS) DE CONSTR|VIDRO|ALUMIN|FORRO|ANDAIM|INCORPORA|IMOBILI', "Construção / Ferragens"),
    (r'ELETR|ENERGIA|SOLAR|LED|BATERIA|LUMEN|ILUMIN', "Elétrico / Energia"),
    (r'AGRO|AGRIC|RURAL|HORTI|IMPLEMENTO', "Agro"),
    (r'FARMA|MED|VET|ODONTO|SAUDE|CLINIC|BIOTEC|ANIMAL', "Saúde / Veterinária"),
    (r'MOVEI|HOME|CASA|DECOR|ENXOVA|UTILIDADE|PRESENTE', "Casa / Móveis"),
    (r'TEXTIL|CONFEC|CAMISET|BORDAD|MODA|ROUPA', "Têxtil / Vestuário"),
    (r'ALIMENT|GOURMET|AGUA|SUPERMERC|DOCE', "Alimentos"),
    (r'ECOMMERCE|E-COMMERCE|VAREJ|ATACAD|COMERCIO|DISTRIBUI|IMPORT|STORE|SHOP|LOJA|MAGAZINE', "Varejo / Atacado"),
    (r'MAQUIN|METALURG|INDUSTR|EQUIPAMENTO|ASSISTENCIA TECNICA|CONTAINER', "Máquinas / Indústria"),
]
ALIAS = [  # nome do "Sourcing responsável" no formulário -> nome padronizado
    (r'^victor( augusto)?( silva)?$', "Victor Augusto"), (r'^arthur leite|^arthur l\.?$', "Arthur Leite"),
    (r'^arthur lima', "Arthur Lima"), (r'^al+an( castellano)?$', "Alan Castellano"),
    (r'^jonathan', "Jonathan Corrêa"), (r'^nat[aá]lia', "Natália"), (r'^rha[ií]ssa', "Rhaissa Max"),
    (r'^paulo', "Paulo Cesar"), (r'^isabel+e', "Isabelle Barroso"), (r'^mis+a(e|i)l', "Misaell Lopes"),
    (r'fornecedor|supplier|^eu$|^nenhum', "Fornecedor do cliente"), (r'^camily', "Camily"), (r'^cliente', "Fornecedor do cliente"), (r'^vit[oó]ria', "Vitória"),
]
def comprador(txt):
    t = re.sub(r'[*_]', '', txt or "").strip(" .").strip()
    for rx, nome in ALIAS:
        if re.search(rx, t, re.I): return nome
    return t.title() or "—"

def segmento(nome):
    n = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().upper()
    for rx, seg in SEG:
        if re.search(rx, n): return seg
    return "A classificar"

def parse(t, origem):
    d = t.get("description") or ""
    nome = t["name"].strip()
    m = re.match(r'(.*?)\s*\(([^()]*)\)\s*$', nome)
    cliente, comercial = (m.group(1).strip(), m.group(2).strip()) if m else (nome, "")
    comercial = " ".join(w if len(w) <= 3 and w.islower() else w.capitalize() for w in comercial.lower().split())
    tem_ganho = campo(d, "Tem ganho?").lower().startswith("s")
    gtxt = campo(d, "Se tiver ganho, quanto?")
    if gtxt.lower().startswith(("auditoria", "\\", "não", "nao")): gtxt = ""
    invoices = [campo(d, f"Link da Invoice do fornecedor {i}:") for i in range(1, 6)]
    off = campo(d, "Se tiver off, quanto?")
    return dict(
        id=t["id"], link=TW + str(t["id"]), origem=origem,
        task=nome, cliente=cliente, comercial=comercial,
        data=t["createdAt"][:10], mes=t["createdAt"][:7], concluida=t.get("status") == "completed",
        pedido=campo(d, "Número do pedido:"), qtdFornecedores=(lambda q: q if q.isdigit() and q != "0" else "")(campo(d, "Quantidade de fornecedores:")),
        operacao=campo(d, "Qual o tipo de operação?"), comp=comprador(campo(d, "Sourcing responsável:")),
        temGanho=tem_ganho, ganhoTexto=gtxt, ganhoInformado=num_usd(gtxt) if tem_ganho else None,
        ganhoPct=pct(gtxt) if tem_ganho else None,
        temOff=campo(d, "Tem off?").lower().startswith("s"), off=off if not off.lower().startswith(("tem perso", "\\")) else "",
        certificacao=campo(d, "Se tiver certificação, qual?") if campo(d, "Tem certificação?").lower().startswith("s") else "",
        chinaMember=campo(d, "Se tiver, qual o nível?") if campo(d, "Tem China Member?").lower().startswith("s") else "",
        beneficio=campo(d, "Se tiver, qual benefício?") if campo(d, "Tem benefício fiscal?").lower().startswith("s") else "",
        temSimLink=campo(d, "Link da planilha de simulação:").startswith("http"), nInvoices=sum(x.startswith("http") for x in invoices),
    )

def main():
    hand = json.load(open(sys.argv[1]))["tasks"]
    ganho = json.load(open(sys.argv[2]))["tasks"] if len(sys.argv) > 2 else []
    out_path = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else pathlib.Path("data/projetos.json")
    fob = json.load(open(sys.argv[4])) if len(sys.argv) > 4 else {}
    antigo = {}
    if out_path.exists():
        try: antigo = {str(p["id"]): p for p in json.load(open(out_path))["projetos"]}
        except Exception: antigo = {}

    projetos = {}
    for t in hand:
        if t["createdAt"][:10] >= CORTE:
            p = parse(t, "Handover - Delivery"); projetos[(norm(p["cliente"]), p["pedido"])] = p
    def achar(g):  # mesmo cliente com o mesmo nº de pedido, ou criado com até 10 dias de diferença
        alvo = norm(g["cliente"]); gd = datetime.date.fromisoformat(g["data"])
        cands = [k for k in projetos if k[0] == alvo]
        for k in cands:
            if k[1] == g["pedido"]: return k
        for k in cands:
            if abs((datetime.date.fromisoformat(projetos[k]["data"]) - gd).days) <= 10: return k
    for t in ganho:  # o formulário enviado ao Purchase prevalece no ganho
        if t["createdAt"][:10] < CORTE: continue
        g = parse(t, "Purchase - Ganho"); k = achar(g)
        if k:
            p = projetos[k]; p["purchaseTask"] = g["link"]
            if g["temGanho"]:
                for f in ("temGanho", "ganhoTexto", "ganhoInformado", "ganhoPct"): p[f] = g[f]
            if p["comp"] in ("—", "Fornecedor do cliente") and g["comp"] != "—": p["comp"] = g["comp"]
        else:
            projetos[(norm(g["cliente"]), g["pedido"])] = g

    lista = []
    for p in projetos.values():
        ext = {**antigo.get(str(p["id"]), {}), **fob.get(str(p["id"]), {})}
        if ext.get("simUSD") and not ext.get("valorMercadoriaUSD"): ext["valorMercadoriaUSD"] = ext["simUSD"]  # formato antigo
        for f in ("valorMercadoriaUSD", "incoterm", "piUSD", "fornecedores", "simFile", "simTentado", "nota"):
            if f in ext and ext[f] not in (None, "", []): p[f] = ext[f]
        p.pop("simUSD", None); p.pop("naoPreco", None)
        p.setdefault("fornecedores", []); p.setdefault("nota", "")
        p["seg"] = ext.get("seg") or segmento(p["cliente"])
        p["tipo"] = ext.get("tipo") or "—"
        # ganho: valor informado no formulário; se só veio %, converte com o FOB; se não informado, usa simulação − PI
        g = p["ganhoInformado"]
        if g is None and p["ganhoPct"] and p.get("valorMercadoriaUSD"): g = round(p["valorMercadoriaUSD"] * p["ganhoPct"] / 100, 2)
        if g is None and p["temGanho"] and p.get("valorMercadoriaUSD") and p.get("piUSD"): g = round(p["valorMercadoriaUSD"] - p["piUSD"], 2)
        p["ganho"] = g if p["temGanho"] else 0.0
        if p["temGanho"] and g is None:
            p["status"] = "ganho_sem_valor"; p["nota"] = p["nota"] or f"Ganho informado como '{p['ganhoTexto'] or 'Sim'}' sem valor em USD"
        else:
            p["status"] = "ganho" if p["temGanho"] and (p["ganho"] or 0) > 0 else "sem"
        p["revisar"] = p["status"] == "ganho_sem_valor" or bool(p.get("valorMercadoriaUSD") and p["ganho"] and p["ganho"] / p["valorMercadoriaUSD"] > 0.35)
        lista.append(p)
    import collections  # unifica grafias do mesmo nome (com/sem acento)
    for campo_nome in ("comercial", "comp"):
        grupos = collections.defaultdict(collections.Counter)
        for p in lista: grupos[norm(p[campo_nome])][p[campo_nome]] += 1
        for p in lista:
            variantes = grupos[norm(p[campo_nome])]
            p[campo_nome] = max(variantes, key=lambda v: (sum(c > "~" for c in v), variantes[v]))
    lista.sort(key=lambda x: (x["data"], x["id"]), reverse=True)
    agora = datetime.datetime.now(zoneinfo.ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(dict(atualizado=agora, desde=CORTE,
                   fonte="Teamwork · Sales Support › Handover - Delivery + Purchase - Ganho",
                   projetos=lista), open(out_path, "w"), ensure_ascii=False, indent=1)
    com = [p for p in lista if p["status"] == "ganho"]
    print(f"{len(lista)} projetos | com ganho {len(com)} | US$ {sum(p['ganho'] for p in com):,.2f} | sem valor {sum(p['status']=='ganho_sem_valor' for p in lista)}")

if __name__ == "__main__":
    main()
