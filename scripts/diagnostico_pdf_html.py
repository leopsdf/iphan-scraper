import re
from bs4 import BeautifulSoup

ARQUIVO = "amostra_categoria_62.html"

with open(ARQUIVO, "r", encoding="utf-8") as f:
    html = f.read()

print("=" * 80)
print("1. OCORRÊNCIAS DE '.pdf' NO HTML")
pdfs = re.findall(r'[^"\']+\.pdf[^"\']*', html, flags=re.IGNORECASE)
for p in sorted(set(pdfs))[:50]:
    print(p)
print(f"\nTotal de ocorrências '.pdf': {len(set(pdfs))}")

print("\n" + "=" * 80)
print("2. OCORRÊNCIAS DE 'uploads'")
uploads = re.findall(r'[^"\']*uploads[^"\']*', html, flags=re.IGNORECASE)
for u in sorted(set(uploads))[:50]:
    print(u)
print(f"\nTotal de ocorrências 'uploads': {len(set(uploads))}")

print("\n" + "=" * 80)
print("3. IMAGENS ENCONTRADAS")
soup = BeautifulSoup(html, "lxml")
for img in soup.find_all("img")[:30]:
    print("src =", img.get("src"))
    print("data-src =", img.get("data-src"))
    print("alt =", img.get("alt"))
    print("-" * 40)

print("\n" + "=" * 80)
print("4. ELEMENTOS COM onclick")
for tag in soup.find_all(attrs={"onclick": True})[:30]:
    print(tag.name, tag.get("onclick"))
    print("-" * 40)

print("\n" + "=" * 80)
print("5. ELEMENTOS COM data-*")
for tag in soup.find_all(True)[:300]:
    attrs = tag.attrs
    data_attrs = {k: v for k, v in attrs.items() if str(k).startswith("data-")}
    if data_attrs:
        print(tag.name, data_attrs)
