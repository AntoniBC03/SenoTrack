🔬 SenoTrack Enterprise v7.0 — Plataforma Avançada de Triagem, Longevidade Celular e Agente de IA
O SenoTrack Enterprise v7.0 é uma plataforma analítica e biomolecular de alta performance projetada para triagem de pipelines clínicos e processamento em lote de compostos senolíticos e senomorfos (focados em reversão da fragilidade biológica e senescência celular).

Nesta versão 7.0 Enterprise, a plataforma evoluiu para uma arquitetura resiliente e de alta disponibilidade, incorporando um Agente Clínico de IA Híbrida com Fallback Preditivo Local, renderização 3D em tempo real via WebGL e suporte para operação offline, garantindo continuidade operacional em ambientes clínicos isolados.

🌐 Como Acessar a Plataforma
A plataforma está pronta para uso em nuvem, não exigindo instalação local de dependências ou conhecimentos prévios em linha de comando:

👉 CLIQUE AQUI PARA ACESSAR O SENOTRACK ONLINE

(Ajuste a URL acima para o link final do seu projeto no Streamlit Cloud)

🤖 O que há de novo na v7.0 Enterprise?
🤖 Agente Clínico de IA Híbrido (Resiliência & Fallback):

Suporte a LLMs Externa: Aceita chaves de API para OpenAI e Google Gemini.

Simulador Preditivo Local: Caso nenhuma chave de API seja fornecida ou haja falha de conexão, o sistema aciona automaticamente um modelo preditivo local sem quebrar a execução, gerando insights farmacológicos contextuais e garantindo zero downtime.

🌐 Alta Disponibilidade & Operação Offline:

Contingência local projetada para rodar sem dependência crítica de redes externas ou instabilidades na API do PubChem, permitindo o uso em ambiente de produção hospitalar/laboratorial.

🧬 Renderização Estereoscópica 2D e 3D:

Integração com py3Dmol e WebGL para navegação, rotação e visualização interativa das conformações tridimensionais das moléculas.

📜 Rastreabilidade & Audit Trail (Audit-Ready):

Sistema de auditoria com persistência em st.session_state e exportação de logs em JSON, atendendo a padrões rígidos de governança de dados.

📄 Engine de Laudos em PDF Atualizada:

Geração de laudos executivos em formato PDF (fpdf2) com gráficos em buffer de memória (Matplotlib), prontos para impressão e download imediato.

🧪 Funcionalidades Principais
📊 Perfil Clínico e Terapêutico Individual:

Consulta automatizada REST integrada ao repositório público internacional do PubChem.

Identificação de peso molecular, fórmula e conformação estrutural 2D e 3D.

Diagnóstico de mecanismos de ação nos eixos de sobrevivência celular (SCAP), barreiras farmacêuticas e síntese preditiva via Agente de IA.

📁 Processamento de Lotes Hospitalares:

Motor de Regras Químicas & Lipinski: Filtragem automática de arquivos carregados (.csv ou .xlsx) avaliando critérios de biodisponibilidade e restrições farmacocinéticas.

Detecção de Sinergias: Identificação de combos senolíticos avançados (ex: Dasatinib + Quercetina).

Painel Comparativo: Exibição em cartões e gráficos automatizados de distribuição de massa molecular do lote.

Emissão Executiva: Exportação automatizada de laudos analíticos completos em PDF.

🛠️ Tech Stack & Arquitetura
Linguagem & Framework: Python 3.10+ / Streamlit

Dados & Analytics: Pandas, NumPy, OpenPyXL

APIs & Conectividade: PubChem REST API, OpenAI API / Gemini API

Visualização: Py3Dmol (WebGL), Matplotlib

Documentos & Exportação: FPDF2 (PDF Engine), JSON (Audit Trail)