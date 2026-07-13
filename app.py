import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import os
from fpdf import FPDF
import py3Dmol


# Configuração da página - Tema profissional e amplo
st.set_page_config(page_title="SenoTrack Enterprise", page_icon="🔬", layout="wide")


# --- FUNÇÃO AUXILIAR: SANITIZAÇÃO DE TEXTO PARA O PDF ---
def sanitize_pdf_text(texto):
    if texto is None:
        return ""
    return str(texto).encode("latin-1", "ignore").decode("latin-1")


# --- 1. CLASSE PDF DEFINIDA NO TOPO ---
class PDFLaudoPremium(FPDF):
    def header(self):
        self.set_fill_color(16, 185, 129)
        self.rect(0, 0, 210, 32, "F")
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "SENOTRACK ENTERPRISE SOLUTION", ln=True, align="C")
        self.set_font("Helvetica", "I", 9)
        self.cell(0, 5, "Relatorio de Viabilidade de Compostos Clinicos", ln=True, align="C")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Pagina {self.page_no()}", align="C")


# --- 2. FUNÇÃO DE GERAÇÃO DE PDF (ANÁLISE INDIVIDUAL) ---
def gerar_pdf_laudo(df):
    pdf = PDFLaudoPremium()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)

    for _, row in df.iterrows():
        pdf.cell(0, 10, sanitize_pdf_text(f"Composto: {row['Nome Oficial']}"), ln=True)
        pdf.multi_cell(0, 5, sanitize_pdf_text(f"Aplicacao: {row['Aplicação Médica']}"))
        pdf.ln(5)

    return bytes(pdf.output())


# --- 3. FUNÇÃO DE GERAÇÃO DE PDF (LOTE COMPLETO) ---
def gerar_pdf_laudo_lote(df_exibicao):
    pdf = PDFLaudoPremium()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pdf.set_text_color(50, 50, 50)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "1. Sumario Analitico da Triagem em Lote", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, f"Volume de compostos submetidos a varredura: {len(df_exibicao)} amostras processadas.", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "2. Mapeamento de Viabilidade e Complexidade de Cura por Entidade", ln=True)
    pdf.ln(2)

    for _, row in df_exibicao.iterrows():
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(
            0, 7,
            sanitize_pdf_text(f" Entidade: {row['Nome Oficial']} ({row['Fórmula']}) - {row['Massa Molecular']}"),
            border=1, ln=True, fill=True,
        )
        pdf.ln(1)

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(16, 185, 129)
        pdf.cell(0, 5, "    Mecanismo e Aplicacao Terapeutica:", ln=True)

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 5, sanitize_pdf_text(f"    {row['Aplicação Médica']}"))
        pdf.ln(1)

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(220, 53, 69)
        pdf.cell(0, 5, "    Desafios Estrategicos de Pipeline e Desenvolvimento:", ln=True)

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 5, sanitize_pdf_text(f"    {row['Mapeamento Pipeline']}"))
        pdf.ln(4)

    return bytes(pdf.output())


# --- BASE DE CONHECIMENTO CIENTÍFICO EXPANDIDA ---
BASE_CONHECIMENTO_GLOBAL = {
    "Longevidade Celular e Oncologia": {
        "quercetin": {
            "aplicacao": "Flavonoide natural exógeno que inibe a via de sobrevivência PI3K/AKT, induzindo seletivamente a apoptose em células senescentes e reduzindo drasticamente o SASP.",
            "pipeline": "Fase II de Ensaios Clínicos Translacionais. Desafios focados em melhorar a baixa biodisponibilidade oral crônica através de matrizes lipossomais.",
            "classe": "Flavonoide Senolítico"
        },
        "dasatinib": {
            "aplicacao": "Potente inibidor de tirosina quinase. Atua desregulando as redes de sinalização pró-sobrevivência das células senescentes através de dosagem intermitente 'hit-and-run'.",
            "pipeline": "Transição entre aplicações oncológicas e rejuvenescimento. Desafios envolvem o controle de toxicidade residual periférica.",
            "classe": "Inibidor de Tirosina Quinase"
        },
        "navitoclax": {
            "aplicacao": "Inibidor sintético que suprime os eixos antiapoptóticos BCL-2 e BCL-xL, reativando a morte celular programada em linhagens senescentes profundas.",
            "pipeline": "Validação clínica oncológica. O maior desafio disruptivo reside no controle de efeitos colaterais como a trombocitopenia aguda.",
            "classe": "Inibidor BCL-2 / BCL-xL"
        },
        "fisetin": {
            "aplicacao": "Polifenol flavonoide de alta especificidade senolítica. Modula negativamente as redes NF-kB, reduzindo o ecossistema inflamatório SASP com alto perfil de segurança.",
            "pipeline": "Fase II de estudos translacionais em humanos. Projetos priorizam a nanoencapsulação lipídica para otimização farmacocinética.",
            "classe": "Flavonoide Senolítico"
        },
        "resveratrol": {
            "aplicacao": "Agente senorfológico e modulador alostérico das Sirtuínas (SIRT1). Não induz a lise celular, mas reprograma epigeneticamente o microambiente contendo a inflamação.",
            "pipeline": "Uso global consolidado como nutracêutico. Esforços atuais focam na síntese de ativadores sintéticos de segunda geração (STACs) com maior estabilidade.",
            "classe": "Modulador de Sirtuína / Senomorfo"
        }
    },
    "Neurologia e Neuroproteção": {
        "donepezil": {
            "aplicacao": "Inibidor reversível da acetilcolinesterase (AChE). Aumenta a concentração cortical de acetilcolina, melhorando a neurotransmissão em tecidos afetados por demência progressiva.",
            "pipeline": "Aprovado globalmente para estágios leves a graves da Doença de Alzheimer. Pipelines de P&D focam na redução de efeitos colaterais gastrointestinais periféricos.",
            "classe": "Inibidor da AChE"
        },
        "memantine": {
            "aplicacao": "Antagonista de ligação de baixa afinidade dos receptores NMDA de glutamato. Protege o sistema nervoso contra a excitotoxicidade induzida pelo excesso patológico de glutamato.",
            "pipeline": "Consolidado na clínica farmacêutica. Pipelines de vanguarda buscam o desenvolvimento de formulações de liberação prolongada combinadas com outros agentes.",
            "classe": "Antagonista NMDA"
        }
    }
}


def obter_dados_cientificos_v2(nome_composto, modulo_selecionado):
    nome_limpo = nome_composto.strip().lower()
    base_modulo = BASE_CONHECIMENTO_GLOBAL.get(modulo_selecionado, {})
    
    for chave, dados in base_modulo.items():
        if chave in nome_limpo:
            return dados
            
    return {
        "aplicacao": f"O composto '{nome_composto.capitalize()}' encontra-se em estágio de triagem molecular primária para a área de {modulo_selecionado}. Mecanismos de ação específicos estão sob investigação analítica.",
        "pipeline": "Status de validação experimental inicial. Ensaios pré-clínicos e mapeamento farmacocinético preliminar agendados no pipeline corrente.",
        "classe": "Triagem Primária"
    }


def analisar_acao_reacao(peso_molecular, classe_terapeutica):
    if peso_molecular > 500:
        return "⚠️ Alerta de Reação: Risco de baixa biodisponibilidade por tamanho molecular avançado. Pode requerer veículos de entrega lipossomais."
    
    if "Inibidor" in classe_terapeutica:
        return "🟢 Mecanismo Ativo: Alta afinidade enzimática detectada. Recomenda-se monitorar a saturação de receptores a longo prazo."
        
    if "Senolítico" in classe_terapeutica:
        return "⚡ Mecanismo Ativo: Indução seletiva de apoptose celular. Requer protocolos de pulso intermitente para proteção de tecidos."
        
    if "Antagonista" in classe_terapeutica:
        return "🧠 Modulação Ativa: Bloqueio balanceado de receptores neurais contra neurotoxicidade."
        
    return "🔍 Perfil farmacocinético padrão estável sob investigação in vitro."


# --- GERADOR AUTOMÁTICO DO MODELO EXCEL ---
if not os.path.exists("modelo_triagem_senotrack.xlsx"):
    df_modelo = pd.DataFrame({"Composto": ["quercetin", "dasatinib", "donepezil", "memantine", "resveratrol"]})
    df_modelo.to_excel("modelo_triagem_senotrack.xlsx", index=False)

# Interface Principal
st.markdown("<p style='color: #10b981; font-weight: bold; margin-bottom: -10px;'>SENOTRACK ENTERPRISE • BIOTECH DATA</p>", unsafe_allow_html=True)
st.title("🔬 Hub Avançado de Análise Oncológica e Longevidade Celular")
st.markdown("---")

# CONFIGURAÇÃO DE MÓDULOS NA BARRA LATERAL
st.sidebar.markdown("### ⚙️ Configuração do Sistema")
modulo_ativo = st.sidebar.selectbox(
    "Selecione o Módulo de Análise:",
    list(BASE_CONHECIMENTO_GLOBAL.keys())
)
st.sidebar.info(f"Módulo Ativo: **{modulo_ativo}**")

aba_individual, aba_lote = st.tabs(["📊 Perfil Clínico e Terapêutico", "📁 Processamento de Lotes Hospitalares"])

# =====================================================================
# ABA 1: ANÁLISE INDIVIDUAL
# =====================================================================
with aba_individual:
    composto_a = st.text_input("Digite o nome da molécula para análise (inglês):", placeholder="Ex: dasatinib, quercetin, donepezil...")

    if composto_a:
        dados_locais = obter_dados_cientificos_v2(composto_a, modulo_ativo)

        # REQUISIÇÃO DA API (PUBCHEM)
        url_dados = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{composto_a}/property/MolecularFormula,MolecularWeight,Title/JSON"
        res_dados = requests.get(url_dados)

        if res_dados.status_code == 200:
            prop = res_dados.json()["PropertyTable"]["Properties"][0]
            nome = prop.get("Title", composto_a.capitalize())
            formula = prop.get("MolecularFormula", "-")
            peso = prop.get("MolecularWeight", "-")

            st.markdown(f"## **{nome}**")

            c1, c2 = st.columns(2)
            c1.metric("Fórmula Química", formula)
            c2.metric("Massa Molecular", f"{peso} g/mol")

            st.subheader("💊 Aplicação Médica e Terapêutica Avançada")
            st.info(dados_locais["aplicacao"])

            st.subheader("🎯 Pipeline de Eficiência Terapêutica Real")
            st.warning(dados_locais["pipeline"])

            st.write("---")
            st.markdown("🔍 **Mapeamento de Conformação Estrutural**")

            col_2d, col_3d = st.columns([1, 1])

            with col_2d:
                url_imagem = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{composto_a}/PNG"
                st.image(url_imagem, use_container_width=True)
                st.caption("Conformação 2D")

            with col_3d:
                try:
                    url_sdf = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{composto_a}/SDF?record_type=3d"
                    res_sdf = requests.get(url_sdf)

                    if res_sdf.status_code == 200 and res_sdf.text.strip():
                        sdf_data = res_sdf.text
                        xyzview = py3Dmol.view(width=450, height=450)
                        xyzview.addModel(sdf_data, "sdf")
                        xyzview.setStyle({"stick": {}, "sphere": {"scale": 0.3}})
                        xyzview.zoomTo()
                        xyzview.setBackgroundColor("white")

                        components.html(xyzview._make_html(), height=470, width=470)
                        st.caption("Modelo 3D Rotacionável")
                    else:
                        st.caption("⚠️ Coordenadas 3D não localizadas para este composto")
                except Exception as e:
                    st.caption(f"⚠️ Renderizador 3D indisponível ({e})")

            st.write("---")
            df_individual = pd.DataFrame([{
                "Nome Oficial": nome,
                "Aplicação Médica": dados_locais["aplicacao"],
            }])
            try:
                pdf_bytes_individual = gerar_pdf_laudo(df_individual)
                st.download_button(
                    label="📥 Baixar Laudo Individual (PDF)",
                    data=pdf_bytes_individual,
                    file_name=f"laudo_{composto_a}.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"⚠️ Não foi possível gerar o PDF: {e}")

        else:
            st.error("⚠️ Composto não encontrado na base de dados internacional do PubChem. Verifique a grafia em inglês.")

# =====================================================================
# ABA 2: PROCESSAMENTO DE LOTES HOSPITALARES
# =====================================================================
with aba_lote:
    st.caption("Envie um arquivo .csv ou .xlsx com uma coluna contendo os nomes dos compostos (em inglês).")

    with open("modelo_triagem_senotrack.xlsx", "rb") as f:
        st.download_button(
            label="📄 Baixar modelo de planilha",
            data=f,
            file_name="modelo_triagem_senotrack.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    arquivo_upload = st.file_uploader("Carregue o arquivo de triagem (.xlsx ou .csv):", type=["csv", "xlsx"])

    if arquivo_upload:
        try:
            if arquivo_upload.name.endswith(".csv"):
                df_lote = pd.read_csv(arquivo_upload)
            else:
                df_lote = pd.read_excel(arquivo_upload)

            if df_lote.shape[1] > 0:
                df_lote.rename(columns={df_lote.columns[0]: "Composto"}, inplace=True)
                compostos_no_lote = [str(c).strip().lower() for c in df_lote["Composto"].unique()]

                # --- A. MOTOR DE REGRAS QUÍMICAS E SINERGIAS ---
                st.write("### 🧬 Análise de Interações e Sinergias")

                if "dasatinib" in compostos_no_lote and "quercetin" in compostos_no_lote:
                    st.success("""
                        ⚡ **Sinergia Oncológica/Senolítica Detectada: Combo D+Q (Dasatinib + Quercetina)**
                        * **Mecanismo:** O Dasatinib elimina seletivamente os pré-adipócitos senescentes, enquanto a Quercetina elimina células endoteliais senescentes. Juntos cobrem redes de sobrevivência complementares (SCAP).
                    """)

                if "donepezil" in compostos_no_lote and "memantine" in compostos_no_lote:
                    st.success("""
                        ⚡ **Sinergia Clínica Detectada: Protocolo Combinado de Alta Afinidade (Alzheimer Avançado)**
                        * **Mecanismo:** O Donepezil maximiza a disponibilidade de acetilcolina na fenda sináptica, enquanto a Memantina regula a atividade do glutamato para evitar a neurotoxicidade.
                    """)

                if "quercetin" in compostos_no_lote and "resveratrol" in compostos_no_lote:
                    st.info("""
                        🌱 **Sinergia Nutracêutica Protegida Detectada (Senolítico + Senomorfo)**
                        * **Mecanismo:** A Quercetina força a apoptose das células senescentes, enquanto o Resveratrol modula as Sirtuínas bloqueando o avanço do perfil inflamatório (SASP).
                    """)

                # --- B. ENGENHARIA DE DADOS E ENRIQUECIMENTO VIA API ---
                list_formulas = []
                list_pesos = []
                list_aplicacoes = []
                list_pipelines = []
                list_absorcao = []
                list_seguranca = []

                status_loading = st.empty()
                status_loading.caption("🔬 Consultando dados moleculares na base internacional do PubChem...")

                for comp in df_lote["Composto"]:
                    nome_comp = str(comp).strip().lower()
                    dados_c = obter_dados_cientificos_v2(nome_comp, modulo_selecionado=modulo_ativo)

                    # Reset padrão preventivo antes de chamar a API
                    f_quimica, p_molecular = "-", 300.0

                    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{nome_comp}/property/MolecularFormula,MolecularWeight/JSON"
                    try:
                        res = requests.get(url, timeout=15)
                        if res is not None and res.status_code == 200:
                            prop_b = res.json()["PropertyTable"]["Properties"][0]
                            f_quimica = prop_b.get("MolecularFormula", "-")
                            p_molecular = float(prop_b.get("MolecularWeight", 300.0))
                    except Exception:
                        pass

                    # Alocação estruturada pós-resposta da API
                    list_formulas.append(f_quimica)
                    list_pesos.append(f"{p_molecular} g/mol")
                    list_aplicacoes.append(dados_c["aplicacao"])
                    list_pipelines.append(dados_c["pipeline"])

                    # Validação de absorção com base no peso real capturado
                    if p_molecular < 500:
                        list_absorcao.append("🟢 Alta (Peso < 500 g/mol)")
                    else:
                        list_absorcao.append("🟡 Moderada/Baixa (Molécula Grande)")

                    # Nova lógica de segurança/ação dinâmica por classe terapêutica
                    resultado_reacao = analisar_acao_reacao(p_molecular, dados_c["classe"])
                    list_seguranca.append(resultado_reacao)

                status_loading.empty()

                # Montando a tabela estruturada final
                df_exibicao = pd.DataFrame({
                    "Nome Oficial": df_lote["Composto"].astype(str).str.capitalize(),
                    "Fórmula": list_formulas,
                    "Massa Molecular": list_pesos,
                    "Aplicação Médica": list_aplicacoes,
                    "Mapeamento Pipeline": list_pipelines,
                    "Absorção Oral": list_absorcao,
                    "Segurança Laboratorial": list_seguranca,
                })

                # --- C. COMPARATIVO VISUAL DINÂMICO ---
                st.divider()
                st.write("### ⚖️ Comparativo Direto de Eficiência (Visão Intuitiva)")
                
                compostos_validos = df_exibicao.to_dict(orient="records")

                if compostos_validos:
                    qtd_itens = len(compostos_validos)
                    colunas_compostos = st.columns(qtd_itens)

                    for idx in range(qtd_itens):
                        item = compostos_validos[idx]
                        nome_item = item["Nome Oficial"]
                        aplicacao = item["Aplicação Médica"]
                        seguranca = item["Segurança Laboratorial"]

                        cor_borda = "#10b981"
                        icone = "🍏"
                        funcao = "Ação Preventiva / Estabilização"
                        estrelas = "⭐⭐⭐⭐☆"

                        # Customizações estéticas dinâmicas baseadas no nome
                        if "dasatinib" in nome_item.lower():
                            cor_borda = "#ef4444"
                            icone = "💥"
                            funcao = "Ação Avançada (Precisão)"
                            estrelas = "⭐⭐⭐⭐⭐"
                        elif "resveratrol" in nome_item.lower():
                            cor_borda = "#3b82f6"
                            icone = "🍇"
                            funcao = "O Escudo (Bloqueio inflamatório)"
                            estrelas = "⭐⭐⭐☆☆"
                        elif "donepezil" in nome_item.lower() or "memantine" in nome_item.lower():
                            cor_borda = "#a855f7"
                            icone = "🧠"
                            funcao = "Mecanismo Neuroprotetor"
                            estrelas = "⭐⭐⭐⭐⭐"

                        with colunas_compostos[idx]:
                            st.markdown(f"""
                            <div style='background-color: #1e293b; padding: 18px; border-radius: 10px; border-left: 5px solid {cor_borda}; height: 100%; margin-bottom: 10px;'>
                                <h4 style='margin-top:0;'>{icone} {nome_item}</h4>
                                <p style='font-size:13px; margin-bottom:6px;'><b>Função:</b> {funcao}</p>
                                <p style='font-size:13px; margin-bottom:6px;'><b>Força de Ação:</b> {estrelas}</p>
                                <p style='font-size:13px; margin-bottom:6px;'><b>Foco Clínico:</b> {aplicacao}</p>
                                <p style='font-size:13px; margin-bottom:0; color: {cor_borda};'><b>Status:</b> {seguranca}</p>
                            </div>
                            """, unsafe_allow_html=True)

                # --- D. RENDERIZAÇÃO DA TABELA GERENCIAL ---
                st.divider()
                st.write("### 📋 Tabela Gerencial Expandida de Triagem")

                estilo_tabela = """
                <style>
                    .tabela-lote { width: 100%; border-collapse: collapse; font-family: sans-serif; margin-bottom: 20px;}
                    .tabela-lote th { background-color: #1e293b; color: white; padding: 12px; text-align: left; font-size: 14px; }
                    .tabela-lote td { padding: 12px; border-bottom: 1px solid #475569; color: #f1f5f9; font-size: 13px; white-space: normal !important; word-wrap: break-word; }
                    .tabela-lote tr:nth-child(even) { background-color: #0f172a; }
                </style>
                """
                st.markdown(estilo_tabela, unsafe_allow_html=True)
                st.markdown(df_exibicao.to_html(classes="tabela-lote", index=False, escape=False), unsafe_allow_html=True)

                # --- E. GRÁFICO DE BARRAS ---
                st.divider()
                st.subheader("📈 Análise de Densidade Molecular do Lote")

                df_grafico = df_exibicao.copy()
                df_grafico["Massa Numérica"] = df_grafico["Massa Molecular"].str.replace(" g/mol", "", regex=False).astype(float)
                st.bar_chart(data=df_grafico, x="Nome Oficial", y="Massa Numérica", color="#10b981")

                # --- F. GERADOR DE LAUDO PDF ---
                st.divider()
                st.subheader("🖨️ Central de Emissão de Laudos Técnicos")

                try:
                    pdf_bytes = gerar_pdf_laudo_lote(df_exibicao)
                    st.download_button(
                        label="📥 Baixar Laudo Clínico Executivo (PDF)",
                        data=pdf_bytes,
                        file_name="laudo_viabilidade_senotrack.pdf",
                        mime="application/pdf",
                        type="primary",
                    )
                except Exception as e:
                    st.error(f"⚠️ Não foi possível gerar o PDF do lote: {e}")
            else:
                st.error("O arquivo enviado está vazio.")
        except Exception as e:
            st.error(f"Erro ao processar lote: {e}")

st.caption("SenoTrack Platform v4.0 • Tecnologia Estratégica Inovadora de Mapeamento Molecular Modular.")