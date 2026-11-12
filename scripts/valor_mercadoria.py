"""Lê da planilha de simulação o valor da mercadoria em USD fechado com o cliente.

O valor vem da coluna "VALOR MERCADORIA (DÓLAR)" (soma dos itens = QTD × PREÇO UNITÁRIO U$),
na aba do cenário fechado. Vale para qualquer incoterm (FOB, EXW...): não depende do rótulo "VALOR FOB".

Aba por tipo de operação do formulário de handover:
  Direto -> CONVENCIONAL | Conta e Ordem -> Conta e Ordem | Compra e Venda -> Compra e Venda
Uso: python3 scripts/valor_mercadoria.py planilha.xlsx [operacao]
"""
import sys, re, json, openpyxl

ABA = {"direto": "CONVENCIONAL", "conta e ordem": "Conta e Ordem", "compra e venda": "Compra e Venda"}

def escolher_aba(wb, operacao):
    alvo = ABA.get((operacao or "").strip().lower(), "CONVENCIONAL")
    nomes = {n.strip().lower(): n for n in wb.sheetnames}
    if alvo.lower() in nomes: return nomes[alvo.lower()]
    for n in wb.sheetnames:
        if re.search(r'CONVENCIONAL|COMPRA|CONTA', n, re.I): return n
    return wb.sheetnames[0]

def ler(path, operacao=""):
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    aba = escolher_aba(wb, operacao); ws = wb[aba]
    rows = list(ws.iter_rows(min_row=1, max_row=1500, max_col=40, values_only=True))
    out = {"aba": aba, "incoterm": None, "cliente": None, "valorMercadoriaUSD": None, "fonte": None}
    for r in rows[:20]:
        for i, v in enumerate(r[:-1]):
            if isinstance(v, str):
                t = v.strip().upper()
                if t == "INCOTERM" and r[i + 1]: out["incoterm"] = str(r[i + 1]).strip()
                if t == "CLIENTE" and r[i + 1]: out["cliente"] = str(r[i + 1]).strip()
                if t.startswith("VALOR FOB") and isinstance(r[i + 1], (int, float)): out["_a10"] = float(r[i + 1])
    # cabeçalho "VALOR MERCADORIA (DÓLAR)" -> soma dos itens abaixo
    for ri, r in enumerate(rows):
        for ci, v in enumerate(r):
            if isinstance(v, str) and re.match(r'\s*VALOR MERCADORIA \(D[ÓO]LAR\)', v, re.I):
                total, vazios = 0.0, 0
                for r2 in rows[ri + 1:]:
                    x = r2[ci] if ci < len(r2) else None
                    item = r2[0] if r2 else None  # só linhas de item (coluna ITEM numérica); ignora a linha de total
                    if isinstance(x, (int, float)) and isinstance(item, (int, float)): total += x; vazios = 0
                    else:
                        vazios += 1
                        if vazios > 30: break
                if total > 0:
                    out["valorMercadoriaUSD"] = round(total, 2); out["fonte"] = f"{aba}: soma de VALOR MERCADORIA (DÓLAR)"
                break
        if out["valorMercadoriaUSD"]: break
    if not out["valorMercadoriaUSD"] and out.get("_a10"):
        out["valorMercadoriaUSD"] = out["_a10"]; out["fonte"] = f"{aba}: célula VALOR FOB (total da mercadoria)"
    out.pop("_a10", None)
    return out

if __name__ == "__main__":
    print(json.dumps(ler(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ""), ensure_ascii=False))
