# SenoTrack Enterprise v10.0

Hub de análise para triagem de compostos em **oncologia, longevidade celular e P&D farmacêutico**, construído em Streamlit. Reúne consulta a bases públicas (PubChem, PubMed, RxNav, RCSB PDB), cálculo de descritores moleculares com RDKit, visualização 2D/3D, um caderno eletrônico de laboratório (ELN) e exportação de relatórios.

> **Aviso:** ferramenta de **triagem preliminar e apoio educacional**. Os scores de docking, hERG, sinergia e a classificação de evidência são **heurísticas simplificadas**. Não substituem docking real, ensaios in vitro/in vivo, revisão sistemática nem decisão clínica.

---

## Funcionalidades

| Aba | O que faz |
|---|---|
| **Perfil Clínico e Terapêutico** | Busca um composto por nome (inglês): fórmula, massa, aplicação, pipeline, PMID no PubMed, RxCUI no RxNav, estrutura 2D e modelo 3D interativo. Salva no ELN e gera laudo PDF. |
| **Processamento de Lotes** | Upload de `.xlsx`/`.csv` (até 200 compostos), consulta paralela às APIs, filtro por teto de massa molecular, KPIs, cards, tabela mestra, gráfico, parecer sintético, exportação PDF/JSON. |
| **Triagem Físico-Química** | Lipinski, Veber, Egan, alertas PAINS (A/B/C), risco hERG heurístico, estrutura 2D e download de `.sdf` 3D otimizado (MMFF). |
| **Docking Virtual & Proteômica** | Visualiza proteína (RCSB PDB por ID ou upload `.pdb`) e calcula uma estimativa **heurística** de encaixe (tamanho, lipofilicidade, flexibilidade). |
| **Farmacoterapia & Benchmark** | Compara 2 a 6 moléculas: matriz de similaridade (LogP/TPSA) e radar contra o fármaco de referência do módulo ativo. |
| **Agente Clínico & Literatura** | Classifica o nível de evidência do artigo recuperado (por palavras-chave do título), propõe um MoA por regras e exporta citação `.bib`/`.ris` com metadados reais do PubMed. |
| **Caderno Científico (ELN)** | Registro manual ou automático de experimentos; exporta JSON, CSV e PDF consolidado. |

### Recursos transversais

- **6 idiomas:** português, inglês, espanhol, chinês, alemão e japonês (troca em tempo real, sem perder o estado dos widgets).
- **Dois perfis de interface:** *Didático* (simplificado) e *Pesquisa/P&D* (PAINS, hERG, limites ajustáveis de TPSA e ligações rotacionáveis).
- **5 módulos temáticos:** Longevidade/Oncologia, Neurologia, Cardiologia, Endocrinologia/Metabolismo e Imunologia.
- **Modo de demonstração (offline):** usa dados locais (`MOCK_PUBCHEM_DATA`) sem acessar a rede.
- **Auditoria:** histórico de consultas da sessão, exportável em JSON.
- **Tema:** acompanha o tema claro/escuro nativo do Streamlit.

---

## Requisitos

- Python 3.10 ou superior
- Acesso à internet (exceto no modo offline)

Dependências (`requirements.txt`):

```txt
streamlit>=1.35
requests
urllib3>=1.26
pandas
openpyxl
matplotlib
plotly
fpdf2>=2.7
py3Dmol
rdkit
```

> Instale `fpdf2`, **não** o pacote legado `fpdf`. O app usa a API nova (`new_x`/`new_y`).

## Instalação e execução

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

O app abre em `http://localhost:8501`.

---

## Estrutura do projeto

```
.
├── app.py            # aplicação completa (UI, dados, RDKit, PDF, i18n)
├── style.css         # estilos opcionais (variáveis de tema)
├── requirements.txt
└── README.md
```

Organização interna do `app.py`, de cima para baixo:

1. Imports, constantes e compatibilidade de versões do Streamlit
2. Ícones SVG e cabeçalhos de seção
3. i18n: `TRANSLATIONS`, `EXTRA_TRANSLATIONS`, `MODULE_TRANSLATIONS`, funções `t()` e `modulo_nome()`
4. CSS e estado global (`st.session_state`)
5. Base de conhecimento: `KB_DATA`, `FARMACO_CONTROLE_POR_MODULO`, `MOCK_PUBCHEM_DATA`
6. Camada de dados: rede com retry, PubChem, PubMed, RxNav, RCSB, execução paralela
7. RDKit: descritores, hERG, SVG 2D, SDF 3D (todos com cache)
8. Citações e auditoria
9. PDF (FPDF2)
10. Sidebar e as 7 abas

---

## Fontes de dados

| Fonte | Uso | Cache |
|---|---|---|
| [PubChem PUG REST](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest) | Fórmula, massa, SMILES, SDF 3D | 1 h |
| [PubMed E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/) | PMID, título, autores, periódico, ano | 1 h |
| [RxNav](https://lhncbc.nlm.nih.gov/RxNav/) | RxCUI | 1 h |
| [RCSB PDB](https://www.rcsb.org/) | Estruturas de proteínas | 1 h |

Falhas transitórias de rede **não são cacheadas**: só respostas definitivas (encontrado ou não encontrado) entram no cache.

---

## Configuração

**Barra lateral**

- **Idioma, perfil, módulo ativo:** controlam textos e conteúdo exibido.
- **Teto de massa molecular:** compostos acima do limite são excluídos do lote.
- **TPSA e ligações rotacionáveis (modo Pesquisa):** ajustam o critério de Veber.
- **Modo de demonstração:** funciona só com os compostos de `MOCK_PUBCHEM_DATA`.
- **Chave API:** campo reservado. Hoje **nenhum LLM é chamado**; o "insight" e o "MoA" são sínteses determinísticas por regras locais (há um `TODO` em `gerar_insight_ia`).

**Limites internos** (constantes no topo do `app.py`)

| Constante | Valor | Função |
|---|---|---|
| `MAX_LOTE` | 200 | Máximo de compostos por planilha |
| `MAX_PDB_BYTES` | 25 MB | Tamanho máximo de arquivo PDB |
| `MAX_PDB_ATOMS_SURFACE` | 20.000 | Acima disso, a superfície VDW não é desenhada |

**Planilha de lote:** a **primeira coluna** contém os nomes dos compostos (inglês). Aceita `.xlsx` e `.csv` (separador `,` ou `;` detectado automaticamente). Há um modelo para download na própria aba.

---

## Como estender

**Adicionar um composto à base local**

1. Inclua uma entrada em `KB_DATA` com `modulo`, `tag`, `classe`, `aplicacao` e `pipeline` nos 6 idiomas.
2. Para uso offline, inclua também em `MOCK_PUBCHEM_DATA` (`formula`, `weight`, `smiles`). Use `smiles: ""` para macromoléculas/biológicos.

**Adicionar um idioma**

1. Inclua o código em `IDIOMAS_DISPONIVEIS`.
2. Adicione a nova chave em **todas** as entradas de `TRANSLATIONS`, `EXTRA_TRANSLATIONS`, `MODULE_TRANSLATIONS` e `KB_DATA`. Na ausência, o app cai para português.

**Adicionar um módulo temático**

1. Inclua a tradução em `MODULE_TRANSLATIONS`.
2. Defina o fármaco de referência em `FARMACO_CONTROLE_POR_MODULO`.
3. Associe compostos ao módulo em `KB_DATA`.

---

## Limitações conhecidas

- **Docking, hERG e sinergia são heurísticas**, descritas como tal na interface.
- **Biológicos e peptídeos grandes** (anticorpos, semaglutida etc.) não têm SMILES tratável por RDKit; as abas físico-química, docking e benchmark não os suportam.
- **PDF:** usa fonte Helvetica (Latin-1) e rótulos em português sem acento. Chinês e japonês podem não renderizar; seria necessário carregar uma fonte TTF Unicode via `pdf.add_font`.
- **Busca no PubMed:** retorna o artigo mais relevante por título/resumo; a classificação de evidência olha apenas palavras-chave do título.
- **Sessão em memória:** ELN e auditoria vivem em `st.session_state` e são perdidos ao fechar a aba. Exporte antes de sair.
- **APIs públicas** têm limites de taxa; lotes grandes podem receber respostas lentas ou erros temporários (o app tenta novamente 2 vezes).

---

## Solução de problemas

| Sintoma | Causa provável |
|---|---|
| `ModuleNotFoundError: rdkit` | `pip install rdkit` (em Conda: `conda install -c conda-forge rdkit`) |
| `TypeError` ao gerar PDF (`ln`/`new_x`) | Versão antiga; instale `fpdf2>=2.7` e desinstale `fpdf` |
| Composto "não resolvido" no lote | Nome inválido no PubChem ou falha de rede |
| Visualização 3D em branco | Composto sem modelo 3D no PubChem (o app tenta gerar via RDKit) ou bloqueio de rede |
| Estilo diferente do esperado | `style.css` ausente; o app usa um fallback mínimo |

---

## Licença

Defina aqui a licença do projeto (por exemplo, MIT) e adicione o arquivo `LICENSE`.