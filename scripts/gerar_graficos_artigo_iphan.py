import os
import pandas as pd
import matplotlib.pyplot as plt

CATALOGO = "publicacoes_iphan_catalogo_v1_limpo.csv"
AUDITORIA = "auditoria_download_pdfs_v3.csv"
OUTDIR = "figuras_artigo"

os.makedirs(OUTDIR, exist_ok=True)

df_cat = pd.read_csv(CATALOGO)
df_aud = pd.read_csv(AUDITORIA)

# limpeza leve
for col in ["categoria", "autor", "edicao", "titulo"]:
    if col in df_cat.columns:
        df_cat[col] = df_cat[col].fillna("").astype(str).str.strip()

if "status" in df_aud.columns:
    df_aud["status"] = df_aud["status"].fillna("").astype(str).str.strip()

# -----------------------------
# 1. Top categorias
# -----------------------------
cat_counts = df_cat["categoria"].value_counts().head(10)

plt.figure(figsize=(10, 6))
cat_counts.sort_values().plot(kind="barh")
plt.xlabel("Quantidade de publicações")
plt.ylabel("Categoria")
plt.title("Top 10 categorias de publicações do IPHAN")
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "grafico_top_categorias.png"), dpi=300)
plt.close()

# -----------------------------
# 2. Status dos downloads
# -----------------------------
status_counts = df_aud["status"].value_counts()

plt.figure(figsize=(8, 5))
status_counts.plot(kind="bar")
plt.xlabel("Status")
plt.ylabel("Quantidade")
plt.title("Resultado da auditoria dos downloads")
plt.xticks(rotation=20, ha="right")
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "grafico_status_downloads.png"), dpi=300)
plt.close()

# -----------------------------
# 3. Top autores
# -----------------------------
autor_counts = df_cat["autor"].replace("", pd.NA).dropna().value_counts().head(10)

plt.figure(figsize=(10, 6))
autor_counts.sort_values().plot(kind="barh")
plt.xlabel("Quantidade de publicações")
plt.ylabel("Autor")
plt.title("Top 10 autores mais frequentes no catálogo")
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "grafico_top_autores.png"), dpi=300)
plt.close()

# -----------------------------
# 4. Publicações por ano
# -----------------------------
# tenta converter edição para ano numérico
anos = pd.to_numeric(df_cat["edicao"], errors="coerce").dropna().astype(int)
anos = anos[(anos >= 1800) & (anos <= 2100)]

if len(anos) > 0:
    ano_counts = anos.value_counts().sort_index()

    plt.figure(figsize=(10, 5))
    ano_counts.plot(kind="line", marker="o")
    plt.xlabel("Ano")
    plt.ylabel("Quantidade de publicações")
    plt.title("Distribuição das publicações por ano de edição")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, "grafico_publicacoes_por_ano.png"), dpi=300)
    plt.close()

# -----------------------------
# 5. Cobertura de PDFs únicos
# -----------------------------
total_catalogo = len(df_cat)
titulos_com_pdf = df_aud[df_aud["status"] == "baixado"]["titulo"].nunique()
sem_pdf = len(df_aud[df_aud["status"] == "sem_pdf_no_html"][["titulo"]].drop_duplicates())

dados_cobertura = pd.Series({
    "Com PDF baixado": titulos_com_pdf,
    "Sem PDF detectado": sem_pdf
})

plt.figure(figsize=(7, 5))
dados_cobertura.plot(kind="bar")
plt.xlabel("Situação")
plt.ylabel("Quantidade de títulos")
plt.title("Cobertura de PDFs no portal do IPHAN")
plt.xticks(rotation=15, ha="right")
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "grafico_cobertura_pdfs.png"), dpi=300)
plt.close()

print("Figuras geradas em:", OUTDIR)
for arq in sorted(os.listdir(OUTDIR)):
    print("-", arq)
