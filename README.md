🔬 SenoTrack Enterprise v8.0 — Plataforma Avançada de Triagem Quimioinformática, Longevidade Celular e Docking Virtual

O **SenoTrack Enterprise v8.0** é uma plataforma analítica e biomolecular de alta performance projetada para a triagem de pipelines clínicos, docking virtual e processamento em lote de compostos senolíticos, senomorfos e alvos oncológicos (focados em reversão da fragilidade biológica e senescência celular).

Nesta versão **8.0 Enterprise**, a plataforma expande sua arquitetura de alta disponibilidade ao incorporar motores quimioinformáticos avançados via **RDKit**, alertas estruturais de toxicidade (PAINS e hERG), simulações de encaixe molecular ligante-proteína (RCSB PDB + py3Dmol) e integração de literatura científica (PubMed) ao seu Agente Clínico de IA Híbrida.

---

🌐 Como Acessar a Plataforma
A plataforma está pronta para uso em nuvem, não exigindo instalação local de dependências ou conhecimentos prévios em linha de comando:

👉 **[CLIQUE AQUI PARA ACESSAR O SENOTRACK ONLINE](https://seu-app.streamlit.app)**
*(Ajuste a URL acima para o link final do seu projeto no Streamlit Cloud)*

---

🤖 O que há de novo na v8.0 Enterprise?

🔬 **Motor Quimioinformático Integrado (RDKit):**
- Cálculo em tempo real de descritores físico-químicos e verificação estendida de regras de biodisponibilidade (*Lipinski, Veber e Egan*).
- **Filtros de Alerta PAINS:** Identificação automática de subestruturas promíscuas para evitar falsos positivos em ensaios.
- **Triagem de Cardiotoxicidade (hERG):** Mapeamento e estimativa de risco de inibição dos canais hERG.

🎯 **Docking Virtual & Proteômica 3D:**
- Integração direta com o repositório **RCSB PDB** para busca e renderização tridimensional de macromoléculas em tempo real via **py3Dmol / WebGL**.
- Estimativa geométrica e avaliação de compatibilidade de binding ligante-bolsa catalítica (*docking virtual simplificado*).

📊 **Benchmarking & Radar Farmacocinético:**
- Visualização gráfica interativa do tipo Radar (*Plotly*) comparando candidatos com o fármaco padrão-ouro da classe.
- Matriz de similaridade estrutural (Tanimoto/Fingerprints) e análise de sinergia entre moléculas.

🤖 **Agente Clínico de IA Híbrido + Literatura (PubMed):**
- **Suporte a LLMs Externas:** Integração nativa com APIs da OpenAI e Google Gemini para proposição de Mecanismos de Ação (MoA) e sugestões de síntese.
- **Simulador Preditivo Local (Zero Downtime):** Em caso de ausência de chave de API ou queda de conexão, o sistema aciona automaticamente o modelo preditivo local sem quebrar a execução.
- **Nível de Evidência Científica:** Mapeamento em tempo real no PubMed e classificação hierárquica das evidências (*In Vitro, Modelos Animais, Ensaios Clínicos e Metanálises*).

📓 **Caderno Eletrônico de Laboratório (ELN) Audit-Ready:**
- Trilha de auditoria persistente em `st.session_state` com exportação de logs em JSON.
- Exportação multiformato: laudos técnicos e executivos em PDF estilizado (`FPDF2`), relatórios CSV, JSON e citações bibliográficas em formato RIS/BibTeX.

---

🧪 Funcionalidades Principais

📊 **Perfil Clínico, Químico e Terapêutico Individual:**
- Consulta automatizada via PUG-REST integrada ao repositório público internacional do **PubChem**.
- Identificação de peso molecular, LogP, TPSA, pontes de hidrogênio e conformações estruturais 2D e 3D.
- Análise de mecanismos de ação nos eixos de sobrevivência celular (SCAP), barreiras farmacêuticas e síntese preditiva via Agente de IA.

📁 **Processamento de Lotes Hospitalares & Laboratoriais:**
- **Motor de Regras Químicas & Lipinski/Veber/Egan:** Filtragem automática de arquivos carregados (`.csv` ou `.xlsx`) avaliando critérios de biodisponibilidade e restrições farmacocinéticas.
- **Detecção de Sinergias & PAINS:** Identificação de combos senolíticos avançados (ex: *Dasatinib + Quercetina*) e filtragem de falsos positivos no lote.
- **Painel Comparativo:** Exibição em cartões e gráficos interativos de distribuição de massa e perfis físico-químicos.
- **Emissão Executiva:** Exportação automatizada de laudos analíticos em PDF e planilhas tabulares.

---

🛠️ Tech Stack & Arquitetura

- **Linguagem & Framework:** Python 3.9+ / Streamlit
- **Quimioinformática & Moléculas:** RDKit
- **Dados & Analytics:** Pandas, NumPy, OpenPyXL
- **APIs & Conectividade:** PubChem PUG-REST API, PubMed Entrez API, RCSB PDB REST API, OpenAI API / Gemini API
- **Visualização 3D & Gráficos:** py3Dmol (WebGL), Plotly, Matplotlib
- **Documentos & Exportação:** FPDF2 (PDF Engine), JSON (Audit Trail), RIS/BibTeX