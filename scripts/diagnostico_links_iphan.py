import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "http://portal.iphan.gov.br"
URL = "http://portal.iphan.gov.br/publicacoes/lista?categoria=62&busca="

headers = {"User-Agent": "Mozilla/5.0"}

r = requests.get(URL, headers=headers, timeout=30)
r.raise_for_status()
soup = BeautifulSoup(r.text, "lxml")

for h in soup.find_all("h4"):
    titulo = " ".join(h.get_text(" ", strip=True).split())
    if not titulo:
        continue

    print("\n" + "=" * 80)
    print("TÍTULO:", titulo)

    container = h
    for _ in range(8):
        if container.parent is None:
            break
        container = container.parent
        texto = " ".join(container.get_text(" ", strip=True).split())
        if "Autor:" in texto:
            break

    links = container.find_all("a", href=True)
    if not links:
        print("Nenhum link encontrado no bloco.")
        continue

    for a in links:
        href = a.get("href", "").strip()
        texto_link = " ".join(a.get_text(" ", strip=True).split())
        full = urljoin(BASE_URL, href)
        print(f"LINK: texto='{texto_link}' | href='{full}'")
