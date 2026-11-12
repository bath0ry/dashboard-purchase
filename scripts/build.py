"""Gera index.html (GitHub/standalone) e dist/artifact.html (página publicada no Claude) a partir de data/projetos.json."""
import json, pathlib, re
root = pathlib.Path(__file__).resolve().parent.parent
data = json.loads((root/"data/projetos.json").read_text(encoding="utf-8"))
html = (root/"src/template.html").read_text(encoding="utf-8")
payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
full = html.replace("/*__DATA__*/", payload)
(root/"index.html").write_text(full, encoding="utf-8")
frag = re.sub(r"<!DOCTYPE html>\s*<html[^>]*>\s*<head>\s*<meta charset=\"UTF-8\">\s*<meta name=\"viewport\"[^>]*>\s*", "", full)
frag = frag.replace("</head>\n<body>", "").replace("</body>\n</html>", "")
(root/"dist").mkdir(exist_ok=True); (root/"dist/artifact.html").write_text(frag, encoding="utf-8")
print("ok:", len(data["projetos"]), "projetos")
