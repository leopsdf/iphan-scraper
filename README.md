#Curadoria Digital Orientada por Dados em Acervos Institucionais de Patrimônio Cultural
Este repositório contém a implementação da pipeline desenvolvida para coleta, estruturação, auditoria e análise de publicações digitais do portal do Instituto do Patrimônio Histórico e Artístico Nacional (IPHAN).

#Contexto
O projeto foi desenvolvido no contexto de uma pesquisa sobre curadoria digital, organização da informação e uso de dados em acervos institucionais, com aplicação no artigo submetido ao WIDaT 2026.

#Objetivo
Transformar um conjunto de publicações digitais dispersas em uma base estruturada, auditável e reutilizável, apoiando práticas de:

- curadoria digital
- organização da informação
- preservação digital
- interoperabilidade
- análise de acervos culturais

#Pipeline desenvolvida
A abordagem implementada segue uma pipeline composta por:

1. Coleta automatizada de metadados
2. Diagnóstico da estrutura HTML
3. Identificação de documentos digitais
4. Download automatizado dos arquivos
5. Auditoria do processo (duplicidades e falhas)
6. Geração de artefatos (catálogo, relatórios e gráficos)

#Estrutura do projeto
iphan_scraper/
├── scripts/ # scripts Python
├── data/ # dados brutos e processados
├── reports/ # relatórios
├── figures/ # gráficos do artigo
├── downloads/ # PDFs coletados


#Tecnologias utilizadas
- Python
- requests
- BeautifulSoup
- pandas
- matplotlib

#Resultados
- 1.132 registros catalogados
- 559 downloads realizados
- 555 títulos únicos
- identificação de duplicidades e lacunas no acervo

#Aplicação
Este projeto sustenta um estudo sobre:

- curadoria digital
- metadados
- interoperabilidade
- dados em patrimônio cultural

#Autor

Leonardo de Paiva Souza

Universidade de Brasília (UnB)

