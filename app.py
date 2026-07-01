import streamlit as st
import requests
import pandas as pd
import os
from fpdf import FPDF
import py3Dmol
from stmol import showmol


# Configuração da página - Tema profissional e amplo
st.set_page_config(page_title="SenoTrack Enterprise", page_icon="🔬", layout="wide")


# --- FUNÇÃO AUXILIAR: SANITIZAÇÃO DE TEXTO PARA O PDF ---
# A fonte padrão do FPDF (Helvetica) só suporta caracteres latin-1.
# Emojis e outros símbolos unicode quebram a geração do PDF, então
# removemos qualquer caractere fora desse conjunto antes de escrever.
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

    # fpdf2 já retorna um bytearray pronto para uso em st.download_button
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


# --- BASE DE CONHECIMENTO CIENTÍFICO AVANÇADO (SenoTrack Deep Intelligence) ---
DADOS_AVANCADOS_SENOLITICOS = {
    "quercetin": {
        "aplicacao": "Flavonoide natural exógeno amplamente mapeado por sua capacidade de inibir a via de sobrevivência PI3K/AKT, induzindo seletivamente a apoptose em células senescentes. Quando administrado em protocolos combinados de pulso biológico, atua de forma sinérgica na depuração de células endoteliais senescentes e células progenitoras adiposas humanas, resultando em uma redução drástica na secreção do Fenótipo Secretor Associado à Senescência (SASP), mitigando a inflamação crônica sistêmica e preservando a integridade tecidual adjacente.",
        "pipeline": "Atualmente posicionado em Fase II de Ensaios Clínicos Translacionais. Estudos robustos conduzidos por consórcios de longevidade celular (como a Mayo Clinic) validaram sua eficácia na redução da carga inflamatória em tecidos de pacientes com fibrose idiopática e nefropatia diabética. As principais barreiras de engenharia farmacêutica envolvem sua baixa biodisponibilidade oral crônica e rápida taxa de depuração metabólica hepática, impulsionando o desenvolvimento de formulações inovadoras baseadas em matrizes lipossomais e cocristalização molecular.",
        "medicamentos": "Suplementos Clínicos, Combo D+Q (Dasatinib + Quercetina).",
    },
    "dasatinib": {
        "aplicacao": "Potente inibidor de tirosina quinase multicatalítico, originalmente aprovado para interventions oncológicas de alta precisão. No escopo da medicina da longevidade, atua desregulando as redes de sinalização pró-sobrevivência das células senescentes (redes efrina/ephrin). Sua principal assinatura farmacológica é a eliminação direcionada de pré-adipócitos humanos senescentes, promovendo uma varredura celular profunda através do mecanismo conhecido como dosagem intermitente 'hit-and-run', que minimiza a exposição sistêmica crônica.",
        "pipeline": "Mapeado na transição estratégica entre aplicações oncológicas convencionais e protocolos clínicos de rejuvenescimento celular. O composto enfrenta rigorosa validação regulatória devido ao perfil de toxicidade residual (como risco de mielossupressão intermitente). Os pipelines científicos de ponta estão focados no refinamento de janelas posológicas ultraprecisas e na triagem de novos análogos sintéticos com janelas de segurança biológica significativamente expandidas para uso preventivo.",
        "medicamentos": "Sprycel (Aprovado para Leucemia), Combo D+Q.",
    },
    "navitoclax": {
        "aplicacao": "Inibidor sintético de alta afinidade projetado para interagir diretamente com os domínios BH3 das proteínas pró-sobrevivência BCL-2 e BCL-xL. Ao suprimir esses eixos antiapoptóticos chaves, o composto reativa os caminhos de morte celular programada intrínseca especificamente em linhagens celulares senescentes profundas de tecidos humanos, limpando o microambiente com eficiência celular cirúrgica.",
        "pipeline": "Posicionado em janelas de validação clínica oncológica e pré-clínica avançada de extensão de saúde. O maior desafio disruptivo reside no controle dos efeitos colaterais severos periféricos, destacando-se a destruição induzida de plaquetas saudáveis (trombocitopenia aguda). Pesquisas atuais buscam o desenvolvimento de pró-fármacos galênicos ou anticorpos conjugados (ADCs) direcionados para blindar a integridade sanguínea.",
        "medicamentos": "ABT-263 (Composto de Investigação Clínica).",
    },
    "fisetin": {
        "aplicacao": "Polifenol flavonoide natural de alta especificidade senolítica, documentado por modular negativamente vias de sobrevivência celular dependentes de senescência, como as redes NF-kB. Exibe um dos maiores perfis de segurança biológica celular conhecidos, agindo de forma intermitente para reduzir a transcrição e liberação massiva do coquetel de citocinas citotóxicas e quimiocinas degradantes que compõem o ecossistema inflamatório SASP.",
        "pipeline": "Fase II de estudos translacionais em humanos focados em inflamação crônica relacionada à senescência tecidual sistêmica. O composto esbarra em limitações estruturais de biodisponibilidade por sua hidrofobicidade nativa. Projetos de vanguarda biofarmacêutica priorizam a nanoencapsulação lipídica e veículos micelares estáveis para otimização farmacocinética in vivo.",
        "medicamentos": "Formulações lipossomais de Longevidade, Protocolos Clínicos de Pulso.",
    },
    "resveratrol": {
        "aplicacao": "Composto polifenólico atuante como modulador alostérico das Sirtuínas (especificamente SIRT1) e mimético de restrição calórica. Classificado classicamente como um agente 'senomorfo' de alta performance, ele não induz diretamente a lise celular, mas reprograma epigeneticamente o microambiente tecidual. Sua ação bloqueia a transcrição de citocinas pró-inflamatórias, quimiocinas e metaloproteinases da matriz celular (MMPs), contendo o efeito cascata que danifica células saudáveis vizinhas.",
        "pipeline": "Uso comercial consolidado em escala global como nutracêutico protetor celular de barreira primária. Na triagem gerencial de pipelines clínicos estruturados, o composto enfrenta desafios severos relacionados à sua instabilidade termodinâmica in vivo e baixa solubilidade aquosa. Os esforços de pesquisa e desenvolvimento (P&D) atuais concentram-se na síntese de compostos ativadores de sirtuína sintéticos de segunda geração (STACs), desenhados para mimetizar seus benefícios com estabilidade metabólica ampliada.",
        "medicamentos": "Trans-Resveratrol, Ativadores de Sirtuínas de Mercado.",
    },
}


def obter_dados_cientificos(nome_composto):
    nome_limpo = nome_composto.strip().lower()
    for chave, dados in DADOS_AVANCADOS_SENOLITICOS.items():
        if chave in nome_limpo:
            return dados
    return {
        "aplicacao": f"O composto '{nome_composto.capitalize()}' encontra-se em estágio de triagem molecular primária. Mecanismos específicos de interação com as vias de sinalização pró-sobrevivência SCAP e regulação do fenótipo secretor inflamatório (SASP) estão sob investigação analítica in vitro na atual janela do pipeline.",
        "pipeline": "Status de validação experimental inicial. Ensaios pré-clínicos de citotoxicidade seletiva e mapeamento farmacocinético preliminar agendados para consolidação de dados de bioequivalência e modelagem preditiva de segurança em sistemas humanos.",
        "medicamentos": "Compostos análogos ou em fase de síntese laboratorial de triagem primária.",
    }


# --- GERADOR AUTOMÁTICO DO MODELO EXCEL ---
if not os.path.exists("modelo_triagem_senotrack.xlsx"):
    df_modelo = pd.DataFrame({"Composto": ["quercetin", "dasatinib", "navitoclax", "fisetin", "resveratrol"]})
    df_modelo.to_excel("modelo_triagem_senotrack.xlsx", index=False)

# Interface Principal
st.markdown("<p style='color: #10b981; font-weight: bold; margin-bottom: -10px;'>SENOTRACK ENTERPRISE • BIOTECH DATA</p>", unsafe_allow_html=True)
st.title("🔬 Hub Avançado de Análise Oncológica e Longevidade Celular")
st.markdown("---")

aba_individual, aba_lote = st.tabs(["📊 Perfil Clínico e Terapêutico", "📁 Processamento de Lotes Hospitalares"])

# =====================================================================
# ABA 1: ANÁLISE INDIVIDUAL
# =====================================================================
with aba_individual:
    composto_a = st.text_input("Digite o nome da molécula para análise (inglês):", placeholder="Ex: dasatinib, quercetin, navitoclax...")

    if composto_a:
        dados_locais = obter_dados_cientificos(composto_a)

        # REQUISIÇÃO DA API (PUBCHEM)
        url_dados = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{composto_a}/property/MolecularFormula,MolecularWeight,Title/JSON"
        res_dados = requests.get(url_dados)

        if res_dados.status_code == 200:
            prop = res_dados.json()["PropertyTable"]["Properties"][0]
            nome = prop.get("Title", composto_a.capitalize())
            formula = prop.get("MolecularFormula", "-")
            peso = prop.get("MolecularWeight", "-")

            # --- INTERFACE ---
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

                        showmol(xyzview, height=450, width=450)
                        st.caption("Modelo 3D Rotacionável")
                    else:
                        st.caption("⚠️ Coordenadas 3D não localizadas para este composto")
                except Exception as e:
                    st.caption(f"⚠️ Renderizador 3D indisponível ({e})")

            # --- GERAÇÃO DE PDF (ANÁLISE INDIVIDUAL) ---
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
    st.caption("Envie um arquivo .csv ou .xlsx com uma coluna contendo os nomes dos compostos (em inglês). "
               "Você pode baixar o modelo abaixo como ponto de partida.")

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
            # Lendo o arquivo corretamente (CSV ou Excel)
            if arquivo_upload.name.endswith(".csv"):
                df_lote = pd.read_csv(arquivo_upload)
            else:
                df_lote = pd.read_excel(arquivo_upload)

            if df_lote.shape[1] > 0:
                # Padronizando o nome da primeira coluna para "Composto"
                df_lote.rename(columns={df_lote.columns[0]: "Composto"}, inplace=True)
                compostos_no_lote = [str(c).strip().lower() for c in df_lote["Composto"].unique()]

                # --- A. MOTOR DE REGRAS QUÍMICAS E SINERGIAS ---
                st.write("### 🧬 Análise de Interações e Sinergias")

                if "dasatinib" in compostos_no_lote and "quercetin" in compostos_no_lote:
                    st.success("""
                        ⚡ **Sinergia Oncológica/Senolítica Detectada: Combo D+Q (Dasatinib + Quercetina)**
                        * **Mecanismo:** O Dasatinib elimina seletivamente os pré-adipócitos senescentes, enquanto a Quercetina elimina células endoteliais senescentes. Juntos, cobrem redes de sobrevivência complementares (SCAP), multiplicando a eficácia da depuração celular in vivo.
                        * **Status Clínico:** Altamente referenciado em ensaios clínicos da Mayo Clinic para reversão de fragilidade biológica.
                    """)

                if "quercetin" in compostos_no_lote and "resveratrol" in compostos_no_lote:
                    st.info("""
                        🌱 **Sinergia Nutracêutica Protegida Detectada (Senolítico + Senomorfo)**
                        * **Mecanismo:** A Quercetina atua forçando a apoptose das células em estado de senescência crônica. O Resveratrol entra como modulador alostérico (SIRT1), bloqueando o SASP (fenótipo inflamatório) para que as células saudáveis ao redor não sejam contaminadas pelo estresse oxidativo.
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

                    dados_c = obter_dados_cientificos(nome_comp)

                    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{nome_comp}/property/MolecularFormula,MolecularWeight/JSON"
                    try:
                        res = requests.get(url, timeout=15)
                    except requests.RequestException:
                        res = None

                    f_quimica, p_molecular = "-", 300.0
                    if res is not None and res.status_code == 200:
                        try:
                            prop_b = res.json()["PropertyTable"]["Properties"][0]
                            f_quimica = prop_b.get("MolecularFormula", "-")
                            p_molecular = float(prop_b.get("MolecularWeight", 300.0))
                        except Exception:
                            pass

                    list_formulas.append(f_quimica)
                    list_pesos.append(f"{p_molecular} g/mol")
                    list_aplicacoes.append(dados_c["aplicacao"])
                    list_pipelines.append(dados_c["pipeline"])

                    # Regra intuitiva de Absorção
                    if p_molecular < 500:
                        list_absorcao.append("🟢 Alta (Peso < 500 g/mol)")
                    else:
                        list_absorcao.append("🟡 Moderada/Baixa (Molécula Grande)")

                    # Regras de Segurança Laboratorial
                    if "dasatinib" in nome_comp:
                        list_seguranca.append("⚠️ Risco Moderado: Requer dosagem intermitente (Hit-and-Run)")
                    elif "quercetin" in nome_comp or "resveratrol" in nome_comp or "fisetin" in nome_comp:
                        list_seguranca.append("✅ Perfil Seguro: Baixa toxicidade sistêmica observada")
                    else:
                        list_seguranca.append("🔍 Fase de mapeamento de toxicidade in vitro")

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

                # =========================================================
                # COMPARATIVO VISUAL 100% DINÂMICO (VÁRIOS ITENS)
                # =========================================================
                st.divider()
                st.write("### ⚖️ Comparativo Direto de Eficiência (Visão Intuitiva)")
                st.caption("Resumo simplificado para tomada de decisão rápida, ideal para triagem não técnica.")

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
                        funcao = "Ação Preventiva / Varredura Celular"
                        estrelas = "⭐⭐⭐⭐☆"

                        if "dasatinib" in nome_item.lower():
                            cor_borda = "#ef4444"
                            icone = "💥"
                            funcao = "Ação Avançada (Precisão Clínica)"
                            estrelas = "⭐⭐⭐⭐⭐"
                        elif "resveratrol" in nome_item.lower():
                            cor_borda = "#3b82f6"
                            icone = "🍇"
                            funcao = "O Escudo (Bloqueio de Inflamação)"
                            estrelas = "⭐⭐⭐☆☆"

                        with colunas_compostos[idx]:
                            st.markdown(f"""
                            <div style='background-color: #1e293b; padding: 18px; border-radius: 10px; border-left: 5px solid {cor_borda}; height: 100%; margin-bottom: 10px;'>
                                <h4 style='margin-top:0;'>{icone} {nome_item}</h4>
                                <p style='font-size:13px; margin-bottom:6px;'><b>Função:</b> {funcao}</p>
                                <p style='font-size:13px; margin-bottom:6px;'><b>Força de Ação:</b> {estrelas}</p>
                                <p style='font-size:13px; margin-bottom:6px;'><b>Foco Clínico:</b> {aplicacao}</p>
                                <p style='font-size:13px; margin-bottom:0; color: {cor_borda};'><b>Segurança:</b> {seguranca}</p>
                            </div>
                            """, unsafe_allow_html=True)

                    st.markdown("""
                    <div style='background-color: #0f172a; padding: 15px; border-radius: 8px; margin-top: 15px; border: 1px dashed #475569;'>
                        💡 <b>Diretriz Global de Triagem:</b> Esta visualização foi desenhada para facilitar análises rápidas. Itens marcados com 💥 representam intervenções críticas de pipeline, enquanto 🍏 e 🍇 representam estabilizadores metabólicos secundários.
                    </div>
                    """, unsafe_allow_html=True)

                # --- C. RENDERIZAÇÃO DA TABELA GERENCIAL EM HTML ---
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

                # --- D. GRÁFICO DE BARRAS ---
                st.divider()
                st.subheader("📈 Análise de Densidade Molecular do Lote")

                df_grafico = df_exibicao.copy()
                df_grafico["Massa Numérica"] = df_grafico["Massa Molecular"].str.replace(" g/mol", "", regex=False).astype(float)
                st.bar_chart(data=df_grafico, x="Nome Oficial", y="Massa Numérica", color="#10b981")

                # --- E. GERADOR DE LAUDO PDF ---
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

st.caption("SenoTrack Platform v3.5 • Tecnologia Estratégica Inovadora de Longevidade Celular.")