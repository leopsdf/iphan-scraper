import pandas as pd
from datetime import datetime

CSV_FILE = "publicacoes_iphan_catalogo_v1_limpo.csv"

df = pd.read_csv(CSV_FILE)

total = len(df)

categorias = df["categoria"].value_counts()

autores = df["autor"].value_counts().head(20)

anos = df["edicao"].value_counts().sort_index()

data = datetime.now().strftime("%Y-%m-%d %H:%M")

txt = []
txt.append("RELATÓRIO AUTOMÁTICO – PUBLICAÇÕES IPHAN\n")
txt.append(f"Gerado em: {data}\n")
txt.append(f"Total de registros catalogados: {total}\n")

txt.append("\nPUBLICAÇÕES POR CATEGORIA\n")
txt.append(categorias.to_string())

txt.append("\n\nAUTORES MAIS FREQUENTES\n")
txt.append(autores.to_string())

txt.append("\n\nPUBLICAÇÕES POR ANO\n")
txt.append(anos.to_string())

with open("relatorio_publicacoes_iphan.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(txt))

html = f"""
<html>
<head>
<meta charset="utf-8">
<title>Relatório IPHAN</title>
<style>
body{{font-family:Arial;margin:40px}}
h1{{color:#333}}
table{{border-collapse:collapse}}
td,th{{border:1px solid #ccc;padding:6px}}
</style>
</head>
<body>

<h1>Relatório das Publicações do IPHAN</h1>

<p><b>Data do relatório:</b> {data}</p>
<p><b>Total de publicações catalogadas:</b> {total}</p>

<h2>Publicações por Categoria</h2>
{categorias.to_frame().to_html()}

<h2>Autores mais frequentes</h2>
{autores.to_frame().to_html()}

<h2>Publicações por Ano</h2>
{anos.to_frame().to_html()}

</body>
</html>
"""

with open("relatorio_publicacoes_iphan.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Relatórios gerados:")
print("relatorio_publicacoes_iphan.txt")
print("relatorio_publicacoes_iphan.html")
