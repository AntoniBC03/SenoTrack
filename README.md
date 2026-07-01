# 🔬 SenoTrack Platform v3.0 — Plataforma Avançada de Triagem e Longevidade Celular

O **SenoTrack v3.0** é uma plataforma analítica interativa projetada para a triagem de pipelines clínicos e processamento de lotes hospitalares, com foco na análise de compostos senolíticos e senomorfos (moléculas voltadas para a reversão da fragilidade biológica e rejuvenescimento celular através da eliminação de células senescentes).

Este projeto foi desenvolvido com foco em **acessibilidade e divulgação científica**. O objetivo é permitir que estudantes, pesquisadores e entusiastas da área de biologia e saúde explorem dados moleculares complexos, simulem interações medicamentosas e analisem sinergias biológicas de forma visual e intuitiva, eliminando barreiras técnicas e dispensando qualquer conhecimento em programação ou linhas de comando.

---

## 🌐 Como Acessar a Plataforma (Pronto para Uso)

Para utilizar o sistema, você não precisa instalar nenhum programa ou dependência no seu computador. A plataforma está hospedada em ambiente de produção na nuvem e pode ser acessada de qualquer navegador ou dispositivo móvel através do link oficial:

👉 **[CLIQUE AQUI PARA ACESSAR O SENOTRACK ONLINE](https://SEU_LINK_DO_STREAMLIT.streamlit.app)**  
*(Nota: Substitua o link acima pela URL gerada pelo Streamlit após realizar o deploy)*

---

## 🧪 Funcionalidades Principais do MVP

1. **📊 Perfil Clínico e Terapêutico (Aba 1):** 
   - Consulta molecular automatizada integrada à base internacional do **PubChem**.
   - Exibição de fórmulas químicas, massa molecular e conformação estrutural (Visualizador 2D e Modelo 3D rotacionável/interativo).
   - Diagnóstico detalhado sobre aplicações médicas profundas, mecanismos de ação nos eixos de sobrevivência celular (SCAP) e barreiras farmacêuticas atuais.

2. **📁 Processamento de Lotes Hospitalares (Aba 2):**
   - **Motor de Regras Químicas:** Varredura inteligente de arquivos carregados (`.csv` ou `.xlsx`) para detecção automática de sinergias terapêuticas avançadas (como o Combo D+Q — *Dasatinib + Quercetina*).
   - **Comparativo Direto de Eficiência:** Painel visual dinâmico em cartões paralelos para análise rápida de funções, força de ação, foco clínico e segurança laboratorial, adaptado para triagens gerenciais e tomadas de decisão rápidas.
   - **Tabela Gerencial Expandida:** Compilação estruturada de dados com enriquecimento de informações via API em tempo real.
   - **Análise Gráfica:** Gráfico automatizado de densidade molecular das amostras submetidas.
   - **Central de Emissão de Laudos:** Geração automática e download de laudos clínicos executivos em formato **PDF**.

---

## 📂 Estrutura de Arquivos do Repositório

Para o correto funcionamento do servidor de hospedagem, o repositório mantém a seguinte estrutura básica:
* `app.py` (ou nome do seu arquivo principal): Código fonte estruturado em Python e Streamlit.
* `requirements.txt`: Arquivo de configuração contendo as dependências e bibliotecas necessárias para a compilação do servidor.
* `modelo_triagem_senotrack.xlsx`: Planilha modelo de exemplo gerada dinamicamente pelo sistema para auxiliar o usuário no teste de triagem em lote.