import csv
import re
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

SLEEP = 1.0
CSV_FILE = "publicacoes_iphan.csv"

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


def clean_text(text):
    return " ".join(str(text).replace("\xa0", " ").split()).strip()


def get_soup(params):
    r = requests.get(LIST_URL, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "lxml")


def get_total_records(soup):
    txt = soup.get_text(" ", strip=True)
    m = re.search(r"Registros encontrados:\s*(\d+)", txt, re.IGNORECASE)
    return int(m.group(1)) if m else 0


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


def extract_field(pattern, text):
    m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not m:
        return ""
    return clean_text(m.group(1))


def extract_items_from_page(soup, categoria_id, categoria_nome, pagina_num):
    items = []
    seen = set()

    title_tags = soup.find_all(["h1", "h2", "h3", "h4"])

    for title_tag in title_tags:
        titulo = normalize_title(title_tag.get_text(" ", strip=True))

        if looks_like_invalid_title(titulo):
            continue

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

        block_text = clean_text(best_container.get_text(" ", strip=True))

        if "Autor:" not in block_text:
            continue

        autor = extract_field(r"Autor:\s*(.+?)(?=Edição:|Páginas:|Publicação:|$)", block_text)
        edicao = extract_field(r"Edição:\s*(.+?)(?=Páginas:|Publicação:|$)", block_text)
        paginas = extract_field(r"Páginas:\s*([0-9]+)(?=\D|$)", block_text)
        publicacao = extract_field(r"Publicação:\s*(.+?)(?=$)", block_text)

        if not autor:
            continue

        desc_text = block_text
        desc_text = re.sub(re.escape(titulo), "", desc_text, count=1, flags=re.IGNORECASE)
        desc_text = re.sub(r"Autor:\s*.+?(?=Edição:|Páginas:|Publicação:|$)", "", desc_text, flags=re.IGNORECASE | re.DOTALL)
        desc_text = re.sub(r"Edição:\s*.+?(?=Páginas:|Publicação:|$)", "", desc_text, flags=re.IGNORECASE | re.DOTALL)
        desc_text = re.sub(r"Páginas:\s*[0-9]+", "", desc_text, flags=re.IGNORECASE)
        desc_text = re.sub(r"Publicação:\s*.+?(?=$)", "", desc_text, flags=re.IGNORECASE | re.DOTALL)
        descricao = clean_text(desc_text)

        capa_url = ""
        img = best_container.find("img")
        if img and img.get("src"):
            capa_url = urljoin(BASE_URL, img["src"])

        pdf_url = ""
        for a in best_container.find_all("a", href=True):
            href = a["href"].strip()
            full = urljoin(BASE_URL, href)
            if ".pdf" in full.lower():
                pdf_url = full
                break

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
            "publicacao": publicacao,
            "descricao": descricao,
            "capa_url": capa_url,
            "pdf_url": pdf_url,
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
        if not page_items:
            print(f"[INFO] Página {pagina} sem itens. Encerrando categoria.")
            break

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


def save_csv(rows):
    fields = [
        "categoria_id",
        "categoria",
        "pagina_listagem",
        "titulo",
        "autor",
        "edicao",
        "paginas",
        "publicacao",
        "descricao",
        "capa_url",
        "pdf_url",
    ]

    with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    all_rows = []

    for cat in CATEGORIES:
        try:
            rows = scrape_category(cat)
            all_rows.extend(rows)
            time.sleep(SLEEP)
        except Exception as e:
            print(f"[ERRO] Falha na categoria {cat['nome']}: {e}")

    save_csv(all_rows)
    print(f"\n[OK] Finalizado. CSV salvo em {CSV_FILE}")
    print(f"[OK] Total geral de itens: {len(all_rows)}")


if __name__ == "__main__":
    main()
