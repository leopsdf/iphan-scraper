import os
import re
import csv
import time
from math import ceil
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://portal.iphan.gov.br"
LIST_URL = BASE_URL + "/publicacoes/lista"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

SLEEP = 0.5
DOWNLOAD_DIR = "downloads/pdfs_v3"
CSV_AUDITORIA = "auditoria_download_pdfs_v3.csv"

INVALID_TITLES = {
    "acesse",
    "saiba mais",
    "clique aqui",
    "leia mais",
    "download",
    "pdf",
    "publicações",
}

CATEGORIES = [
    {"id": "", "nome": "Linhas editoriais e textos diversos"},
    {"id": "62", "nome": "Acervos"},
    {"id": "28", "nome": "Anais"},
    {"id": "54", "nome": "Artigos do Patrimônio"},
    {"id": "55", "nome": "Boletins do Iphan"},
    {"id": "14", "nome": "Cadernos de Pesquisa e Documentação"},
    {"id": "29", "nome": "Cadernos Técnicos"},
    {"id": "16", "nome": "Catálogos de Patrimônio e Leitura"},
    {"id": "41", "nome": "Coleções - Arquitetura"},
    {"id": "42", "nome": "Coleções - Cadernos de Memória"},
    {"id": "43", "nome": "Coleções - Grandes Obras e Intervenções"},
    {"id": "44", "nome": "Coleções - Imagens"},
    {"id": "45", "nome": "Coleções - Obras de Referência"},
    {"id": "69", "nome": "Coleções - Patrimônio cultural do Brasil"},
    {"id": "66", "nome": "Coleções - Patrimônio para Jovens"},
    {"id": "46", "nome": "Coleções - Registro"},
    {"id": "47", "nome": "Coleções - Roteiros do Patrimônio"},
    {"id": "70", "nome": "Coleções - 20 anos INRC"},
    {"id": "30", "nome": "Educação Patrimonial"},
    {"id": "19", "nome": "Folclore e Cultura Popular"},
    {"id": "20", "nome": "Manuais"},
    {"id": "59", "nome": "Patrimônio Imaterial - Diversidade Linguística"},
    {"id": "22", "nome": "Patrimônio Imaterial - Dossiês"},
    {"id": "68", "nome": "Patrimônio Imaterial - Planos de Salvaguarda"},
    {"id": "31", "nome": "Patrimônio Imaterial - Títulos Diversos"},
    {"id": "63", "nome": "Patrimônio Material - Títulos Diversos"},
    {"id": "32", "nome": "Publicações Diversas - Arqueologia"},
    {"id": "56", "nome": "Publicações Diversas - Cidades"},
    {"id": "35", "nome": "Publicações Diversas - Coletâneas"},
    {"id": "36", "nome": "Publicações Diversas - Imigrantes"},
    {"id": "64", "nome": "Publicações Diversas - Inventários"},
    {"id": "37", "nome": "Publicações Diversas - Museus"},
    {"id": "38", "nome": "Publicações Diversas - Restauração"},
    {"id": "39", "nome": "Publicações Diversas - Revista Musas"},
    {"id": "40", "nome": "Publicações Diversas - Turismo"},
    {"id": "23", "nome": "Revista do Patrimônio"},
    {"id": "73", "nome": "Revista do Prêmio Rodrigo Melo Franco de Andrade"},
    {"id": "24", "nome": "Revista Eletrônica nos Arquivos do IPHAN"},
    {"id": "61", "nome": "Rotas do Patrimônio"},
    {"id": "52", "nome": "Séries - Memórias do Patrimônio"},
    {"id": "49", "nome": "Séries - Pat. Cultural e Extensão Universitária"},
    {"id": "72", "nome": "Séries - Patrimônio em prática"},
    {"id": "53", "nome": "Séries - Pesquisa e Documentação"},
    {"id": "67", "nome": "Séries - Planos de Conservação"},
    {"id": "21", "nome": "Séries - Práticas e Reflexões"},
    {"id": "50", "nome": "Séries - Preservação e Desenvolvimento"},
    {"id": "51", "nome": "Séries - Reedições do Iphan"},
    {"id": "26", "nome": "Textos Especializados"},
    {"id": "74", "nome": "Superintendência - GO"},
]

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def clean_text(text):
    return " ".join(str(text).replace("\xa0", " ").split()).strip()


def normalize_title(title):
    title = clean_text(title)
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def looks_like_invalid_title(title):
    t = normalize_title(title).lower().strip(" .:-")
    if not t:
        return True
    if t in INVALID_TITLES:
        return True
    if len(t) <= 3:
        return True
    return False


def slugify_filename(name):
    name = normalize_title(name)
    name = re.sub(r"[\\/*?:\"<>|]", "_", name)
    name = re.sub(r"\s+", "_", name)
    return name[:180]


def get_soup(params):
    r = requests.get(LIST_URL, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "lxml")


def get_total_records(soup):
    txt = soup.get_text(" ", strip=True)
    m = re.search(r"Registros encontrados:\s*(\d+)", txt, re.IGNORECASE)
    return int(m.group(1)) if m else 0


def find_best_container(title_tag):
    container = title_tag
    best_container = title_tag

    for _ in range(8):
        if not container.parent:
            break
        container = container.parent
        block_text = clean_text(container.get_text(" ", strip=True))
        if "Autor:" in block_text:
            best_container = container
            if "Edição:" in block_text or "Páginas:" in block_text:
                break

    return best_container


def extract_pdf_and_cover_from_container(container):
    html = str(container)

    pdfs = re.findall(r'https?://[^"\']+\.pdf[^"\']*', html, flags=re.IGNORECASE)
    pdfs = list(dict.fromkeys(pdfs))

    cover_url = ""
    for img in container.find_all("img"):
        src = img.get("src")
        if not src:
            continue
        full = urljoin(BASE_URL, src)
        if "uploads/ckfinder/images/Diversas/Publicacaoes/" in full:
            cover_url = full
            break

    return pdfs, cover_url


def download_file(url, filepath):
    try:
        r = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        r.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True, ""
    except Exception as e:
        return False, str(e)


def extract_items_from_page(soup, categoria_id, categoria_nome, pagina_num):
    items = []
    seen = set()

    title_tags = soup.find_all(["h1", "h2", "h3", "h4"])

    for title_tag in title_tags:
        titulo = normalize_title(title_tag.get_text(" ", strip=True))

        if looks_like_invalid_title(titulo):
            continue

        container = find_best_container(title_tag)
        block_text = clean_text(container.get_text(" ", strip=True))

        if "Autor:" not in block_text:
            continue

        autor = ""
        edicao = ""
        paginas = ""

        m = re.search(r"Autor:\s*(.+?)(?=Edição:|Páginas:|Publicação:|$)", block_text, re.IGNORECASE | re.DOTALL)
        if m:
            autor = clean_text(m.group(1))

        m = re.search(r"Edição:\s*(.+?)(?=Páginas:|Publicação:|$)", block_text, re.IGNORECASE | re.DOTALL)
        if m:
            edicao = clean_text(m.group(1))

        m = re.search(r"Páginas:\s*([0-9]+)(?=\D|$)", block_text, re.IGNORECASE)
        if m:
            paginas = clean_text(m.group(1))

        if not autor:
            continue

        pdf_urls, capa_url = extract_pdf_and_cover_from_container(container)

        key = (categoria_id, titulo.lower())
        if key in seen:
            continue
        seen.add(key)

        items.append({
            "categoria_id": categoria_id,
            "categoria": categoria_nome,
            "pagina_listagem": pagina_num,
            "titulo": titulo,
            "autor": autor,
            "edicao": edicao,
            "paginas": paginas,
            "capa_url": capa_url,
            "pdf_urls": pdf_urls,
        })

    return items


def scrape_category(cat):
    categoria_id = cat["id"]
    categoria_nome = cat["nome"]

    print(f"\n[INFO] Categoria: {categoria_nome} (ID={categoria_id!r})")

    soup = get_soup({"categoria": categoria_id, "busca": ""})
    total_records = get_total_records(soup)
    first_items = extract_items_from_page(soup, categoria_id, categoria_nome, 1)

    items_per_page = len(first_items)
    if items_per_page == 0:
        print("[INFO] Nenhum item encontrado nessa categoria.")
        return []

    total_pages = ceil(total_records / items_per_page) if total_records else 1

    print(f"[INFO] Registros encontrados: {total_records}")
    print(f"[INFO] Itens por página: {items_per_page}")
    print(f"[INFO] Total estimado de páginas: {total_pages}")

    all_items = list(first_items)

    for pagina in range(2, total_pages + 1):
        print(f"[INFO] Lendo categoria={categoria_id!r} página={pagina}")
        soup = get_soup({
            "categoria": categoria_id,
            "busca": "",
            "pagina": pagina
        })

        page_items = extract_items_from_page(soup, categoria_id, categoria_nome, pagina)
        all_items.extend(page_items)
        time.sleep(SLEEP)

    final_items = []
    seen = set()
    for item in all_items:
        key = (item["categoria_id"], item["titulo"].strip().lower())
        if key not in seen:
            seen.add(key)
            final_items.append(item)

    print(f"[INFO] Total coletado na categoria '{categoria_nome}': {len(final_items)}")
    return final_items


def main():
    auditoria = []
    downloaded_urls = set()

    for cat in CATEGORIES:
        try:
            items = scrape_category(cat)
        except Exception as e:
            print(f"[ERRO] Falha na categoria {cat['nome']}: {e}")
            continue

        for item in items:
            titulo = item["titulo"]
            categoria = item["categoria"]
            capa_url = item["capa_url"]
            pdf_urls = item["pdf_urls"]

            if not pdf_urls:
                auditoria.append({
                    "categoria": categoria,
                    "titulo": titulo,
                    "autor": item["autor"],
                    "edicao": item["edicao"],
                    "paginas": item["paginas"],
                    "capa_url": capa_url,
                    "pdf_url": "",
                    "arquivo_local": "",
                    "status": "sem_pdf_no_html"
                })
                continue

            for idx, pdf_url in enumerate(pdf_urls, start=1):
                if "uploads/legislacao" in pdf_url.lower():
                    auditoria.append({
                        "categoria": categoria,
                        "titulo": titulo,
                        "autor": item["autor"],
                        "edicao": item["edicao"],
                        "paginas": item["paginas"],
                        "capa_url": capa_url,
                        "pdf_url": pdf_url,
                        "arquivo_local": "",
                        "status": "ignorado_legislacao"
                    })
                    continue

                if pdf_url in downloaded_urls:
                    auditoria.append({
                        "categoria": categoria,
                        "titulo": titulo,
                        "autor": item["autor"],
                        "edicao": item["edicao"],
                        "paginas": item["paginas"],
                        "capa_url": capa_url,
                        "pdf_url": pdf_url,
                        "arquivo_local": "",
                        "status": "pdf_duplicado"
                    })
                    continue

                downloaded_urls.add(pdf_url)

                base_name = slugify_filename(titulo)
                if len(pdf_urls) > 1:
                    filename = f"{base_name}_{idx}.pdf"
                else:
                    filename = f"{base_name}.pdf"

                filepath = os.path.join(DOWNLOAD_DIR, filename)

                ok, erro = download_file(pdf_url, filepath)
                if ok:
                    print(f"[BAIXADO] {filename}")
                    status = "baixado"
                else:
                    print(f"[ERRO] {titulo} -> {erro}")
                    filepath = ""
                    status = f"erro_download: {erro}"

                auditoria.append({
                    "categoria": categoria,
                    "titulo": titulo,
                    "autor": item["autor"],
                    "edicao": item["edicao"],
                    "paginas": item["paginas"],
                    "capa_url": capa_url,
                    "pdf_url": pdf_url,
                    "arquivo_local": filepath,
                    "status": status
                })

                time.sleep(SLEEP)

    with open(CSV_AUDITORIA, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "categoria",
                "titulo",
                "autor",
                "edicao",
                "paginas",
                "capa_url",
                "pdf_url",
                "arquivo_local",
                "status",
            ]
        )
        writer.writeheader()
        writer.writerows(auditoria)

    print("\n[OK] Auditoria salva em:", CSV_AUDITORIA)
    print("[OK] PDFs baixados em:", DOWNLOAD_DIR)


if __name__ == "__main__":
    main()
