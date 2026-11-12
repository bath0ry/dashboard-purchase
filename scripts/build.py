"""Gera index.html (GitHub/standalone) e dist/artifact.html (página publicada no Claude) a partir de data/projetos.json."""
import json, pathlib, re, base64
root = pathlib.Path(__file__).resolve().parent.parent
data = json.loads((root/"data/projetos.json").read_text(encoding="utf-8"))
for p in data["projetos"]: p.setdefault("naoPreco", [])
html = (root/"src/template.html").read_text(encoding="utf-8")
lp = root/"assets/logo-white.png"
logo = ("data:image/png;base64," + base64.b64encode(lp.read_bytes()).decode()) if lp.exists() else (root/"assets/logo-white.b64").read_text().strip()
payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
full = html.replace("/*__LOGO__*/", logo).replace("/*__DATA__*/", payload)
# no GitHub o logo vem de assets/ (arquivo menor); no Artifact vai embutido
(root/"index.html").write_text(html.replace("/*__LOGO__*/", "assets/logo-white.png").replace("/*__DATA__*/", payload), encoding="utf-8")
frag = re.sub(r"<!DOCTYPE html>\s*<html[^>]*>\s*<head>\s*<meta charset=\"UTF-8\">\s*<meta name=\"viewport\"[^>]*>\s*", "", full)
frag = frag.replace("</head>\n<body>", "").replace("</body>\n</html>", "")
(root/"dist").mkdir(exist_ok=True); (root/"dist/artifact.html").write_text(frag, encoding="utf-8")
print("ok:", len(data["projetos"]), "projetos")
