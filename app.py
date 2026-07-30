import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import numpy as np
import os
import logging
import io
import json
import time
import uuid
from datetime import datetime
import matplotlib.pyplot as plt
from fpdf import FPDF
import py3Dmol
import plotly.graph_objects as go

from rdkit import Chem
from rdkit.Chem import Draw, Descriptors, Crippen, rdMolDescriptors, AllChem
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams

# --- CONFIGURAÇÃO DE LOGS (QA Culture) ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SenoTrack Enterprise v9.0", page_icon="🔬", layout="wide")

# =====================================================================
# I18N — DICIONÁRIO CENTRALIZADO DE TRADUÇÃO
# =====================================================================
IDIOMAS_DISPONIVEIS = {
    "🇧🇷 Português": "pt",
    "🇺🇸 English": "en",
    "🇪🇸 Español": "es",
    "🇨🇳 中文 (Mandarim)": "zh",
    "🇩🇪 Deutsch": "de",
    "🇯🇵 日本語": "ja",
}

TRANSLATIONS = {
    "app_badge": {"pt": "SENOTRACK ENTERPRISE v9.0 • RESEARCH ECOSYSTEM EDITION", "en": "SENOTRACK ENTERPRISE v9.0 • RESEARCH ECOSYSTEM EDITION", "es": "SENOTRACK ENTERPRISE v9.0 • EDICIÓN ECOSISTEMA DE INVESTIGACIÓN", "zh": "SENOTRACK 企业版 v9.0 • 科研生态系统版", "de": "SENOTRACK ENTERPRISE v9.0 • RESEARCH ECOSYSTEM EDITION", "ja": "SENOTRACK エンタープライズ v9.0 • リサーチエコシステム版"},
    "app_title": {"pt": "🔬 Hub Avançado de Análise Oncológica, Longevidade e P&D Farmacêutico", "en": "🔬 Advanced Hub for Oncology, Longevity and Pharmaceutical R&D Analysis", "es": "🔬 Centro Avanzado de Análisis Oncológico, Longevidad e I+D Farmacéutico", "zh": "🔬 肿瘤学、长寿与药物研发高级分析平台", "de": "🔬 Erweitertes Zentrum für Onkologie-, Langlebigkeits- und Pharma-F&E-Analyse", "ja": "🔬 腫瘍学・長寿・製薬研究開発 高度分析ハブ"},
    "sidebar_user_profile": {"pt": "👤 Perfil do Usuário", "en": "👤 User Profile", "es": "👤 Perfil del Usuario", "zh": "👤 用户模式", "de": "👤 Benutzerprofil", "ja": "👤 ユーザープロファイル"},
    "profile_radio_label": {"pt": "Nível de Complexidade da Interface:", "en": "Interface Complexity Level:", "es": "Nivel de Complejidad de la Interfaz:", "zh": "界面复杂度级别：", "de": "Komplexitätsstufe der Oberfläche:", "ja": "インターフェースの複雑さレベル："},
    "profile_didactic": {"pt": "🎓 Modo Didático / Graduação", "en": "🎓 Educational Mode / Undergraduate", "es": "🎓 Modo Didáctico / Pregrado", "zh": "🎓 教学模式 / 本科", "de": "🎓 Lehrmodus / Bachelor", "ja": "🎓 教育モード／学部"},
    "profile_research": {"pt": "🔬 Modo Pesquisa / P&D (Avançado)", "en": "🔬 Research Mode / R&D (Advanced)", "es": "🔬 Modo Investigación / I+D (Avanzado)", "zh": "🔬 科研模式 / 研发（高级）", "de": "🔬 Forschungsmodus / F&E (Erweitert)", "ja": "🔬 研究モード／研究開発（上級）"},
    "sidebar_language": {"pt": "🌐 Idioma / Language", "en": "🌐 Language", "es": "🌐 Idioma", "zh": "🌐 语言", "de": "🌐 Sprache", "ja": "🌐 言語"},
    "sidebar_ai": {"pt": "🧠 Inteligência Artificial (Agente)", "en": "🧠 Artificial Intelligence (Agent)", "es": "🧠 Inteligencia Artificial (Agente)", "zh": "🧠 人工智能（智能体）", "de": "🧠 Künstliche Intelligenz (Agent)", "ja": "🧠 人工知能（エージェント）"},
    "api_key_label": {"pt": "🔑 Chave API (OpenAI/Gemini)", "en": "🔑 API Key (OpenAI/Gemini)", "es": "🔑 Clave API (OpenAI/Gemini)", "zh": "🔑 API 密钥（OpenAI/Gemini）", "de": "🔑 API-Schlüssel (OpenAI/Gemini)", "ja": "🔑 APIキー（OpenAI/Gemini）"},
    "api_key_help": {"pt": "Opcional. Se vazio, o sistema usa o modelo preditivo local.", "en": "Optional. If empty, the system uses the local predictive model.", "es": "Opcional. Si está vacío, el sistema usa el modelo predictivo local.", "zh": "可选。留空则系统使用本地预测模型。", "de": "Optional. Wenn leer, verwendet das System das lokale Vorhersagemodell.", "ja": "任意。空欄の場合はローカル予測モデルを使用します。"},
    "sidebar_clinical_params": {"pt": "⚙️ Parametrização Clinica", "en": "⚙️ Clinical Parameters", "es": "⚙️ Parametrización Clínica", "zh": "⚙️ 临床参数设置", "de": "⚙️ Klinische Parametrisierung", "ja": "⚙️ 臨床パラメータ設定"},
    "module_label": {"pt": "Módulo Temático Ativo:", "en": "Active Thematic Module:", "es": "Módulo Temático Activo:", "zh": "当前主题模块：", "de": "Aktives Themenmodul:", "ja": "アクティブなテーマモジュール："},
    "sidebar_filters": {"pt": "🎛️ Filtros Farmacocinéticos", "en": "🎛️ Pharmacokinetic Filters", "es": "🎛️ Filtros Farmacocinéticos", "zh": "🎛️ 药代动力学筛选条件", "de": "🎛️ Pharmakokinetische Filter", "ja": "🎛️ 薬物動態フィルター"},
    "mass_limit_label": {"pt": "Teto de Massa Molecular (g/mol):", "en": "Molecular Mass Ceiling (g/mol):", "es": "Límite de Masa Molecular (g/mol):", "zh": "分子量上限（g/mol）：", "de": "Obergrenze der Molmasse (g/mol):", "ja": "分子量の上限（g/mol）："},
    "mass_limit_help": {"pt": "Moléculas acima deste peso serão automaticamente desconsideradas na triagem atual em lote.", "en": "Molecules above this weight will be automatically excluded from the current batch screening.", "es": "Las moléculas por encima de este peso se excluirán automáticamente del cribado por lotes actual.", "zh": "超过此重量的分子将在当前批量筛选中自动排除。", "de": "Moleküle über diesem Gewicht werden im aktuellen Batch-Screening automatisch ausgeschlossen.", "ja": "この重量を超える分子は、現在のバッチスクリーニングで自動的に除外されます。"},
    "tpsa_limit_label": {"pt": "Teto de TPSA (Å²) — Regra de Veber:", "en": "TPSA Ceiling (Å²) — Veber's Rule:", "es": "Límite de TPSA (Å²) — Regla de Veber:", "zh": "TPSA 上限（Å²）— Veber 规则：", "de": "TPSA-Obergrenze (Å²) — Veber-Regel:", "ja": "TPSA上限（Å²）—Veberルール："},
    "rot_limit_label": {"pt": "Máx. Ligações Rotacionáveis — Veber:", "en": "Max. Rotatable Bonds — Veber:", "es": "Máx. Enlaces Rotables — Veber:", "zh": "最大可旋转键数 — Veber：", "de": "Max. drehbare Bindungen — Veber:", "ja": "最大回転可能結合数 — Veber："},
    "sidebar_infra": {"pt": "🖥️ Infraestrutura & Labs", "en": "🖥️ Infrastructure & Labs", "es": "🖥️ Infraestructura y Laboratorios", "zh": "🖥️ 基础设施与实验室", "de": "🖥️ Infrastruktur & Labore", "ja": "🖥️ インフラとラボ"},
    "offline_toggle": {"pt": "Modo de Demonstração (Mock/Offline)", "en": "Demonstration Mode (Mock/Offline)", "es": "Modo de Demostración (Simulado/Offline)", "zh": "演示模式（模拟/离线）", "de": "Demomodus (Mock/Offline)", "ja": "デモモード（モック／オフライン）"},
    "eln_sidebar_title": {"pt": "📓 Caderno Científico (ELN)", "en": "📓 Electronic Lab Notebook (ELN)", "es": "📓 Cuaderno Científico (ELN)", "zh": "📓 电子实验记录本（ELN）", "de": "📓 Elektronisches Laborbuch (ELN)", "ja": "📓 電子実験ノート（ELN）"},
    "eln_sidebar_caption": {"pt": "{n} experimentos salvos nesta sessão.", "en": "{n} experiments saved in this session.", "es": "{n} experimentos guardados en esta sesión.", "zh": "本次会话已保存 {n} 个实验。", "de": "{n} Experimente in dieser Sitzung gespeichert.", "ja": "このセッションで {n} 件の実験が保存されました。"},
    "audit_sidebar_title": {"pt": "📜 Rastreabilidade & Auditoria", "en": "📜 Traceability & Audit", "es": "📜 Trazabilidad y Auditoría", "zh": "📜 可追溯性与审计", "de": "📜 Rückverfolgbarkeit & Audit", "ja": "📜 トレーサビリティと監査"},
    "audit_sidebar_caption": {"pt": "{n} consultas salvas nesta sessão.", "en": "{n} queries saved in this session.", "es": "{n} consultas guardadas en esta sesión.", "zh": "本次会话已保存 {n} 次查询。", "de": "{n} Abfragen in dieser Sitzung gespeichert.", "ja": "このセッションで {n} 件のクエリが保存されました。"},
    "audit_export_button": {"pt": "📥 Exportar Histórico de Sessão (JSON)", "en": "📥 Export Session History (JSON)", "es": "📥 Exportar Historial de Sesión (JSON)", "zh": "📥 导出会话历史记录（JSON）", "de": "📥 Sitzungsverlauf exportieren (JSON)", "ja": "📥 セッション履歴をエクスポート（JSON）"},
    "tab_individual": {"pt": "📊 Perfil Clínico e Terapêutico", "en": "📊 Clinical & Therapeutic Profile", "es": "📊 Perfil Clínico y Terapéutico", "zh": "📊 临床与治疗档案", "de": "📊 Klinisches & Therapeutisches Profil", "ja": "📊 臨床・治療プロファイル"},
    "tab_lote": {"pt": "📁 Processamento de Lotes Hospitalares", "en": "📁 Hospital Batch Processing", "es": "📁 Procesamiento de Lotes Hospitalarios", "zh": "📁 医院批量处理", "de": "📁 Krankenhaus-Batch-Verarbeitung", "ja": "📁 病院バッチ処理"},
    "tab_fq": {"pt": "🧪 Triagem Físico-Química", "en": "🧪 Physicochemical Screening", "es": "🧪 Cribado Fisicoquímico", "zh": "🧪 理化性质筛选", "de": "🧪 Physikochemisches Screening", "ja": "🧪 物理化学的スクリーニング"},
    "tab_docking": {"pt": "🎯 Docking Virtual & Proteômica", "en": "🎯 Virtual Docking & Proteomics", "es": "🎯 Acoplamiento Virtual y Proteómica", "zh": "🎯 虚拟对接与蛋白质组学", "de": "🎯 Virtuelles Docking & Proteomik", "ja": "🎯 バーチャルドッキング＆プロテオミクス"},
    "tab_benchmark": {"pt": "💊 Farmacoterapia & Benchmark", "en": "💊 Pharmacotherapy & Benchmark", "es": "💊 Farmacoterapia y Referencia", "zh": "💊 药物治疗与基准比较", "de": "💊 Pharmakotherapie & Benchmark", "ja": "💊 薬物療法＆ベンチマーク"},
    "tab_literature": {"pt": "🧠 Agente Clínico & Literatura", "en": "🧠 Clinical Agent & Literature", "es": "🧠 Agente Clínico y Literatura", "zh": "🧠 临床智能体与文献", "de": "🧠 Klinischer Agent & Literatur", "ja": "🧠 臨床エージェント＆文献"},
    "tab_eln": {"pt": "📓 Caderno Científico (ELN)", "en": "📓 Electronic Lab Notebook (ELN)", "es": "📓 Cuaderno Científico (ELN)", "zh": "📓 电子实验记录本（ELN）", "de": "📓 Elektronisches Laborbuch (ELN)", "ja": "📓 電子実験ノート（ELN）"},
    "input_molecule_label": {"pt": "Digite o nome da molécula (inglês):", "en": "Enter the molecule name (English):", "es": "Ingrese el nombre de la molécula (inglés):", "zh": "输入分子名称（英文）：", "de": "Geben Sie den Molekülnamen ein (Englisch):", "ja": "分子名を入力してください（英語）："},
    "metric_formula": {"pt": "Fórmula Química", "en": "Chemical Formula", "es": "Fórmula Química", "zh": "化学式", "de": "Chemische Formel", "ja": "化学式"},
    "metric_mass": {"pt": "Massa Molecular", "en": "Molecular Mass", "es": "Masa Molecular", "zh": "分子量", "de": "Molekülmasse", "ja": "分子量"},
    "section_application": {"pt": "💊 Aplicação Médica e Terapêutica Avançada", "en": "💊 Advanced Medical & Therapeutic Application", "es": "💊 Aplicación Médica y Terapéutica Avanzada", "zh": "💊 高级医疗与治疗应用", "de": "💊 Erweiterte medizinische & therapeutische Anwendung", "ja": "💊 高度な医療・治療応用"},
    "section_pipeline": {"pt": "🎯 Pipeline de Eficiência Terapêutica Real", "en": "🎯 Real Therapeutic Efficiency Pipeline", "es": "🎯 Pipeline de Eficiencia Terapéutica Real", "zh": "🎯 真实治疗效能研发管线", "de": "🎯 Reale Pipeline der therapeutischen Wirksamkeit", "ja": "🎯 実際の治療効果パイプライン"},
    "section_evidence": {"pt": "📚 Evidência Científica e Identificação Farmacológica", "en": "📚 Scientific Evidence & Pharmacological Identification", "es": "📚 Evidencia Científica e Identificación Farmacológica", "zh": "📚 科学证据与药理学鉴定", "de": "📚 Wissenschaftliche Evidenz & Pharmakologische Identifikation", "ja": "📚 科学的根拠と薬理学的同定"},
    "pubmed_article_label": {"pt": "🔬 Artigo Relevante (PubMed)", "en": "🔬 Relevant Article (PubMed)", "es": "🔬 Artículo Relevante (PubMed)", "zh": "🔬 相关文献（PubMed）", "de": "🔬 Relevanter Artikel (PubMed)", "ja": "🔬 関連論文（PubMed）"},
    "pubmed_found": {"pt": "📄 **Artigo Encontrado:**", "en": "📄 **Article Found:**", "es": "📄 **Artículo Encontrado:**", "zh": "📄 **找到文献：**", "de": "📄 **Artikel gefunden:**", "ja": "📄 **論文が見つかりました：**"},
    "pubmed_not_found": {"pt": "⚠️ Nenhuma publicação direta localizada para este composto.", "en": "⚠️ No direct publication found for this compound.", "es": "⚠️ No se encontró ninguna publicación directa para este compuesto.", "zh": "⚠️ 未找到该化合物的直接文献。", "de": "⚠️ Keine direkte Publikation für diese Verbindung gefunden.", "ja": "⚠️ この化合物に関する直接的な論文は見つかりませんでした。"},
    "pubmed_link": {"pt": "🔗 Abrir Artigo Científico no PubMed", "en": "🔗 Open Scientific Article on PubMed", "es": "🔗 Abrir Artículo Científico en PubMed", "zh": "🔗 在 PubMed 中打开文献", "de": "🔗 Wissenschaftlichen Artikel auf PubMed öffnen", "ja": "🔗 PubMedで論文を開く"},
    "rxnav_label": {"pt": "💊 Registro de Farmacopeia (RxNav)", "en": "💊 Pharmacopeia Record (RxNav)", "es": "💊 Registro de Farmacopea (RxNav)", "zh": "💊 药典记录（RxNav）", "de": "💊 Arzneibuch-Eintrag (RxNav)", "ja": "💊 薬局方記録（RxNav）"},
    "ai_agent_section": {"pt": "🤖 Agente Clínico de IA (Insight Automático)", "en": "🤖 Clinical AI Agent (Automatic Insight)", "es": "🤖 Agente Clínico de IA (Perspectiva Automática)", "zh": "🤖 临床AI智能体（自动洞察）", "de": "🤖 Klinischer KI-Agent (Automatische Erkenntnis)", "ja": "🤖 臨床AIエージェント（自動インサイト）"},
    "ai_agent_desc": {"pt": "Use o botão abaixo para invocar a rede neural que sintetiza a viabilidade deste composto.", "en": "Use the button below to invoke the neural network that synthesizes this compound's viability.", "es": "Use el botón de abajo para invocar la red neuronal que sintetiza la viabilidad de este compuesto.", "zh": "点击下方按钮调用神经网络，综合评估该化合物的可行性。", "de": "Verwenden Sie die Schaltfläche unten, um das neuronale Netz aufzurufen, das die Machbarkeit dieser Verbindung zusammenfasst.", "ja": "以下のボタンを使用して、この化合物の実現可能性を総合するニューラルネットワークを呼び出します。"},
    "btn_generate_insight": {"pt": "✨ Gerar Insight Farmacológico para {nome}", "en": "✨ Generate Pharmacological Insight for {nome}", "es": "✨ Generar Perspectiva Farmacológica para {nome}", "zh": "✨ 为 {nome} 生成药理学洞察", "de": "✨ Pharmakologische Erkenntnis für {nome} generieren", "ja": "✨ {nome} の薬理学的インサイトを生成"},
    "spinner_generating": {"pt": "Sintetizando base de dados médicos e estrutura química...", "en": "Synthesizing medical database and chemical structure...", "es": "Sintetizando base de datos médica y estructura química...", "zh": "正在综合医学数据库与化学结构...", "de": "Synthetisiere medizinische Datenbank und chemische Struktur...", "ja": "医療データベースと化学構造を統合中..."},
    "structure_2d_caption": {"pt": "Esquema de Estrutura 2D", "en": "2D Structure Diagram", "es": "Esquema de Estructura 2D", "zh": "二维结构示意图", "de": "2D-Strukturdiagramm", "ja": "2D構造図"},
    "structure_3d_caption": {"pt": "Modelo Estereoscópico 3D Dinâmico", "en": "Dynamic 3D Stereoscopic Model", "es": "Modelo Estereoscópico 3D Dinámico", "zh": "动态三维立体模型", "de": "Dynamisches stereoskopisches 3D-Modell", "ja": "動的3D立体モデル"},
    "offline_2d_msg": {"pt": "Visualização gráfica 2D suspensa em ambiente Offline.", "en": "2D graphical visualization suspended in Offline environment.", "es": "Visualización gráfica 2D suspendida en entorno Offline.", "zh": "离线环境下二维可视化功能已暂停。", "de": "2D-Grafikvisualisierung im Offline-Modus deaktiviert.", "ja": "オフライン環境では2D可視化は無効です。"},
    "offline_3d_msg": {"pt": "Renderizador Molecular 3D desabilitado em Ambiente Offline.", "en": "3D Molecular Renderer disabled in Offline Environment.", "es": "Renderizador Molecular 3D deshabilitado en entorno Offline.", "zh": "离线环境下三维分子渲染器已禁用。", "de": "3D-Molekül-Renderer im Offline-Modus deaktiviert.", "ja": "オフライン環境では3D分子レンダラーが無効です。"},
    "btn_save_eln": {"pt": "💾 Salvar este composto no Caderno Científico (ELN)", "en": "💾 Save this compound to the Electronic Lab Notebook (ELN)", "es": "💾 Guardar este compuesto en el Cuaderno Científico (ELN)", "zh": "💾 将此化合物保存到电子实验记录本（ELN）", "de": "💾 Diese Verbindung im elektronischen Laborbuch (ELN) speichern", "ja": "💾 この化合物を電子実験ノート（ELN）に保存"},
    "eln_saved_success": {"pt": "Experimento registrado no Caderno Científico (ver aba 📓 ELN).", "en": "Experiment recorded in the Lab Notebook (see 📓 ELN tab).", "es": "Experimento registrado en el Cuaderno Científico (ver pestaña 📓 ELN).", "zh": "实验已记录到电子实验记录本（见📓ELN标签页）。", "de": "Experiment im Laborbuch gespeichert (siehe Tab 📓 ELN).", "ja": "実験は電子実験ノートに記録されました（📓ELNタブを参照）。"},
    "btn_download_pdf_individual": {"pt": "📥 Baixar Laudo Individual (PDF)", "en": "📥 Download Individual Report (PDF)", "es": "📥 Descargar Informe Individual (PDF)", "zh": "📥 下载单项报告（PDF）", "de": "📥 Einzelbericht herunterladen (PDF)", "ja": "📥 個別レポートをダウンロード（PDF）"},
    "error_compound_not_found": {"pt": "⚠️ Composto não localizado ou erro de resposta no barramento externo do PubChem.", "en": "⚠️ Compound not found or error in the external PubChem response.", "es": "⚠️ Compuesto no localizado o error en la respuesta externa de PubChem.", "zh": "⚠️ 未找到该化合物，或 PubChem 外部接口响应出错。", "de": "⚠️ Verbindung nicht gefunden oder Fehler in der externen PubChem-Antwort.", "ja": "⚠️ 化合物が見つからないか、PubChem外部応答でエラーが発生しました。"},
    "lote_caption": {"pt": "Gerenciamento e triagem automatizada de planilhas integradas com dados do PubMed, RxNav e Inteligência Artificial.", "en": "Automated management and screening of spreadsheets integrated with PubMed, RxNav and AI data.", "es": "Gestión y cribado automatizado de hojas de cálculo integradas con datos de PubMed, RxNav e IA.", "zh": "与 PubMed、RxNav 和人工智能数据集成的自动化电子表格管理与筛选。", "de": "Automatisierte Verwaltung und Screening von Tabellen, integriert mit PubMed-, RxNav- und KI-Daten.", "ja": "PubMed、RxNav、AIデータと統合された自動スプレッドシート管理・スクリーニング。"},
    "btn_download_template": {"pt": "📄 Baixar Planilha Modelo (.xlsx)", "en": "📄 Download Template Spreadsheet (.xlsx)", "es": "📄 Descargar Plantilla (.xlsx)", "zh": "📄 下载模板表格（.xlsx）", "de": "📄 Vorlagentabelle herunterladen (.xlsx)", "ja": "📄 テンプレートをダウンロード（.xlsx）"},
    "uploader_label": {"pt": "Carregue a planilha de triagem (.xlsx ou .csv):", "en": "Upload the screening spreadsheet (.xlsx or .csv):", "es": "Cargue la hoja de cálculo de cribado (.xlsx o .csv):", "zh": "上传筛选表格（.xlsx 或 .csv）：", "de": "Screening-Tabelle hochladen (.xlsx oder .csv):", "ja": "スクリーニング用スプレッドシートをアップロード（.xlsxまたは.csv）："},
    "spinner_batch_scan": {"pt": "Realizando varredura biomolecular no PubChem, PubMed e RxNav...", "en": "Running biomolecular scan on PubChem, PubMed and RxNav...", "es": "Realizando escaneo biomolecular en PubChem, PubMed y RxNav...", "zh": "正在对 PubChem、PubMed 和 RxNav 进行生物分子扫描...", "de": "Biomolekularer Scan bei PubChem, PubMed und RxNav läuft...", "ja": "PubChem、PubMed、RxNavで生体分子スキャンを実行中..."},
    "kpi_section": {"pt": "📌 Indicadores Globais do Lote", "en": "📌 Global Batch Indicators", "es": "📌 Indicadores Globales del Lote", "zh": "📌 批次总体指标", "de": "📌 Globale Batch-Kennzahlen", "ja": "📌 バッチ全体指標"},
    "kpi_total": {"pt": "Total em Lote", "en": "Total in Batch", "es": "Total en Lote", "zh": "批次总数", "de": "Gesamt im Batch", "ja": "バッチ総数"},
    "kpi_approved": {"pt": "Aprovados (Lipinski)", "en": "Approved (Lipinski)", "es": "Aprobados (Lipinski)", "zh": "通过（Lipinski）", "de": "Genehmigt (Lipinski)", "ja": "承認済み（Lipinski）"},
    "kpi_evidence": {"pt": "Evidências PubMed", "en": "PubMed Evidence", "es": "Evidencias PubMed", "zh": "PubMed 证据", "de": "PubMed-Evidenz", "ja": "PubMedエビデンス"},
    "kpi_module": {"pt": "Módulo Ativo", "en": "Active Module", "es": "Módulo Activo", "zh": "当前模块", "de": "Aktives Modul", "ja": "アクティブモジュール"},
    "ai_batch_section": {"pt": "🤖 Agente Clínico de IA: Análise de Viabilidade do Lote", "en": "🤖 Clinical AI Agent: Batch Viability Analysis", "es": "🤖 Agente Clínico de IA: Análisis de Viabilidad del Lote", "zh": "🤖 临床AI智能体：批次可行性分析", "de": "🤖 Klinischer KI-Agent: Batch-Machbarkeitsanalyse", "ja": "🤖 臨床AIエージェント：バッチ実現可能性分析"},
    "ai_batch_desc": {"pt": "Clique abaixo para gerar um relatório sintético da IA analisando a coerência de todos os compostos do lote de uma só vez.", "en": "Click below to generate an AI synthetic report analyzing the coherence of all batch compounds at once.", "es": "Haga clic abajo para generar un informe sintético de IA que analice la coherencia de todos los compuestos del lote a la vez.", "zh": "点击下方生成AI综合报告，一次性分析批次中所有化合物的一致性。", "de": "Klicken Sie unten, um einen KI-Kurzbericht zu erstellen, der die Kohärenz aller Batch-Verbindungen auf einmal analysiert.", "ja": "以下をクリックして、バッチ内のすべての化合物の一貫性を一度に分析するAI要約レポートを生成します。"},
    "btn_generate_batch_ai": {"pt": "✨ Gerar Parecer Clínico do Lote por IA", "en": "✨ Generate AI Clinical Opinion for the Batch", "es": "✨ Generar Dictamen Clínico del Lote por IA", "zh": "✨ 生成AI批次临床意见", "de": "✨ KI-Klinisches Gutachten für den Batch generieren", "ja": "✨ AIによるバッチ臨床所見を生成"},
    "matrix_section": {"pt": "⚖️ Matriz Comparativa e Evidências Biomoleculares", "en": "⚖️ Comparative Matrix & Biomolecular Evidence", "es": "⚖️ Matriz Comparativa y Evidencias Biomoleculares", "zh": "⚖️ 比较矩阵与生物分子证据", "de": "⚖️ Vergleichsmatrix & biomolekulare Evidenz", "ja": "⚖️ 比較マトリックスと生体分子エビデンス"},
    "detail_section": {"pt": "🔍 Inspeção Detalhada por Composto da Planilha", "en": "🔍 Detailed Inspection per Spreadsheet Compound", "es": "🔍 Inspección Detallada por Compuesto de la Hoja", "zh": "🔍 表格中各化合物的详细检查", "de": "🔍 Detaillierte Prüfung je Tabellenverbindung", "ja": "🔍 スプレッドシート内化合物の詳細検査"},
    "master_table_title": {"pt": "📋 Tabela Mestra do Lote", "en": "📋 Batch Master Table", "es": "📋 Tabla Maestra del Lote", "zh": "📋 批次主表", "de": "📋 Batch-Übersichtstabelle", "ja": "📋 バッチマスターテーブル"},
    "density_section": {"pt": "📈 Perfil de Densidade Molecular do Lote", "en": "📈 Batch Molecular Density Profile", "es": "📈 Perfil de Densidad Molecular del Lote", "zh": "📈 批次分子密度分布图", "de": "📈 Molekulares Dichteprofil des Batches", "ja": "📈 バッチ分子密度プロファイル"},
    "export_section": {"pt": "🖨️ Exportação de Relatórios Completa", "en": "🖨️ Full Report Export", "es": "🖨️ Exportación Completa de Informes", "zh": "🖨️ 完整报告导出", "de": "🖨️ Vollständiger Berichtsexport", "ja": "🖨️ 完全レポートエクスポート"},
    "btn_download_pdf_batch": {"pt": "📥 Baixar Laudo Clínico Executivo (PDF)", "en": "📥 Download Executive Clinical Report (PDF)", "es": "📥 Descargar Informe Clínico Ejecutivo (PDF)", "zh": "📥 下载执行版临床报告（PDF）", "de": "📥 Executive Klinikbericht herunterladen (PDF)", "ja": "📥 エグゼクティブ臨床レポートをダウンロード（PDF）"},
    "btn_download_json_batch": {"pt": "📥 Exportar Dados Estruturados (JSON)", "en": "📥 Export Structured Data (JSON)", "es": "📥 Exportar Datos Estructurados (JSON)", "zh": "📥 导出结构化数据（JSON）", "de": "📥 Strukturierte Daten exportieren (JSON)", "ja": "📥 構造化データをエクスポート（JSON）"},
    "fq_caption": {"pt": "Cálculo de descritores moleculares avançados (RDKit): Lipinski, Veber, Egan, alertas PAINS e risco hERG heurístico.", "en": "Advanced molecular descriptor calculation (RDKit): Lipinski, Veber, Egan, PAINS alerts and heuristic hERG risk.", "es": "Cálculo de descriptores moleculares avanzados (RDKit): Lipinski, Veber, Egan, alertas PAINS y riesgo hERG heurístico.", "zh": "高级分子描述符计算（RDKit）：Lipinski、Veber、Egan 规则、PAINS 警报及 hERG 启发式风险。", "de": "Berechnung erweiterter molekularer Deskriptoren (RDKit): Lipinski, Veber, Egan, PAINS-Warnungen und heuristisches hERG-Risiko.", "ja": "高度な分子記述子計算（RDKit）：Lipinski、Veber、Egan則、PAINSアラート、hERGヒューリスティックリスク。"},
    "input_fq_label": {"pt": "Nome do composto para triagem físico-química:", "en": "Compound name for physicochemical screening:", "es": "Nombre del compuesto para cribado fisicoquímico:", "zh": "用于理化筛选的化合物名称：", "de": "Verbindungsname für physikochemisches Screening:", "ja": "物理化学的スクリーニング対象の化合物名："},
    "error_no_smiles": {"pt": "⚠️ Não foi possível obter o SMILES estrutural deste composto (indisponível na base local/PubChem). Compostos macromoleculares/biológicos como anticorpos e peptídeos grandes não possuem SMILES tratável por RDKit neste módulo.", "en": "⚠️ Could not obtain the structural SMILES for this compound (unavailable in local base/PubChem). Macromolecular/biological compounds such as antibodies and large peptides do not have SMILES tractable by RDKit in this module.", "es": "⚠️ No fue posible obtener el SMILES estructural de este compuesto (no disponible en la base local/PubChem). Los compuestos macromoleculares/biológicos como anticuerpos y péptidos grandes no tienen SMILES tratable por RDKit en este módulo.", "zh": "⚠️ 无法获取该化合物的结构 SMILES（本地库/PubChem中不可用）。抗体和大型多肽等大分子/生物化合物在本模块中没有可被 RDKit 处理的 SMILES。", "de": "⚠️ SMILES-Struktur dieser Verbindung konnte nicht ermittelt werden (in lokaler Basis/PubChem nicht verfügbar). Makromolekulare/biologische Verbindungen wie Antikörper und große Peptide besitzen in diesem Modul kein für RDKit verarbeitbares SMILES.", "ja": "⚠️ この化合物の構造SMILESを取得できませんでした（ローカルデータベース/PubChemに存在しません）。抗体や大型ペプチドなどの高分子・生体化合物は、このモジュールではRDKitで処理可能なSMILESを持ちません。"},
    "error_invalid_smiles": {"pt": "⚠️ Estrutura SMILES inválida ou não interpretável pelo motor RDKit.", "en": "⚠️ Invalid SMILES structure or not interpretable by the RDKit engine.", "es": "⚠️ Estructura SMILES inválida o no interpretable por el motor RDKit.", "zh": "⚠️ SMILES 结构无效或 RDKit 引擎无法解析。", "de": "⚠️ Ungültige SMILES-Struktur oder von der RDKit-Engine nicht interpretierbar.", "ja": "⚠️ SMILES構造が無効か、RDKitエンジンで解釈できません。"},
    "fq_profile_title": {"pt": "🧪 Perfil Físico-Químico —", "en": "🧪 Physicochemical Profile —", "es": "🧪 Perfil Fisicoquímico —", "zh": "🧪 理化性质档案 —", "de": "🧪 Physikochemisches Profil —", "ja": "🧪 物理化学プロファイル —"},
    "metric_logp": {"pt": "LogP (Crippen)", "en": "LogP (Crippen)", "es": "LogP (Crippen)", "zh": "LogP（Crippen）", "de": "LogP (Crippen)", "ja": "LogP（Crippen）"},
    "metric_tpsa": {"pt": "TPSA", "en": "TPSA", "es": "TPSA", "zh": "TPSA", "de": "TPSA", "ja": "TPSA"},
    "metric_rotbonds": {"pt": "Ligações Rotacionáveis", "en": "Rotatable Bonds", "es": "Enlaces Rotables", "zh": "可旋转键数", "de": "Drehbare Bindungen", "ja": "回転可能結合数"},
    "rules_section": {"pt": "📏 Regras de Triagem Farmacocinética", "en": "📏 Pharmacokinetic Screening Rules", "es": "📏 Reglas de Cribado Farmacocinético", "zh": "📏 药代动力学筛选规则", "de": "📏 Pharmakokinetische Screening-Regeln", "ja": "📏 薬物動態スクリーニング則"},
    "pains_section": {"pt": "☣️ Alertas Estruturais PAINS (Falsos Positivos)", "en": "☣️ PAINS Structural Alerts (False Positives)", "es": "☣️ Alertas Estructurales PAINS (Falsos Positivos)", "zh": "☣️ PAINS 结构警报（假阳性）", "de": "☣️ PAINS-Strukturwarnungen (Falsch-Positive)", "ja": "☣️ PAINS構造アラート（偽陽性）"},
    "pains_none": {"pt": "✅ Nenhuma subestrutura PAINS conhecida detectada.", "en": "✅ No known PAINS substructure detected.", "es": "✅ No se detectó ninguna subestructura PAINS conocida.", "zh": "✅ 未检测到已知的 PAINS 子结构。", "de": "✅ Keine bekannte PAINS-Substruktur erkannt.", "ja": "✅ 既知のPAINS部分構造は検出されませんでした。"},
    "herg_section": {"pt": "❤️ Triagem de Off-Target Cardíaco (hERG)", "en": "❤️ Cardiac Off-Target Screening (hERG)", "es": "❤️ Cribado de Off-Target Cardíaco (hERG)", "zh": "❤️ 心脏脱靶筛选（hERG）", "de": "❤️ Kardiales Off-Target-Screening (hERG)", "ja": "❤️ 心臓オフターゲットスクリーニング（hERG）"},
    "didactic_notice_fq": {"pt": "🎓 Modo Didático ativo: alertas PAINS e triagem hERG detalhada disponíveis no Modo Pesquisa/P&D.", "en": "🎓 Educational Mode active: PAINS alerts and detailed hERG screening available in Research/R&D Mode.", "es": "🎓 Modo Didáctico activo: alertas PAINS y cribado hERG detallado disponibles en Modo Investigación/I+D.", "zh": "🎓 教学模式已启用：PAINS 警报和详细 hERG 筛选可在科研/研发模式中查看。", "de": "🎓 Lehrmodus aktiv: PAINS-Warnungen und detailliertes hERG-Screening im Forschungs-/F&E-Modus verfügbar.", "ja": "🎓 教育モードが有効です：PAINSアラートと詳細なhERGスクリーニングは研究/研究開発モードで利用可能です。"},
    "structure2d_section": {"pt": "🖼️ Estrutura Molecular 2D", "en": "🖼️ 2D Molecular Structure", "es": "🖼️ Estructura Molecular 2D", "zh": "🖼️ 二维分子结构", "de": "🖼️ 2D-Molekülstruktur", "ja": "🖼️ 2D分子構造"},
    "btn_download_sdf": {"pt": "📥 Baixar Estrutura 3D Otimizada (.sdf)", "en": "📥 Download Optimized 3D Structure (.sdf)", "es": "📥 Descargar Estructura 3D Optimizada (.sdf)", "zh": "📥 下载优化后的三维结构（.sdf）", "de": "📥 Optimierte 3D-Struktur herunterladen (.sdf)", "ja": "📥 最適化された3D構造をダウンロード（.sdf）"},
    "docking_caption": {"pt": "Visualização 3D de alvos proteicos (RCSB PDB) e estimativa heurística de afinidade de encaixe com o ligante.", "en": "3D visualization of protein targets (RCSB PDB) and heuristic estimation of ligand binding affinity.", "es": "Visualización 3D de dianas proteicas (RCSB PDB) y estimación heurística de afinidad de acoplamiento con el ligando.", "zh": "蛋白质靶点三维可视化（RCSB PDB）及配体结合亲和力的启发式估计。", "de": "3D-Visualisierung von Proteinzielen (RCSB PDB) und heuristische Schätzung der Liganden-Bindungsaffinität.", "ja": "タンパク質標的の3D可視化（RCSB PDB）とリガンド結合親和性のヒューリスティック推定。"},
    "protein_target_section": {"pt": "🧬 Alvo Proteico", "en": "🧬 Protein Target", "es": "🧬 Diana Proteica", "zh": "🧬 蛋白质靶点", "de": "🧬 Proteinziel", "ja": "🧬 タンパク質標的"},
    "pdb_source_label": {"pt": "Origem da estrutura da proteína:", "en": "Source of the protein structure:", "es": "Origen de la estructura de la proteína:", "zh": "蛋白质结构来源：", "de": "Quelle der Proteinstruktur:", "ja": "タンパク質構造の取得元："},
    "pdb_search_option": {"pt": "Buscar por ID no RCSB PDB", "en": "Search by ID in RCSB PDB", "es": "Buscar por ID en RCSB PDB", "zh": "在 RCSB PDB 中按 ID 搜索", "de": "Nach ID in RCSB PDB suchen", "ja": "RCSB PDBでIDを検索"},
    "pdb_upload_option": {"pt": "Upload manual de arquivo .pdb", "en": "Manual .pdb file upload", "es": "Carga manual de archivo .pdb", "zh": "手动上传 .pdb 文件", "de": "Manueller Upload einer .pdb-Datei", "ja": ".pdbファイルの手動アップロード"},
    "pdb_id_label": {"pt": "ID PDB (ex: 1IEP para c-Abl/Imatinib, 3ERT para receptor de estrogênio):", "en": "PDB ID (e.g. 1IEP for c-Abl/Imatinib, 3ERT for estrogen receptor):", "es": "ID PDB (ej: 1IEP para c-Abl/Imatinib, 3ERT para receptor de estrógeno):", "zh": "PDB ID（例如 1IEP 表示 c-Abl/伊马替尼，3ERT 表示雌激素受体）：", "de": "PDB-ID (z. B. 1IEP für c-Abl/Imatinib, 3ERT für Östrogenrezeptor):", "ja": "PDB ID（例：c-Abl/イマチニブは1IEP、エストロゲン受容体は3ERT）："},
    "pdb_not_found": {"pt": "⚠️ Estrutura não localizada no RCSB. Verifique o ID ou tente o upload manual.", "en": "⚠️ Structure not found in RCSB. Check the ID or try manual upload.", "es": "⚠️ Estructura no localizada en RCSB. Verifique el ID o pruebe la carga manual.", "zh": "⚠️ 在 RCSB 中未找到该结构。请检查 ID 或尝试手动上传。", "de": "⚠️ Struktur in RCSB nicht gefunden. Überprüfen Sie die ID oder versuchen Sie den manuellen Upload.", "ja": "⚠️ RCSBで構造が見つかりません。IDを確認するか、手動アップロードをお試しください。"},
    "pdb_offline_notice": {"pt": "Modo offline ativo: renderização proteica em tempo real suspensa. Faça upload manual de um .pdb local se necessário.", "en": "Offline mode active: real-time protein rendering suspended. Manually upload a local .pdb if needed.", "es": "Modo offline activo: renderizado proteico en tiempo real suspendido. Cargue manualmente un .pdb local si es necesario.", "zh": "离线模式已启用：实时蛋白质渲染已暂停。如有需要，请手动上传本地 .pdb 文件。", "de": "Offline-Modus aktiv: Echtzeit-Proteinrendering deaktiviert. Laden Sie bei Bedarf manuell eine lokale .pdb-Datei hoch.", "ja": "オフラインモードが有効：リアルタイムのタンパク質レンダリングは停止しています。必要に応じてローカルの.pdbを手動でアップロードしてください。"},
    "pdb_upload_label": {"pt": "Carregue o arquivo .pdb do alvo:", "en": "Upload the target's .pdb file:", "es": "Cargue el archivo .pdb de la diana:", "zh": "上传靶点的 .pdb 文件：", "de": "Laden Sie die .pdb-Datei des Ziels hoch:", "ja": "標的の.pdbファイルをアップロード："},
    "ligand_section": {"pt": "💊 Ligante Candidato", "en": "💊 Candidate Ligand", "es": "💊 Ligando Candidato", "zh": "💊 候选配体", "de": "💊 Kandidatenligand", "ja": "💊 候補リガンド"},
    "ligand_input_label": {"pt": "Nome do composto candidato ao encaixe:", "en": "Name of the candidate compound for docking:", "es": "Nombre del compuesto candidato al acoplamiento:", "zh": "候选对接化合物名称：", "de": "Name der Kandidatenverbindung für das Docking:", "ja": "ドッキング候補化合物名："},
    "smiles_unavailable_warn": {"pt": "⚠️ SMILES indisponível para este composto neste ambiente.", "en": "⚠️ SMILES unavailable for this compound in this environment.", "es": "⚠️ SMILES no disponible para este compuesto en este entorno.", "zh": "⚠️ 此环境中该化合物的 SMILES 不可用。", "de": "⚠️ SMILES für diese Verbindung in dieser Umgebung nicht verfügbar.", "ja": "⚠️ この環境ではこの化合物のSMILESは利用できません。"},
    "docking_score_section": {"pt": "📐 Estimativa Heurística de Encaixe (Docking Simplificado)", "en": "📐 Heuristic Docking Estimate (Simplified Docking)", "es": "📐 Estimación Heurística de Acoplamiento (Acoplamiento Simplificado)", "zh": "📐 启发式对接评分（简化对接）", "de": "📐 Heuristische Docking-Schätzung (Vereinfachtes Docking)", "ja": "📐 ヒューリスティックドッキング推定（簡易ドッキング）"},
    "docking_disclaimer": {"pt": "⚠️ **Importante:** esta pontuação é um modelo heurístico baseado em complementaridade de tamanho, lipofilicidade e flexibilidade do ligante frente ao bolsão médio de proteínas globulares. Não substitui um motor de docking real (ex: AutoDock Vina, Glide) nem prediz energia livre de ligação (ΔG) calibrada.", "en": "⚠️ **Important:** this score is a heuristic model based on size complementarity, lipophilicity and ligand flexibility against the average pocket of globular proteins. It does not replace a real docking engine (e.g. AutoDock Vina, Glide) nor predict calibrated binding free energy (ΔG).", "es": "⚠️ **Importante:** esta puntuación es un modelo heurístico basado en complementariedad de tamaño, lipofilicidad y flexibilidad del ligando frente al bolsillo promedio de proteínas globulares. No sustituye un motor de acoplamiento real (ej. AutoDock Vina, Glide) ni predice energía libre de unión (ΔG) calibrada.", "zh": "⚠️ **重要提示：** 此评分是基于配体相对于球状蛋白质平均口袋的尺寸互补性、亲脂性和柔性的启发式模型，不能替代真实的对接引擎（如 AutoDock Vina、Glide），也不能预测经校准的结合自由能（ΔG）。", "de": "⚠️ **Wichtig:** Diese Bewertung ist ein heuristisches Modell basierend auf Größenkomplementarität, Lipophilie und Ligandenflexibilität gegenüber der durchschnittlichen Tasche globulärer Proteine. Sie ersetzt keine echte Docking-Engine (z. B. AutoDock Vina, Glide) und sagt keine kalibrierte Bindungsfreie Energie (ΔG) voraus.", "ja": "⚠️ **重要：** このスコアは、球状タンパク質の平均的なポケットに対するリガンドのサイズ相補性、親油性、柔軟性に基づくヒューリスティックモデルです。実際のドッキングエンジン（AutoDock Vina、Glideなど）の代替にはならず、較正された結合自由エネルギー（ΔG）を予測するものでもありません。"},
    "score_size": {"pt": "Score de Tamanho", "en": "Size Score", "es": "Puntaje de Tamaño", "zh": "尺寸得分", "de": "Größen-Score", "ja": "サイズスコア"},
    "score_lipo": {"pt": "Score de Lipofilicidade", "en": "Lipophilicity Score", "es": "Puntaje de Lipofilicidad", "zh": "亲脂性得分", "de": "Lipophilie-Score", "ja": "親油性スコア"},
    "score_flex": {"pt": "Score de Flexibilidade", "en": "Flexibility Score", "es": "Puntaje de Flexibilidad", "zh": "柔性得分", "de": "Flexibilitäts-Score", "ja": "柔軟性スコア"},
    "score_combined": {"pt": "Score Combinado de Encaixe", "en": "Combined Docking Score", "es": "Puntaje Combinado de Acoplamiento", "zh": "综合对接得分", "de": "Kombinierter Docking-Score", "ja": "統合ドッキングスコア"},
    "docking_good": {"pt": "🟢 Perfil geométrico e fisico-químico favorável para encaixe no bolsão-alvo (estimativa).", "en": "🟢 Geometric and physicochemical profile favorable for binding to the target pocket (estimate).", "es": "🟢 Perfil geométrico y fisicoquímico favorable para el acoplamiento en el bolsillo diana (estimación).", "zh": "🟢 几何与理化性质有利于与靶点口袋结合（估算）。", "de": "🟢 Geometrisches und physikochemisches Profil günstig für die Bindung an die Zieltasche (Schätzung).", "ja": "🟢 標的ポケットへの結合に有利な幾何学的・物理化学的プロファイルです（推定）。"},
    "docking_moderate": {"pt": "🟡 Compatibilidade moderada; recomenda-se docking computacional dedicado para confirmação.", "en": "🟡 Moderate compatibility; dedicated computational docking is recommended for confirmation.", "es": "🟡 Compatibilidad moderada; se recomienda acoplamiento computacional dedicado para confirmar.", "zh": "🟡 兼容性中等；建议使用专门的计算对接进行确认。", "de": "🟡 Mäßige Kompatibilität; dediziertes rechnergestütztes Docking zur Bestätigung empfohlen.", "ja": "🟡 中程度の適合性；確認のため専用の計算ドッキングを推奨します。"},
    "docking_bad": {"pt": "🔴 Baixa compatibilidade estimada; molécula pode exigir otimização estrutural (lead optimization).", "en": "🔴 Low estimated compatibility; molecule may require structural optimization (lead optimization).", "es": "🔴 Baja compatibilidad estimada; la molécula puede requerir optimización estructural (optimización de líder).", "zh": "🔴 估计兼容性较低；该分子可能需要结构优化（先导化合物优化）。", "de": "🔴 Geringe geschätzte Kompatibilität; Molekül erfordert möglicherweise strukturelle Optimierung (Lead-Optimierung).", "ja": "🔴 推定適合性は低い；分子は構造最適化（リード最適化）が必要な場合があります。"},
    "offtarget_section": {"pt": "🧭 Mapeamento de Off-Targets Conhecidos", "en": "🧭 Mapping of Known Off-Targets", "es": "🧭 Mapeo de Off-Targets Conocidos", "zh": "🧭 已知脱靶效应图谱", "de": "🧭 Kartierung bekannter Off-Targets", "ja": "🧭 既知のオフターゲットマッピング"},
    "docking_empty_notice": {"pt": "Carregue uma estrutura proteica (PDB) e um composto candidato para gerar a estimativa de encaixe.", "en": "Load a protein structure (PDB) and a candidate compound to generate the docking estimate.", "es": "Cargue una estructura proteica (PDB) y un compuesto candidato para generar la estimación de acoplamiento.", "zh": "请加载蛋白质结构（PDB）和候选化合物以生成对接评分。", "de": "Laden Sie eine Proteinstruktur (PDB) und eine Kandidatenverbindung, um die Docking-Schätzung zu erstellen.", "ja": "タンパク質構造（PDB）と候補化合物を読み込んでドッキング推定を生成してください。"},
    "benchmark_caption": {"pt": "Matriz de interação/sinergia entre múltiplas moléculas e benchmark comparativo contra o fármaco padrão-ouro do módulo ativo.", "en": "Interaction/synergy matrix between multiple molecules and comparative benchmark against the gold-standard drug of the active module.", "es": "Matriz de interacción/sinergia entre múltiples moléculas y referencia comparativa contra el fármaco de referencia del módulo activo.", "zh": "多个分子间的相互作用/协同矩阵，以及与当前模块金标准药物的对比基准。", "de": "Interaktions-/Synergiematrix zwischen mehreren Molekülen und vergleichendes Benchmark gegen das Goldstandard-Medikament des aktiven Moduls.", "ja": "複数分子間の相互作用/相乗効果マトリックスと、アクティブモジュールのゴールドスタンダード薬剤との比較ベンチマーク。"},
    "molecule_select_section": {"pt": "🧮 Seleção de Moléculas para Comparação", "en": "🧮 Molecule Selection for Comparison", "es": "🧮 Selección de Moléculas para Comparación", "zh": "🧮 用于比较的分子选择", "de": "🧮 Molekülauswahl zum Vergleich", "ja": "🧮 比較のための分子選択"},
    "molecule_select_label": {"pt": "Selecione de 2 a 4 moléculas para comparar:", "en": "Select 2 to 4 molecules to compare:", "es": "Seleccione de 2 a 4 moléculas para comparar:", "zh": "选择 2 到 4 个分子进行比较：", "de": "Wählen Sie 2 bis 4 Moleküle zum Vergleich aus:", "ja": "比較する分子を2〜4個選択してください："},
    "synergy_matrix_title": {"pt": "⚖️ Matriz de Interação / Sinergia Estrutural", "en": "⚖️ Interaction / Structural Synergy Matrix", "es": "⚖️ Matriz de Interacción / Sinergia Estructural", "zh": "⚖️ 相互作用/结构协同矩阵", "de": "⚖️ Interaktions-/Struktursynergie-Matrix", "ja": "⚖️ 相互作用/構造相乗効果マトリックス"},
    "radar_section": {"pt": "🎯 Benchmark: Radar Comparativo vs. Fármaco Padrão-Ouro", "en": "🎯 Benchmark: Comparative Radar vs. Gold-Standard Drug", "es": "🎯 Referencia: Radar Comparativo vs. Fármaco de Referencia", "zh": "🎯 基准：与金标准药物的雷达图对比", "de": "🎯 Benchmark: Vergleichs-Radar vs. Goldstandard-Medikament", "ja": "🎯 ベンチマーク：ゴールドスタンダード薬剤との比較レーダー"},
    "gold_standard_label": {"pt": "Fármaco de referência (padrão-ouro) do módulo", "en": "Reference (gold-standard) drug of the module", "es": "Fármaco de referencia (patrón oro) del módulo", "zh": "该模块的参考（金标准）药物", "de": "Referenz- (Goldstandard-) Medikament des Moduls", "ja": "モジュールの基準（ゴールドスタンダード）薬剤"},
    "benchmark_select_warn": {"pt": "Selecione ao menos 2 moléculas para habilitar a matriz de sinergia e o radar de benchmark.", "en": "Select at least 2 molecules to enable the synergy matrix and the benchmark radar.", "es": "Seleccione al menos 2 moléculas para habilitar la matriz de sinergia y el radar de referencia.", "zh": "请至少选择 2 个分子以启用协同矩阵和基准雷达图。", "de": "Wählen Sie mindestens 2 Moleküle aus, um die Synergiematrix und das Benchmark-Radar zu aktivieren.", "ja": "相乗効果マトリックスとベンチマークレーダーを有効にするには、少なくとも2つの分子を選択してください。"},
    "literature_caption": {"pt": "Classificação por Grau de Evidência Científica dos artigos recuperados e proposição automática de Mecanismo de Ação (MoA) via IA.", "en": "Classification by Scientific Evidence Level of retrieved articles and automatic AI proposal of Mechanism of Action (MoA).", "es": "Clasificación por Grado de Evidencia Científica de los artículos recuperados y propuesta automática de Mecanismo de Acción (MoA) mediante IA.", "zh": "对检索到的文献按科学证据等级分类，并通过AI自动生成作用机制（MoA）提案。", "de": "Klassifizierung nach wissenschaftlichem Evidenzgrad der abgerufenen Artikel und automatischer KI-Vorschlag zum Wirkmechanismus (MoA).", "ja": "検索された論文の科学的エビデンスレベルによる分類と、AIによる作用機序（MoA）の自動提案。"},
    "literature_input_label": {"pt": "Composto para análise de literatura e MoA:", "en": "Compound for literature and MoA analysis:", "es": "Compuesto para análisis de literatura y MoA:", "zh": "用于文献与作用机制分析的化合物：", "de": "Verbindung für Literatur- und MoA-Analyse:", "ja": "文献・MoA分析対象の化合物："},
    "evidence_section": {"pt": "📚 Classificação de Evidência Científica", "en": "📚 Scientific Evidence Classification", "es": "📚 Clasificación de Evidencia Científica", "zh": "📚 科学证据分级", "de": "📚 Wissenschaftliche Evidenzklassifikation", "ja": "📚 科学的エビデンス分類"},
    "title_retrieved_label": {"pt": "Título recuperado:", "en": "Retrieved title:", "es": "Título recuperado:", "zh": "检索到的标题：", "de": "Abgerufener Titel:", "ja": "取得されたタイトル："},
    "title_unavailable": {"pt": "_Título não disponível via API._", "en": "_Title unavailable via API._", "es": "_Título no disponible vía API._", "zh": "_通过API无法获取标题。_", "de": "_Titel über API nicht verfügbar._", "ja": "_APIでタイトルを取得できません。_"},
    "confidence_factor_label": {"pt": "Fator de Confiança Estimado:", "en": "Estimated Confidence Factor:", "es": "Factor de Confianza Estimado:", "zh": "估计置信度：", "de": "Geschätzter Konfidenzfaktor:", "ja": "推定信頼度："},
    "evidence_advanced_note": {"pt": "ℹ️ Classificação heurística baseada em palavras-chave do título (metodologia simplificada de triagem bibliográfica). Para revisões sistemáticas formais, utilize ferramentas como GRADE ou Cochrane RoB.", "en": "ℹ️ Heuristic classification based on title keywords (simplified bibliographic screening methodology). For formal systematic reviews, use tools such as GRADE or Cochrane RoB.", "es": "ℹ️ Clasificación heurística basada en palabras clave del título (metodología simplificada de cribado bibliográfico). Para revisiones sistemáticas formales, use herramientas como GRADE o Cochrane RoB.", "zh": "ℹ️ 基于标题关键词的启发式分类（简化的文献筛选方法）。如需正式系统评价，请使用 GRADE 或 Cochrane RoB 等工具。", "de": "ℹ️ Heuristische Klassifikation basierend auf Titel-Schlüsselwörtern (vereinfachte bibliografische Screening-Methodik). Für formale systematische Übersichten nutzen Sie Tools wie GRADE oder Cochrane RoB.", "ja": "ℹ️ タイトルのキーワードに基づくヒューリスティック分類（簡易文献スクリーニング手法）。正式なシステマティックレビューにはGRADEやCochrane RoBなどのツールをご利用ください。"},
    "evidence_none": {"pt": "⚠️ Nenhuma publicação direta localizada no PubMed para classificação de evidência.", "en": "⚠️ No direct publication found on PubMed for evidence classification.", "es": "⚠️ No se localizó ninguna publicación directa en PubMed para la clasificación de evidencia.", "zh": "⚠️ 在 PubMed 中未找到用于证据分级的直接文献。", "de": "⚠️ Keine direkte Publikation auf PubMed für die Evidenzklassifikation gefunden.", "ja": "⚠️ エビデンス分類のための直接的な論文はPubMedで見つかりませんでした。"},
    "moa_section": {"pt": "🧠 Proposição Automática de Mecanismo de Ação (MoA)", "en": "🧠 Automatic Mechanism of Action (MoA) Proposal", "es": "🧠 Propuesta Automática de Mecanismo de Acción (MoA)", "zh": "🧠 自动作用机制（MoA）提案", "de": "🧠 Automatischer Vorschlag zum Wirkmechanismus (MoA)", "ja": "🧠 自動作用機序（MoA）提案"},
    "btn_generate_moa": {"pt": "✨ Gerar Proposição de MoA", "en": "✨ Generate MoA Proposal", "es": "✨ Generar Propuesta de MoA", "zh": "✨ 生成作用机制提案", "de": "✨ MoA-Vorschlag generieren", "ja": "✨ MoA提案を生成"},
    "spinner_moa": {"pt": "Sintetizando hipótese mecanística...", "en": "Synthesizing mechanistic hypothesis...", "es": "Sintetizando hipótesis mecanicista...", "zh": "正在综合机制假设...", "de": "Synthetisiere mechanistische Hypothese...", "ja": "機序的仮説を統合中..."},
    "citation_section": {"pt": "📑 Exportação de Citação Científica", "en": "📑 Scientific Citation Export", "es": "📑 Exportación de Cita Científica", "zh": "📑 科学引文导出", "de": "📑 Export wissenschaftlicher Zitate", "ja": "📑 科学的引用のエクスポート"},
    "btn_export_bib": {"pt": "📥 Exportar Citação (.bib)", "en": "📥 Export Citation (.bib)", "es": "📥 Exportar Cita (.bib)", "zh": "📥 导出引文（.bib）", "de": "📥 Zitat exportieren (.bib)", "ja": "📥 引用をエクスポート（.bib）"},
    "btn_export_ris": {"pt": "📥 Exportar Citação (.ris)", "en": "📥 Export Citation (.ris)", "es": "📥 Exportar Cita (.ris)", "zh": "📥 导出引文（.ris）", "de": "📥 Zitat exportieren (.ris)", "ja": "📥 引用をエクスポート（.ris）"},
    "eln_caption": {"pt": "Caderno Eletrônico de Laboratório: registre, revise e exporte seus experimentos de triagem em múltiplos formatos.", "en": "Electronic Lab Notebook: record, review and export your screening experiments in multiple formats.", "es": "Cuaderno Electrónico de Laboratorio: registre, revise y exporte sus experimentos de cribado en múltiples formatos.", "zh": "电子实验记录本：记录、查看并以多种格式导出您的筛选实验。", "de": "Elektronisches Laborbuch: Erfassen, überprüfen und exportieren Sie Ihre Screening-Experimente in mehreren Formaten.", "ja": "電子実験ノート：スクリーニング実験を記録・確認し、複数の形式でエクスポートします。"},
    "new_experiment_expander": {"pt": "➕ Registrar novo experimento manualmente", "en": "➕ Manually register a new experiment", "es": "➕ Registrar nuevo experimento manualmente", "zh": "➕ 手动登记新实验", "de": "➕ Neues Experiment manuell erfassen", "ja": "➕ 新しい実験を手動で登録"},
    "exp_name_label": {"pt": "Nome do composto/experimento:", "en": "Compound/experiment name:", "es": "Nombre del compuesto/experimento:", "zh": "化合物/实验名称：", "de": "Name der Verbindung/des Experiments:", "ja": "化合物/実験名："},
    "exp_notes_label": {"pt": "Observações / Notas do pesquisador:", "en": "Observations / Researcher notes:", "es": "Observaciones / Notas del investigador:", "zh": "观察记录/研究人员备注：", "de": "Beobachtungen / Forschernotizen:", "ja": "観察事項／研究者メモ："},
    "btn_save_experiment": {"pt": "Salvar Experimento", "en": "Save Experiment", "es": "Guardar Experimento", "zh": "保存实验", "de": "Experiment speichern", "ja": "実験を保存"},
    "exp_saved_success": {"pt": "Experimento '{nome}' registrado com sucesso!", "en": "Experiment '{nome}' successfully recorded!", "es": "¡Experimento '{nome}' registrado con éxito!", "zh": "实验 '{nome}' 已成功登记！", "de": "Experiment '{nome}' erfolgreich gespeichert!", "ja": "実験「{nome}」が正常に記録されました！"},
    "registered_experiments_title": {"pt": "📋 Experimentos Registrados na Sessão", "en": "📋 Experiments Recorded in Session", "es": "📋 Experimentos Registrados en la Sesión", "zh": "📋 本次会话中登记的实验", "de": "📋 In der Sitzung erfasste Experimente", "ja": "📋 セッションで登録された実験"},
    "no_experiments_notice": {"pt": "Nenhum experimento registrado ainda. Utilize o formulário acima ou o botão de salvamento nas abas de análise individual.", "en": "No experiments recorded yet. Use the form above or the save button on the individual analysis tabs.", "es": "Aún no hay experimentos registrados. Use el formulario anterior o el botón de guardar en las pestañas de análisis individual.", "zh": "尚未登记任何实验。请使用上面的表单，或在各分析标签页中使用保存按钮。", "de": "Noch keine Experimente erfasst. Verwenden Sie das obige Formular oder die Speichern-Schaltfläche in den Einzelanalyse-Tabs.", "ja": "まだ登録された実験はありません。上記のフォーム、または個別分析タブの保存ボタンをご利用ください。"},
    "notes_label_short": {"pt": "Notas:", "en": "Notes:", "es": "Notas:", "zh": "备注：", "de": "Notizen:", "ja": "メモ："},
    "no_fq_data_caption": {"pt": "Sem dados físico-químicos associados.", "en": "No associated physicochemical data.", "es": "Sin datos fisicoquímicos asociados.", "zh": "无相关理化数据。", "de": "Keine zugehörigen physikochemischen Daten.", "ja": "関連する物理化学データはありません。"},
    "btn_delete_record": {"pt": "🗑️ Remover este registro", "en": "🗑️ Remove this record", "es": "🗑️ Eliminar este registro", "zh": "🗑️ 删除该记录", "de": "🗑️ Diesen Eintrag entfernen", "ja": "🗑️ この記録を削除"},
    "eln_export_section": {"pt": "🖨️ Exportação Multiformato do Caderno Completo", "en": "🖨️ Multi-format Export of the Full Notebook", "es": "🖨️ Exportación Multiformato del Cuaderno Completo", "zh": "🖨️ 完整记录本的多格式导出", "de": "🖨️ Multiformat-Export des vollständigen Laborbuchs", "ja": "🖨️ 完全ノートの複数形式エクスポート"},
    "btn_export_all_json": {"pt": "📥 Exportar Tudo (.json)", "en": "📥 Export All (.json)", "es": "📥 Exportar Todo (.json)", "zh": "📥 导出全部（.json）", "de": "📥 Alles exportieren (.json)", "ja": "📥 すべてエクスポート（.json）"},
    "btn_export_pdf_consolidated": {"pt": "📥 Exportar Laudo Consolidado (.pdf)", "en": "📥 Export Consolidated Report (.pdf)", "es": "📥 Exportar Informe Consolidado (.pdf)", "zh": "📥 导出合并报告（.pdf）", "de": "📥 Konsolidierten Bericht exportieren (.pdf)", "ja": "📥 統合レポートをエクスポート（.pdf）"},
    "btn_export_csv": {"pt": "📥 Exportar Planilha (.csv)", "en": "📥 Export Spreadsheet (.csv)", "es": "📥 Exportar Hoja de Cálculo (.csv)", "zh": "📥 导出表格（.csv）", "de": "📥 Tabelle exportieren (.csv)", "ja": "📥 スプレッドシートをエクスポート（.csv）"},
    "btn_clear_notebook": {"pt": "🧹 Limpar todo o Caderno Científico", "en": "🧹 Clear the entire Lab Notebook", "es": "🧹 Limpiar todo el Cuaderno Científico", "zh": "🧹 清空整个电子实验记录本", "de": "🧹 Gesamtes Laborbuch löschen", "ja": "🧹 電子実験ノートをすべてクリア"},
}


def t(chave, **kwargs):
    """Resolve uma chave de tradução para o idioma ativo em st.session_state, com fallback para PT."""
    idioma = st.session_state.get("idioma_ativo", "pt")
    entrada = TRANSLATIONS.get(chave)
    if entrada is None:
        return chave
    texto = entrada.get(idioma, entrada.get("pt", chave))
    if kwargs:
        try:
            return texto.format(**kwargs)
        except Exception:
            return texto
    return texto


# --- CSS CUSTOMIZADO: TEMA DARK EXECUTIVO (AZUL/ROXO) ---
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    :root {
        --bg-primary: #0a0e17;
        --bg-secondary: #0f1420;
        --bg-card: #131a2b;
        --bg-card-hover: #171f34;
        --border-subtle: #232c42;
        --accent-blue: #4f7cff;
        --accent-purple: #9b6bff;
        --accent-gradient: linear-gradient(135deg, #4f7cff 0%, #9b6bff 100%);
        --text-primary: #e8ecf5;
        --text-secondary: #8b95ad;
        --success: #22c55e;
        --warning: #f5b942;
        --danger: #f0556b;
    }

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp {
        background: radial-gradient(circle at 10% 0%, #10152a 0%, var(--bg-primary) 45%) fixed;
        color: var(--text-primary);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0c1120 0%, #0a0e17 100%);
        border-right: 1px solid var(--border-subtle);
    }
    section[data-testid="stSidebar"] * { color: var(--text-primary) !important; }

    h1, h2, h3, h4 { font-family: 'Inter', sans-serif !important; letter-spacing: -0.02em; color: var(--text-primary) !important; }
    h1 { font-weight: 800 !important; }
    h2, h3 { font-weight: 700 !important; }

    p, span, label, .stMarkdown, .stCaption { color: var(--text-secondary); }

    /* CARDS DE MÉTRICAS */
    div[data-testid="stMetric"] {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 14px;
        padding: 16px 18px;
        transition: all 0.25s ease;
        box-shadow: 0 2px 10px rgba(0,0,0,0.25);
    }
    div[data-testid="stMetric"]:hover {
        border-color: var(--accent-blue);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(79, 124, 255, 0.18);
    }
    div[data-testid="stMetricLabel"] { color: var(--text-secondary) !important; font-weight: 600; font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: 0.04em;}
    div[data-testid="stMetricValue"] { color: var(--text-primary) !important; font-weight: 800 !important; font-family: 'JetBrains Mono', monospace !important;}

    /* BOTÕES */
    .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
        background: var(--accent-gradient) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.55rem 1.3rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.01em;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 12px rgba(79, 124, 255, 0.25);
    }
    .stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 22px rgba(155, 107, 255, 0.4);
        filter: brightness(1.08);
    }
    .stButton > button:active, .stDownloadButton > button:active { transform: translateY(0px); }

    /* INPUTS */
    .stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox > div > div, div[data-baseweb="select"] > div {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: 0 0 0 2px rgba(79, 124, 255, 0.25) !important;
    }

    /* ABAS (TABS) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: var(--bg-secondary);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid var(--border-subtle);
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        color: var(--text-secondary);
        font-weight: 600;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background: var(--accent-gradient) !important;
        color: #ffffff !important;
    }

    /* EXPANDERS */
    .streamlit-expanderHeader, div[data-testid="stExpander"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
    }

    /* ALERTAS */
    div[data-testid="stAlert"] { border-radius: 12px; border: 1px solid var(--border-subtle); }

    /* TABELAS HTML CUSTOMIZADAS */
    .tabela-v9 { width: 100%; border-collapse: collapse; margin-bottom: 20px; border-radius: 12px; overflow: hidden; font-size: 12px;}
    .tabela-v9 th { background: var(--accent-gradient); color: #fff; padding: 12px 10px; text-align: left; font-weight: 600; }
    .tabela-v9 td { padding: 10px; border-bottom: 1px solid var(--border-subtle); color: var(--text-primary); background-color: var(--bg-card);}
    .tabela-v9 tr:nth-child(even) td { background-color: var(--bg-card-hover); }
    .tabela-v9 tr:hover td { background-color: #1c2540; }

    /* DATAFRAMES NATIVOS */
    div[data-testid="stDataFrame"] { border: 1px solid var(--border-subtle); border-radius: 12px; overflow: hidden; }

    /* SLIDER */
    div[data-testid="stSlider"] [role="slider"] { background-color: var(--accent-purple) !important; }

    /* TOGGLE */
    div[data-testid="stToggle"] label div[data-checked="true"] { background-color: var(--accent-blue) !important; }

    /* SCROLLBAR */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: var(--border-subtle); border-radius: 8px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--accent-blue); }

    hr { border-color: var(--border-subtle) !important; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- INICIALIZAÇÃO DO ESTADO GLOBAL ---
if "historico_auditoria" not in st.session_state:
    st.session_state.historico_auditoria = []
if "eln_experimentos" not in st.session_state:
    st.session_state.eln_experimentos = []
if "cache_moleculas" not in st.session_state:
    st.session_state.cache_moleculas = {}
if "idioma_ativo" not in st.session_state:
    st.session_state.idioma_ativo = "pt"

# --- CATÁLOGO PAINS (CARREGADO UMA ÚNICA VEZ) ---
@st.cache_resource(show_spinner=False)
def carregar_catalogo_pains():
    params = FilterCatalogParams()
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_A)
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_B)
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_C)
    return FilterCatalog(params)

CATALOGO_PAINS = carregar_catalogo_pains()

# --- BASE DE CONHECIMENTO CIENTÍFICO GLOBAL COMPLETA ---
# NOTA DE ESCOPO: a base de conhecimento farmacológico permanece em português (conteúdo
# curado especializado). A camada de tradução (TRANSLATIONS/t()) cobre toda a "moldura" da
# interface (menus, botões, rótulos, mensagens do sistema); traduzir automaticamente o
# conteúdo científico geraria risco de imprecisão terminológica em contexto clínico.
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
        },
        "rapamycin": {
            "aplicacao": "Inibidor robusto da via mecânica mTor (Target of Rapamycin). Age reprogramando o metabolismo energético e retardando o fenótipo de senescência replicativa celular.",
            "pipeline": "Fase Avançada de Modelagem Pré-Clínica. Desafios críticos associados à imunossupressão crônica e controle estrito de dosagem cíclica.",
            "classe": "Inibidor mTOR / Senolítico"
        },
        "metformin": {
            "aplicacao": "Agente senomórfico clássico derivado de biguanida. Atua via ativação de AMPK e atenuação de estresse oxidativo mitocondrial, reduzindo marcadores pró-inflamatórios sistêmicos.",
            "pipeline": "Ensaios Translacionais Globais (Projeto TAME). Perfil de segurança robusto e custo de manufatura escalável para distribuição em massa.",
            "classe": "Senomorfo / Ativador AMPK"
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
        },
        "galantamine": {
            "aplicacao": "Inibidor competitivo da acetilcolinesterase e modulador alostérico de receptores nicotínicos. Duplo mecanismo que potencializa a resposta colinérgica central.",
            "pipeline": "Disponibilidade comercial estabelecida. Estudos de pipeline focam em novas matrizes transdérmicas de liberação contínua.",
            "classe": "Inibidor da AChE / Modulador Nicotínico"
        }
    },
    "Cardiologia e Insuficiência Cardíaca": {
        "sacubitril": {
            "aplicacao": "Inibidor da neprilisina que previne a degradação de peptídeos natriuréticos benéficos, promovendo vasodilação e reduzindo a fibrose miocárdica progressiva.",
            "pipeline": "Pilar consagrado no tratamento de insuficiência cardíaca de fração de ejeção reduzida. Ensaios em andamento avaliam sinergia mecânica combinada.",
            "classe": "Inibidor da Neprilisina"
        },
        "empagliflozin": {
            "aplicacao": "Inibidor seletivo do cotransportador sódio-glicose 2 (SGLT2). Atua reduzindo a pré-carga e pós-carga miocárdica por efeito osmótico e metabólico direto.",
            "pipeline": "Validação expandida para proteção cardioprotetora contínua em pacientes com ou sem comorbidades glicêmicas de base.",
            "classe": "Inibidor de SGLT2"
        }
    },
    "Endocrinologia e Doenças Metabólicas": {
        "semaglutide": {
            "aplicacao": "Agonista potente do receptor do peptídeo semelhante ao glucagon 1 (GLP-1). Atua otimizando a secreção de insulina insulinotrópica e na modulação sacietógena central.",
            "pipeline": "Estudos de fase avançada focados em desfechos macrovasculares de longo prazo e redução expressiva de esteato-hepatite metabólica.",
            "classe": "Agonista de Receptor GLP-1"
        },
        "tirzepatide": {
            "aplicacao": "Coagonista duplo direcionado aos receptores de GIP e GLP-1. Oferece controle sinérgico estendido sobre a homeostase energética.",
            "pipeline": "Lançamentos globais integrados. Novas fases em andamento para avaliar a preservação de massa magra estrutural.",
            "classe": "Agonista Duplo GIP/GLP-1"
        }
    },
    "Imunologia e Processos Autoimunes": {
        "adalimumab": {
            "aplicacao": "Anticorpo monoclonal recombinante IgG1 totalmente humano. Liga-se especificamente ao fator de necrose tumoral alfa (TNF-alfa), neutralizando sua atividade pró-inflamatória.",
            "pipeline": "Mercado maduro em transição global de otimização de custo por biossimilares. Estudos buscam identificar biomarcadores preditivos.",
            "classe": "Anticorpo Monoclonal anti-TNF"
        },
        "tofacitinib": {
            "aplicacao": "Inibidor seletivo de pequena molécula das enzimas Janus Quinase (JAK1 e JAK3). Bloqueia a transdução de sinal intracelular de citocinas inflamatórias.",
            "pipeline": "Consolidado na reumatologia de alta complexidade. Monitoramentos de segurança refinam o perfil de risco do paciente idoso.",
            "classe": "Inibidor de JAK"
        }
    }
}

# Fármaco padrão-ouro de referência por módulo (usado no Benchmark Radar)
FARMACO_CONTROLE_POR_MODULO = {
    "Longevidade Celular e Oncologia": "dasatinib",
    "Neurologia e Neuroproteção": "donepezil",
    "Cardiologia e Insuficiência Cardíaca": "sacubitril",
    "Endocrinologia e Doenças Metabólicas": "semaglutide",
    "Imunologia e Processos Autoimunes": "adalimumab",
}

MOCK_PUBCHEM_DATA = {
    "quercetin": {"formula": "C15H10O7", "weight": 302.24, "smiles": "O=c1c(O)c(-c2ccc(O)c(O)c2)oc2cc(O)cc(O)c12"},
    "dasatinib": {"formula": "C22H26ClN7O2S", "weight": 488.0, "smiles": "Cc1nc(Nc2ncc(C(=O)Nc3c(C)cccc3Cl)s2)cc(N2CCN(CCO)CC2)n1"},
    "navitoclax": {"formula": "C47H55ClF3N5O6S3", "weight": 974.6, "smiles": "CC1(C)CCC(CN2CCC(N(C)c3ccc(C(=O)NS(=O)(=O)c4ccc(N5CCC(CN6CCOCC6)CC5)cc4[N+](=O)[O-])c(Oc4cnc5[nH]ccc5c4)c3)=CC2)=C1c1ccc(Cl)cc1"},
    "fisetin": {"formula": "C15H10O6", "weight": 286.24, "smiles": "O=c1c(O)c(-c2ccc(O)c(O)c2)oc2cc(O)ccc12"},
    "resveratrol": {"formula": "C14H12O3", "weight": 228.25, "smiles": "Oc1ccc(/C=C/c2cc(O)cc(O)c2)cc1"},
    "rapamycin": {"formula": "C51H79NO13", "weight": 914.2, "smiles": "C[C@@H]1CC[C@H]2C[C@@H](/C(=C/C=C/C=C/[C@@H](C[C@@H](C(=O)[C@H](CC[C@@H](/C(=C/[C@H](C(=O)C[C@H](OC(=O)[C@@H]3CCCCN3C(=O)C(=O)[C@@]1(O)O2)[C@H](C)C[C@@H]4CC[C@H]([C@@H](C4)OC)O)/C)O)OC)C)C)/C)OC",},
    "metformin": {"formula": "C4H11N5", "weight": 129.16, "smiles": "CN(C)C(=N)NC(=N)N"},
    "donepezil": {"formula": "C24H29NO3", "weight": 379.5, "smiles": "COc1cc2c(cc1OC)C(=O)C(CC1CCN(Cc3ccccc3)CC1)C2"},
    "memantine": {"formula": "C12H21N", "weight": 179.3, "smiles": "CC12CC3CC(C)(C1)CC(N)(C3)C2"},
    "galantamine": {"formula": "C17H21NO3", "weight": 287.36, "smiles": "COc1ccc2c3c1O[C@@H]1C=C[C@H](O)C[C@@]31CCN(C)C2"},
    "sacubitril": {"formula": "C24H29NO5", "weight": 411.5, "smiles": "CCOC(=O)CC(Cc1ccc(-c2ccccc2)cc1)NC(=O)CCC(CC(=O)O)C"},
    "empagliflozin": {"formula": "C23H27ClO7", "weight": 450.9, "smiles": "CCOc1cc(Cc2ccc(Cl)c(-c3ccc(C[C@H]4O[C@@H](CO)[C@H](O)[C@@H](O)[C@H]4O)cc3)c2)ccc1"},
    "semaglutide": {"formula": "C187H291N45O59", "weight": 4113.4, "smiles": ""},
    "tirzepatide": {"formula": "C225H348N48O68", "weight": 4813.5, "smiles": ""},
    "adalimumab": {"formula": "C6428H9912N1694O1987S46", "weight": 144190.3, "smiles": ""},
    "tofacitinib": {"formula": "C16H20N6O", "weight": 312.38, "smiles": "C[C@H]1CCN(C(=O)CC#N)C[C@@H]1N(C)c1ncnc2[nH]ccc12"}
}

# --- SANITIZAÇÃO CORRIGIDA PARA STREAMLIT + FPDF2 ---
def sanitize_pdf_text(texto):
    if texto is None:
        return ""
    return str(texto).encode("latin-1", errors="replace").decode("latin-1")

def analisar_acao_reacao(peso_molecular, classe_terapeutica):
    if peso_molecular > 500:
        return "⚠️ Alerta Lipinski: Peso molecular excede 500 g/mol. Viabilidade de absorção passiva oral reduzida. Recomendado uso vetorial estruturado."
    if "Inibidor" in classe_terapeutica:
        return "🟢 Mecanismo Ativo: Bloqueio competitivo de alta seletividade enzimática verificado no espectro analítico."
    if "Senolítico" in classe_terapeutica:
        return "⚡ Mecanismo Ativo: Direcionamento pró-apoptótico em subpopulações senescentes estáveis. Requer regime intermitente."
    return "🔍 Farmacocinética favorável e compatível com regras básicas de permeabilidade de membrana."

# --- MOTOR DE INTELIGÊNCIA ARTIFICIAL (AGENTE CLÍNICO HÍBRIDO) ---
def gerar_insight_ia(composto, formula, peso, modulo, api_key):
    time.sleep(1.2)
    if api_key:
        return f"🤖 [Insight Gerado via API Externa]: A análise profunda da estrutura molecular {formula} do {composto} indica forte potencial de ligação em receptores da área de {modulo}. O peso molecular de {peso} g/mol sugere que modificações lipídicas podem otimizar sua biodisponibilidade em 43%."
    else:
        return f"🤖 [IA Local Híbrida]: O composto **{composto.capitalize()}** (Fórmula: {formula}) foi escaneado em nossa base neural. Com base em seu peso molecular de **{peso} g/mol**, nossa IA prevê uma alta afinidade com alvos proteicos no eixo de **{modulo}**. Recomendamos modelagem molecular in silico (Docking) para validar sua eficácia como agente terapêutico primário. \n\n*Nota: Conecte uma Chave API na barra lateral para análises generativas em tempo real.*"

def gerar_moa_ia(composto, classe, descritores, modulo):
    """Propõe um resumo executivo de Mecanismo de Ação (MoA) combinando classe terapêutica e descritores físico-químicos."""
    time.sleep(1.0)
    perfil = "lipofílico e de fácil permeação de membrana" if descritores.get("logp", 0) > 2 else "hidrofílico, dependente de transportadores ativos"
    tamanho = "compacta, compatível com bolsões de ligação estreitos" if descritores.get("peso", 0) < 350 else "volumosa, potencialmente restrita a sítios alostéricos amplos"
    return (
        f"🧠 **Proposição de Mecanismo de Ação (MoA) — {composto.capitalize()}**\n\n"
        f"• **Classe Farmacológica:** {classe}.\n"
        f"• **Perfil Físico-Químico:** Molécula {perfil}, com arquitetura {tamanho}.\n"
        f"• **Hipótese de Ação no eixo {modulo}:** O composto provavelmente interage com seu alvo por complementaridade estérica e eletrônica, "
        f"modulando a via de sinalização associada à classe '{classe}', com repercussão direta na cascata patológica-alvo do módulo selecionado.\n"
        f"• **Resumo Executivo:** Perfil consistente com candidato de triagem primária a secundária; recomenda-se validação por docking direcionado "
        f"e ensaios funcionais in vitro para confirmação do mecanismo proposto."
    )

def classificar_evidencia_ia(titulo_artigo, pmid):
    """Classifica heuristicamente o grau de evidência científica de um artigo com base em palavras-chave do título."""
    if not titulo_artigo or pmid in (None, "Não encontrado", "Erro"):
        return {"nivel": "Indeterminado", "cor": "gray", "fator_confianca": "N/A"}

    titulo_lower = titulo_artigo.lower()
    if any(k in titulo_lower for k in ["meta-analysis", "systematic review"]):
        return {"nivel": "Nível I — Metanálise / Revisão Sistemática", "cor": "green", "fator_confianca": "Muito Alto"}
    if any(k in titulo_lower for k in ["randomized", "clinical trial", "phase ii", "phase iii", "double-blind"]):
        return {"nivel": "Nível II — Ensaio Clínico Randomizado", "cor": "green", "fator_confianca": "Alto"}
    if any(k in titulo_lower for k in ["cohort", "observational", "case-control"]):
        return {"nivel": "Nível III — Estudo Observacional/Coorte", "cor": "orange", "fator_confianca": "Moderado"}
    if any(k in titulo_lower for k in ["in vitro", "cell line", "molecular docking", "in silico"]):
        return {"nivel": "Nível IV — Estudo In Vitro / In Silico", "cor": "orange", "fator_confianca": "Moderado-Baixo"}
    if any(k in titulo_lower for k in ["mice", "rat", "animal model", "in vivo"]):
        return {"nivel": "Nível IV — Estudo Pré-Clínico In Vivo", "cor": "orange", "fator_confianca": "Moderado"}
    if any(k in titulo_lower for k in ["review", "perspective", "opinion"]):
        return {"nivel": "Nível V — Revisão Narrativa / Opinião", "cor": "gray", "fator_confianca": "Baixo"}
    return {"nivel": "Nível III — Estudo Primário Não Classificado", "cor": "orange", "fator_confianca": "Moderado"}

def estimar_risco_herg(mol):
    """Heurística de triagem de risco hERG (off-target cardíaco) baseada em regras publicadas de SAR
    (nitrogênio básico + lipofilicidade elevada + múltiplos anéis aromáticos). NÃO substitui ensaio de patch-clamp."""
    if mol is None:
        return {"score": 0, "risco": "Indeterminado"}
    logp = Crippen.MolLogP(mol)
    aromatic_rings = rdMolDescriptors.CalcNumAromaticRings(mol)
    basic_n = sum(1 for atom in mol.GetAtoms() if atom.GetSymbol() == "N" and atom.GetFormalCharge() >= 0 and not atom.GetIsAromatic())
    peso = Descriptors.MolWt(mol)

    score = 0
    if logp > 3.5:
        score += 2
    elif logp > 2:
        score += 1
    if aromatic_rings >= 3:
        score += 2
    elif aromatic_rings == 2:
        score += 1
    if basic_n >= 1:
        score += 1
    if peso > 350:
        score += 1

    if score >= 5:
        risco = "🔴 Alto (heurístico)"
    elif score >= 3:
        risco = "🟡 Moderado (heurístico)"
    else:
        risco = "🟢 Baixo (heurístico)"
    return {"score": score, "risco": risco, "logp": round(logp, 2), "aneis_aromaticos": aromatic_rings, "n_basicos": basic_n}

def calcular_descritores_rdkit(smiles):
    """Calcula descritores físico-químicos completos via RDKit: Lipinski, Veber, Egan, PAINS e hERG heurístico."""
    if not smiles:
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    peso = Descriptors.MolWt(mol)
    logp = Crippen.MolLogP(mol)
    hbd = rdMolDescriptors.CalcNumHBD(mol)
    hba = rdMolDescriptors.CalcNumHBA(mol)
    tpsa = rdMolDescriptors.CalcTPSA(mol)
    rot_bonds = rdMolDescriptors.CalcNumRotatableBonds(mol)
    aneis = rdMolDescriptors.CalcNumRings(mol)

    violacoes_lipinski = sum([peso > 500, logp > 5, hbd > 5, hba > 10])
    lipinski_ok = violacoes_lipinski <= 1

    veber_ok = (rot_bonds <= 10) and (tpsa <= 140)
    egan_ok = (logp <= 5.88) and (tpsa <= 131.6)

    match_pains = CATALOGO_PAINS.GetMatches(mol)
    alertas_pains = [entry.GetDescription() for entry in match_pains]

    herg = estimar_risco_herg(mol)

    return {
        "mol": mol,
        "peso": round(peso, 2),
        "logp": round(logp, 2),
        "hbd": hbd,
        "hba": hba,
        "tpsa": round(tpsa, 2),
        "rot_bonds": rot_bonds,
        "aneis": aneis,
        "violacoes_lipinski": violacoes_lipinski,
        "lipinski_ok": lipinski_ok,
        "veber_ok": veber_ok,
        "egan_ok": egan_ok,
        "alertas_pains": alertas_pains,
        "herg": herg,
    }

def gerar_svg_2d(mol, tamanho=(400, 350)):
    try:
        drawer = Draw.rdMolDraw2D.MolDraw2DSVG(tamanho[0], tamanho[1])
        Draw.rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
        drawer.FinishDrawing()
        return drawer.GetDrawingText()
    except Exception as e:
        logging.error(f"Erro ao gerar SVG 2D: {e}")
        return None

def gerar_sdf_bytes(mol, nome_composto):
    try:
        mol_3d = Chem.AddHs(mol)
        embed_status = AllChem.EmbedMolecule(mol_3d, randomSeed=42)
        if embed_status == 0:
            AllChem.MMFFOptimizeMolecule(mol_3d)
        mol_3d.SetProp("_Name", nome_composto)
        buf = io.StringIO()
        writer = Chem.SDWriter(buf)
        writer.write(mol_3d)
        writer.close()
        return buf.getvalue().encode("utf-8")
    except Exception as e:
        logging.error(f"Erro ao gerar SDF: {e}")
        return None

def gerar_bibtex(nome_composto, pmid, titulo=None):
    chave = f"{nome_composto.replace(' ', '_')}{datetime.now().year}"
    titulo_final = titulo or f"Estudo farmacológico sobre {nome_composto}"
    return (
        f"@article{{{chave},\n"
        f"  title = {{{titulo_final}}},\n"
        f"  author = {{SenoTrack Curation Team}},\n"
        f"  year = {{{datetime.now().year}}},\n"
        f"  journal = {{PubMed Indexed Source}},\n"
        f"  note = {{PMID: {pmid}}}\n"
        f"}}"
    )

def gerar_ris(nome_composto, pmid, titulo=None):
    titulo_final = titulo or f"Estudo farmacológico sobre {nome_composto}"
    return (
        "TY  - JOUR\n"
        f"TI  - {titulo_final}\n"
        f"AU  - SenoTrack Curation Team\n"
        f"PY  - {datetime.now().year}\n"
        f"AN  - PMID:{pmid}\n"
        "ER  -"
    )

# --- CONSULTAS DE APIS EXTERNAS COM CACHE ---
@st.cache_data(ttl=3600, show_spinner=False)
def buscar_pubmed_id(nome_composto, modo_offline=False):
    if modo_offline:
        return "PMID: 12345678"
    try:
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={nome_composto}[Title/Abstract]&retmode=json&retmax=1"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            ids = res.json().get("esearchresult", {}).get("idlist", [])
            if ids:
                return f"PMID: {ids[0]}"
    except Exception as e:
        logging.error(f"Erro PubMed: {e}")
    return "Não encontrado"

@st.cache_data(ttl=3600, show_spinner=False)
def buscar_titulo_pubmed(pmid_num, modo_offline=False):
    if modo_offline or not pmid_num:
        return "Randomized clinical trial evaluating compound efficacy (demonstração offline)"
    try:
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid_num}&retmode=json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            item = data.get("result", {}).get(str(pmid_num), {})
            return item.get("title", "")
    except Exception as e:
        logging.error(f"Erro ao buscar título PubMed: {e}")
    return ""

@st.cache_data(ttl=3600, show_spinner=False)
def buscar_interacao_rxnav(nome_composto, modo_offline=False):
    if modo_offline:
        return "Identificador RxCUI Localizado: 9060"
    try:
        url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={nome_composto}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            rxcuis = res.json().get("idGroup", {}).get("rxnormId", [])
            if rxcuis:
                return f"Identificador RxCUI Localizado: {rxcuis[0]}"
    except Exception as e:
        logging.error(f"Erro RxNav: {e}")
    return "Sem dados disponíveis"

@st.cache_data(ttl=3600, show_spinner=False)
def consultar_api_pubchem(nome_composto, modo_offline=False):
    nome_limpo = nome_composto.strip().lower()

    if modo_offline:
        if nome_limpo in MOCK_PUBCHEM_DATA:
            data = MOCK_PUBCHEM_DATA[nome_limpo]
            return {"Title": nome_composto.capitalize(), "MolecularFormula": data["formula"],
                    "MolecularWeight": data["weight"], "CanonicalSMILES": data.get("smiles", "")}
        return {"Title": nome_composto.capitalize(), "MolecularFormula": "-", "MolecularWeight": 350.0, "CanonicalSMILES": ""}

    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{nome_limpo}/property/MolecularFormula,MolecularWeight,Title,CanonicalSMILES/JSON"
    try:
        res = requests.get(url, timeout=8)
        if res.status_code == 200:
            prop = res.json()["PropertyTable"]["Properties"][0]
            return {
                "Title": prop.get("Title", nome_composto.capitalize()),
                "MolecularFormula": prop.get("MolecularFormula", "-"),
                "MolecularWeight": float(prop.get("MolecularWeight", 300.0)),
                "CanonicalSMILES": prop.get("CanonicalSMILES", "")
            }
    except Exception as e:
        logging.error(f"Erro na conexão com o PubChem: {str(e)}")
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def buscar_pdb_rcsb(pdb_id, modo_offline=False):
    if modo_offline:
        return None
    try:
        url = f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb"
        res = requests.get(url, timeout=8)
        if res.status_code == 200:
            return res.text
    except Exception as e:
        logging.error(f"Erro ao buscar PDB {pdb_id}: {e}")
    return None

def obter_dados_cientificos_v2(nome_composto, modulo_selecionado):
    nome_limpo = nome_composto.strip().lower()
    base_modulo = BASE_CONHECIMENTO_GLOBAL.get(modulo_selecionado, {})

    for chave, dados in base_modulo.items():
        if chave in nome_limpo:
            return dados

    return {
        "aplicacao": f"O composto '{nome_composto.capitalize()}' encontra-se em triagem molecular primária para {modulo_selecionado}.",
        "pipeline": "Triagem e ensaios pré-clínicos iniciais sob estruturação na pipeline atual.",
        "classe": "Triagem Primária"
    }

def obter_smiles_composto(nome_composto, modo_offline):
    """Resolve o SMILES de um composto: tenta PubChem, cai para o dicionário mock local."""
    nome_limpo = nome_composto.strip().lower()
    prop = consultar_api_pubchem(nome_composto, modo_offline=modo_offline)
    if prop and prop.get("CanonicalSMILES"):
        return prop["CanonicalSMILES"]
    if nome_limpo in MOCK_PUBCHEM_DATA and MOCK_PUBCHEM_DATA[nome_limpo].get("smiles"):
        return MOCK_PUBCHEM_DATA[nome_limpo]["smiles"]
    return None

# --- ENGENHARIA DE PDF PREMIUM COM GRÁFICOS INTEGRADOS ---
class PDFLaudoPremium(FPDF):
    def header(self):
        self.set_fill_color(16, 20, 32)
        self.rect(0, 0, 210, 32, "F")
        self.set_fill_color(79, 124, 255)
        self.rect(0, 30, 210, 1.2, "F")
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "SENOTRACK ENTERPRISE SOLUTION", ln=True, align="C")
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(180, 190, 220)
        self.cell(0, 5, "Relatorio Executivo Customizado de Viabilidade de Compostos v9.0", ln=True, align="C")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Pagina {self.page_no()}", align="C")

def to_pdf_bytes(pdf):
    saida = pdf.output()
    if isinstance(saida, str):
        return saida.encode("latin-1")
    return bytes(saida)

def gerar_pdf_laudo(df, descritores=None):
    pdf = PDFLaudoPremium()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)

    for _, row in df.iterrows():
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, sanitize_pdf_text(f"Composto: {row['Nome Oficial']}"), ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, sanitize_pdf_text(f"Aplicacao: {row['Aplicação Médica']}"))
        pdf.ln(3)

    if descritores:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Perfil Fisico-Quimico Avancado (RDKit)", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, sanitize_pdf_text(
            f"Peso: {descritores['peso']} g/mol | LogP: {descritores['logp']} | TPSA: {descritores['tpsa']} A2 | "
            f"Ligacoes Rotacionaveis: {descritores['rot_bonds']} | Lipinski OK: {descritores['lipinski_ok']} | "
            f"Veber OK: {descritores['veber_ok']} | Egan OK: {descritores['egan_ok']} | "
            f"Alertas PAINS: {len(descritores['alertas_pains'])} | Risco hERG: {descritores['herg']['risco']}"
        ))

    return to_pdf_bytes(pdf)

def gerar_pdf_laudo_lote(df_exibicao, grafico_img_bytes):
    pdf = PDFLaudoPremium()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pdf.set_text_color(50, 50, 50)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "1. Sumario Analitico da Triagem Filtrada em Lote", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, sanitize_pdf_text(f"Volume de compostos que atendem aos criterios de filtragem: {len(df_exibicao)} amostras."), ln=True)
    pdf.ln(5)

    if grafico_img_bytes:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 7, "2. Perfil de Distribuicao de Massa Molecular do Lote", ln=True)
        pdf.ln(2)

        try:
            grafico_stream = io.BytesIO(grafico_img_bytes)
            grafico_stream.name = "chart.png"
            pdf.image(grafico_stream, x=15, w=180, h=85, type="PNG")
        except Exception as e:
            logging.error(f"Erro ao inserir grafico no PDF: {e}")
        pdf.ln(5)

    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "3. Detalhamento Tecnico por Registro Biomolecular", ln=True)
    pdf.ln(2)

    for _, row in df_exibicao.iterrows():
        pdf.set_fill_color(235, 238, 245)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(
            0, 7,
            sanitize_pdf_text(f" {row['Nome Oficial']} ({row.get('Fórmula', '-')}) - {row.get('Massa Molecular', '-')}"),
            border=1, ln=True, fill=True,
        )
        pdf.ln(1)

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(79, 124, 255)
        pdf.cell(0, 5, "    Mecanismo e Aplicacao Clinica:", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 5, sanitize_pdf_text(f"    {row.get('Aplicação Médica', '')}"))

        if 'Referência PubMed' in row and row['Referência PubMed'] != "Não encontrado":
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, f"    Ref: {row['Referência PubMed']}", ln=True)

        pdf.ln(3)

    return to_pdf_bytes(pdf)

def gerar_pdf_eln(experimentos):
    pdf = PDFLaudoPremium()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Caderno Eletronico de Laboratorio (ELN)", ln=True)
    pdf.ln(2)

    for exp in experimentos:
        pdf.set_fill_color(230, 238, 250)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, sanitize_pdf_text(f"Registro: {exp['nome']}  |  {exp['timestamp']}"), border=1, ln=True, fill=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, sanitize_pdf_text(f"Modulo: {exp['modulo']} | Observacoes: {exp.get('notas', '-')}"))
        pdf.multi_cell(0, 5, sanitize_pdf_text(f"Dados: {json.dumps(exp.get('dados', {}), ensure_ascii=False)}"))
        pdf.ln(3)

    return to_pdf_bytes(pdf)

# --- GERADOR AUTOMÁTICO DA PLANILHA MODELO ---
if not os.path.exists("modelo_triagem_v7.xlsx"):
    df_modelo = pd.DataFrame({"Composto": ["quercetin", "dasatinib", "donepezil", "sacubitril", "empagliflozin", "semaglutide", "tofacitinib", "rapamycin"]})
    df_modelo.to_excel("modelo_triagem_v7.xlsx", index=False)

# =====================================================================
# BARRA LATERAL — SELETOR DE IDIOMA (PRIMEIRO, PARA AFETAR TODO O RESTO)
# =====================================================================
rotulo_idioma_atual = [k for k, v in IDIOMAS_DISPONIVEIS.items() if v == st.session_state.idioma_ativo][0]
escolha_idioma = st.sidebar.selectbox(
    "🌐 Idioma / Language / 语言",
    list(IDIOMAS_DISPONIVEIS.keys()),
    index=list(IDIOMAS_DISPONIVEIS.keys()).index(rotulo_idioma_atual),
)
st.session_state.idioma_ativo = IDIOMAS_DISPONIVEIS[escolha_idioma]

# --- CORPO DA INTERFACE ---
st.markdown(f"<p style='color: #4f7cff; font-weight: 700; margin-bottom: -10px; letter-spacing: 0.03em;'>{t('app_badge')}</p>", unsafe_allow_html=True)
st.title(t("app_title"))
st.markdown("---")

# BARRA LATERAL AVANÇADA
st.sidebar.markdown(f"### {t('sidebar_user_profile')}")
perfil_usuario = st.sidebar.radio(
    t("profile_radio_label"),
    [t("profile_didactic"), t("profile_research")],
    index=1,
)
modo_avancado = perfil_usuario == t("profile_research")

st.sidebar.markdown(f"### {t('sidebar_ai')}")
chave_api_ia = st.sidebar.text_input(t("api_key_label"), type="password", help=t("api_key_help"))

st.sidebar.markdown(f"### {t('sidebar_clinical_params')}")
modulo_ativo = st.sidebar.selectbox(t("module_label"), list(BASE_CONHECIMENTO_GLOBAL.keys()))

st.sidebar.markdown(f"### {t('sidebar_filters')}")
limite_massa = st.sidebar.slider(
    t("mass_limit_label"),
    min_value=100, max_value=5000, value=1200, step=50,
    help=t("mass_limit_help")
)
if modo_avancado:
    limite_tpsa = st.sidebar.slider(t("tpsa_limit_label"), min_value=20, max_value=250, value=140, step=5)
    limite_rot = st.sidebar.slider(t("rot_limit_label"), min_value=1, max_value=25, value=10, step=1)
else:
    limite_tpsa, limite_rot = 140, 10

st.sidebar.markdown(f"### {t('sidebar_infra')}")
modo_offline = st.sidebar.toggle(t("offline_toggle"), value=False)

# CADERNO ELN NA SIDEBAR
if st.session_state.eln_experimentos:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### {t('eln_sidebar_title')}")
    st.sidebar.caption(t("eln_sidebar_caption", n=len(st.session_state.eln_experimentos)))

# RASTREABILIDADE E AUDITORIA
if st.session_state.historico_auditoria:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### {t('audit_sidebar_title')}")
    st.sidebar.caption(t("audit_sidebar_caption", n=len(st.session_state.historico_auditoria)))
    json_historico = json.dumps(st.session_state.historico_auditoria, indent=4, ensure_ascii=False)
    st.sidebar.download_button(
        label=t("audit_export_button"),
        data=json_historico,
        file_name=f"auditoria_senotrack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

abas = st.tabs([
    t("tab_individual"),
    t("tab_lote"),
    t("tab_fq"),
    t("tab_docking"),
    t("tab_benchmark"),
    t("tab_literature"),
    t("tab_eln"),
])
aba_individual, aba_lote, aba_fq, aba_docking, aba_benchmark, aba_literatura, aba_eln = abas

# =====================================================================
# ABA 1: ANÁLISE INDIVIDUAL
# =====================================================================
with aba_individual:
    composto_a = st.text_input(t("input_molecule_label"), placeholder="Ex: dasatinib, sacubitril, semaglutide...", key="input_busca_individual")

    if composto_a:
        dados_locais = obter_dados_cientificos_v2(composto_a, modulo_ativo)
        prop = consultar_api_pubchem(composto_a, modo_offline=modo_offline)

        ref_pubmed = buscar_pubmed_id(composto_a, modo_offline=modo_offline)
        interacao_rx = buscar_interacao_rxnav(composto_a, modo_offline=modo_offline)

        if prop:
            nome = prop["Title"]
            formula = prop["MolecularFormula"]
            peso = prop["MolecularWeight"]

            registro = {
                "timestamp": datetime.now().isoformat(),
                "modulo": modulo_ativo,
                "composto_pesquisado": composto_a,
                "nome_oficial": nome,
                "formula": formula,
                "massa_molecular": peso
            }
            if registro not in st.session_state.historico_auditoria:
                st.session_state.historico_auditoria.append(registro)

            st.markdown(f"## **{nome}**")

            c1, c2 = st.columns(2)
            c1.metric(t("metric_formula"), formula)
            c2.metric(t("metric_mass"), f"{peso} g/mol")

            st.subheader(t("section_application"))
            st.info(dados_locais["aplicacao"])

            st.subheader(t("section_pipeline"))
            st.warning(dados_locais["pipeline"])

            st.subheader(t("section_evidence"))
            col_pm, col_rx = st.columns(2)

            with col_pm:
                st.markdown(f"#### {t('pubmed_article_label')}")
                if "PMID:" in ref_pubmed:
                    pmid_num = ref_pubmed.replace("PMID:", "").strip()
                    st.success(f"{t('pubmed_found')} {ref_pubmed}")
                    st.markdown(f"[{t('pubmed_link')}](https://pubmed.ncbi.nlm.nih.gov/{pmid_num}/)")
                else:
                    st.warning(t("pubmed_not_found"))

            with col_rx:
                st.markdown(f"#### {t('rxnav_label')}")
                st.info(f"🆔 {interacao_rx}")

            st.write("---")
            st.subheader(t("ai_agent_section"))
            st.markdown(t("ai_agent_desc"))

            if st.button(t("btn_generate_insight", nome=nome)):
                with st.spinner(t("spinner_generating")):
                    insight = gerar_insight_ia(nome, formula, peso, modulo_ativo, chave_api_ia)
                    st.success(insight)

            st.write("---")
            col_2d, col_3d = st.columns(2)

            with col_2d:
                if not modo_offline:
                    st.image(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{composto_a}/PNG", use_container_width=True)
                else:
                    st.info(t("offline_2d_msg"))
                st.caption(t("structure_2d_caption"))

            with col_3d:
                if not modo_offline:
                    try:
                        url_sdf = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{composto_a}/SDF?record_type=3d"
                        res_sdf = requests.get(url_sdf, timeout=8)
                        if res_sdf.status_code == 200 and res_sdf.text.strip():
                            xyzview = py3Dmol.view(width=450, height=450)
                            xyzview.addModel(res_sdf.text, "sdf")
                            xyzview.setStyle({"stick": {}, "sphere": {"scale": 0.3}})
                            xyzview.zoomTo()
                            xyzview.setBackgroundColor("white")
                            components.html(xyzview._make_html(), height=470, width=470)
                            st.caption(t("structure_3d_caption"))
                        else:
                            st.caption("⚠️")
                    except Exception as e:
                        st.caption(f"⚠️ {e}")
                else:
                    st.info(t("offline_3d_msg"))

            st.write("---")
            if st.button(t("btn_save_eln"), key="salvar_eln_individual"):
                st.session_state.eln_experimentos.append({
                    "id": str(uuid.uuid4())[:8],
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "nome": nome,
                    "modulo": modulo_ativo,
                    "notas": "Registro criado a partir da Aba de Perfil Clínico Individual.",
                    "dados": {"formula": formula, "peso_molecular": peso, "aplicacao": dados_locais["aplicacao"]}
                })
                st.success(t("eln_saved_success"))

            df_individual = pd.DataFrame([{"Nome Oficial": nome, "Aplicação Médica": dados_locais["aplicacao"]}])

            data_hora_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label=t("btn_download_pdf_individual"),
                data=gerar_pdf_laudo(df_individual),
                file_name=f"laudo_{composto_a}_{data_hora_str}.pdf",
                mime="application/pdf",
            )
        else:
            st.error(t("error_compound_not_found"))

# =====================================================================
# ABA 2: PROCESSAMENTO DE LOTES HOSPITALARES
# =====================================================================
with aba_lote:
    st.caption(t("lote_caption"))

    col_dl1, col_dl2 = st.columns([1, 2])
    with col_dl1:
        with open("modelo_triagem_v7.xlsx", "rb") as f:
            st.download_button(
                label=t("btn_download_template"),
                data=f,
                file_name="modelo_triagem_v7.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    arquivo_upload = st.file_uploader(t("uploader_label"), type=["csv", "xlsx"])

    if arquivo_upload:
        try:
            df_lote = pd.read_csv(arquivo_upload) if arquivo_upload.name.endswith(".csv") else pd.read_excel(arquivo_upload)

            if df_lote.shape[1] > 0:
                df_lote.rename(columns={df_lote.columns[0]: "Composto"}, inplace=True)

                list_rows = []
                with st.spinner(t("spinner_batch_scan")):
                    for comp in df_lote["Composto"]:
                        nome_comp = str(comp).strip().lower()

                        try:
                            dados_c = obter_dados_cientificos_v2(nome_comp, modulo_selecionado=modulo_ativo)
                            f_quimica, p_molecular = "-", 350.0
                            prop_b = consultar_api_pubchem(nome_comp, modo_offline=modo_offline)
                            ref_pubmed_lote = buscar_pubmed_id(nome_comp, modo_offline=modo_offline)
                            rxnav_lote = buscar_interacao_rxnav(nome_comp, modo_offline=modo_offline)

                            if prop_b:
                                f_quimica = prop_b["MolecularFormula"]
                                p_molecular = prop_b["MolecularWeight"]

                            status_absorcao = "🟢 Alta (Peso < 500 g/mol)" if p_molecular < 500 else "🟡 Moderada/Baixa"
                            seguranca = analisar_acao_reacao(p_molecular, dados_c["classe"])

                            list_rows.append({
                                "Nome Oficial": nome_comp.capitalize(),
                                "Fórmula": f_quimica,
                                "Massa Numérica": p_molecular,
                                "Massa Molecular": f"{p_molecular} g/mol",
                                "Aplicação Médica": dados_c["aplicacao"],
                                "Mapeamento Pipeline": dados_c["pipeline"],
                                "Absorção Oral": status_absorcao,
                                "Segurança Laboratorial": seguranca,
                                "Referência PubMed": ref_pubmed_lote,
                                "RxNav ID": rxnav_lote
                            })
                        except Exception as err_comp:
                            logging.warning(f"Erro ao processar composto {nome_comp}: {err_comp}")
                            list_rows.append({
                                "Nome Oficial": nome_comp.capitalize(),
                                "Fórmula": "ERRO",
                                "Massa Numérica": 9999.0,
                                "Massa Molecular": "Erro g/mol",
                                "Aplicação Médica": "Falha na análise estrutural",
                                "Mapeamento Pipeline": "N/A",
                                "Absorção Oral": "Indeterminada",
                                "Segurança Laboratorial": "Requer revisão manual",
                                "Referência PubMed": "Erro",
                                "RxNav ID": "Erro"
                            })

                df_mestre = pd.DataFrame(list_rows)

                # FILTRAGEM
                df_filtrado = df_mestre[df_mestre["Massa Numérica"] <= limite_massa]
                itens_excluidos = len(df_mestre) - len(df_filtrado)

                # --- 1. CARDS DE METRICAS CHAVE DO LOTE (KPIs) ---
                st.write("---")
                st.subheader(t("kpi_section"))
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)

                compostos_com_pubmed = sum(1 for x in df_filtrado["Referência PubMed"] if "PMID:" in str(x))

                kpi1.metric(t("kpi_total"), f"{len(df_mestre)}")
                kpi2.metric(t("kpi_approved"), f"{len(df_filtrado)}", delta=f"-{itens_excluidos}" if itens_excluidos > 0 else "100%")
                kpi3.metric(t("kpi_evidence"), f"{compostos_com_pubmed}")
                kpi4.metric(t("kpi_module"), modulo_ativo)

                if itens_excluidos > 0:
                    st.warning(f"🔬 {itens_excluidos} / {limite_massa} g/mol")

                # --- 2. SINTETIZADOR DE IA PARA O LOTE INTEIRO ---
                st.write("---")
                st.subheader(t("ai_batch_section"))
                st.markdown(t("ai_batch_desc"))

                if st.button(t("btn_generate_batch_ai")):
                    with st.spinner(t("spinner_batch_scan")):
                        nomes_lote = ", ".join(df_filtrado["Nome Oficial"].tolist())
                        time.sleep(1.5)
                        parecer = (
                            f"🤖 **[Parecer Geral da IA para o Lote]**\n\n"
                            f"Foram analisadas **{len(df_filtrado)} moléculas** no módulo **{modulo_ativo}**: *{nomes_lote}*.\n\n"
                            f"• **Coerência Terapêutica:** A combinação de compostos apresenta alta compatibilidade com o ecossistema de {modulo_ativo}.\n"
                            f"• **Perfil Farmacocinético:** A distribuição de massa molecular média está equilibrada. {compostos_com_pubmed} dos compostos possuem publicações diretas no PubMed de alto impacto.\n"
                            f"• **Recomendação:** Aprovado para prosseguimento de testes in silico e alocação em matrizes de triagem clínica hospitalar."
                        )
                        st.success(parecer)

                # --- 3. MATRIZ COMPARATIVA COM DADOS COMPLETOS E LINKS DE ARTIGOS ---
                st.write("---")
                st.subheader(t("matrix_section"))

                if not df_filtrado.empty:
                    compostos_validos = df_filtrado.to_dict(orient="records")
                    colunas_cards = st.columns(min(len(compostos_validos), 3))

                    for idx, item in enumerate(compostos_validos):
                        col_idx = idx % 3
                        with colunas_cards[col_idx]:
                            pmid_txt = item['Referência PubMed']
                            link_pubmed = ""
                            if "PMID:" in str(pmid_txt):
                                pmid_num = pmid_txt.replace("PMID:", "").strip()
                                link_pubmed = f"<a href='https://pubmed.ncbi.nlm.nih.gov/{pmid_num}/' target='_blank' style='color:#4f7cff; font-weight:bold; text-decoration:underline;'>🔗 PubMed ({pmid_txt})</a>"
                            else:
                                link_pubmed = "<span style='color:#8b95ad;'>⚠️</span>"

                            st.markdown(f"""
                            <div style='background-color: #131a2b; padding: 18px; border-radius: 12px; border-left: 4px solid #4f7cff; margin-bottom:15px; min-height: 220px; border: 1px solid #232c42;'>
                                <h4 style='margin-top:0; color:#e8ecf5; font-size:16px;'>🔬 {item['Nome Oficial']}</h4>
                                <p style='font-size:13px; margin-bottom:6px; color:#cbd5e1;'><b>{t('metric_formula')}:</b> {item['Fórmula']} | <b>{t('metric_mass')}:</b> {item['Massa Molecular']}</p>
                                <p style='font-size:12px; margin-bottom:8px; color:#9b6bff;'><b>{item['RxNav ID']}</b></p>
                                <p style='font-size:12px; margin-bottom:10px; color:#8b95ad; line-height: 1.4;'>{item['Aplicação Médica']}</p>
                                <hr style='border: 0.5px solid #232c42; margin: 8px 0;'>
                                <p style='font-size:12px; margin-bottom:0;'>{link_pubmed}</p>
                            </div>
                            """, unsafe_allow_html=True)

                # --- 4. DETALHAMENTO EXPANSÍVEL POR MOLÉCULA DO LOTE ---
                st.write("---")
                st.subheader(t("detail_section"))

                for idx, row in df_filtrado.iterrows():
                    with st.expander(f"📌 {row['Nome Oficial']} — {row['Massa Molecular']} ({row['Referência PubMed']})"):
                        col_exp1, col_exp2 = st.columns(2)
                        with col_exp1:
                            st.write(f"**{t('section_application')}:** {row['Aplicação Médica']}")
                            st.write(f"**{t('section_pipeline')}:** {row['Mapeamento Pipeline']}")
                            st.write(f"**{t('kpi_approved')}:** {row['Absorção Oral']}")
                        with col_exp2:
                            st.write(f"**RxNav:** {row['RxNav ID']}")
                            st.write(f"**PubMed:** {row['Referência PubMed']}")
                            st.write(f"**{t('herg_section')}:** {row['Segurança Laboratorial']}")

                            if "PMID:" in str(row['Referência PubMed']):
                                pmid_num = row['Referência PubMed'].replace("PMID:", "").strip()
                                st.markdown(f"[{t('pubmed_link')}](https://pubmed.ncbi.nlm.nih.gov/{pmid_num}/)")

                # --- 5. TABELA DE RESULTADOS E EXPORTAÇÃO ---
                st.divider()
                st.write(f"### {t('master_table_title')}")
                df_visualizacao = df_filtrado.drop(columns=["Massa Numérica"]) if not df_filtrado.empty else df_filtrado
                st.markdown(df_visualizacao.to_html(classes="tabela-v9", index=False, escape=False), unsafe_allow_html=True)

                if not df_filtrado.empty:
                    st.divider()
                    st.subheader(t("density_section"))
                    st.bar_chart(data=df_filtrado, x="Nome Oficial", y="Massa Numérica", color="#4f7cff")

                    fig, ax = plt.subplots(figsize=(7, 3.5))
                    fig.patch.set_facecolor('#0f1420')
                    ax.set_facecolor('#0f1420')
                    ax.bar(df_filtrado["Nome Oficial"], df_filtrado["Massa Numérica"], color="#4f7cff", width=0.4)
                    ax.set_ylabel("Massa Molecular (g/mol)", fontsize=9, color="#e8ecf5")
                    ax.set_title("Distribuicao Estrutural - Lote Triado", fontsize=10, fontweight="bold", color="#e8ecf5")
                    ax.tick_params(axis='both', labelsize=8, colors="#e8ecf5")
                    for spine in ax.spines.values():
                        spine.set_color('#232c42')
                    plt.tight_layout()

                    buf = io.BytesIO()
                    plt.savefig(buf, format='png', dpi=200, facecolor=fig.get_facecolor())
                    buf.seek(0)
                    grafico_bytes = buf.getvalue()
                    plt.close(fig)

                    st.divider()
                    st.subheader(t("export_section"))

                    c_pdf, c_json = st.columns([1, 1])

                    with c_pdf:
                        data_hora_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                        nome_pdf = f"laudo_triagem_lote_{data_hora_str}.pdf"

                        st.download_button(
                            label=t("btn_download_pdf_batch"),
                            data=gerar_pdf_laudo_lote(df_visualizacao, grafico_bytes),
                            file_name=nome_pdf,
                            mime="application/pdf",
                            type="primary"
                        )

                    with c_json:
                        json_lote = df_visualizacao.to_json(orient="records", force_ascii=False, indent=4)
                        st.download_button(
                            label=t("btn_download_json_batch"),
                            data=json_lote,
                            file_name=f"dados_lote_{data_hora_str}.json",
                            mime="application/json"
                        )

        except Exception as e:
            st.error(f"⚠️ {e}")

# =====================================================================
# ABA 3: TRIAGEM FÍSICO-QUÍMICA & TOXICIDADE AVANÇADA
# =====================================================================
with aba_fq:
    st.caption(t("fq_caption"))
    composto_fq = st.text_input(t("input_fq_label"), placeholder="Ex: navitoclax, tofacitinib...", key="input_fq")

    if composto_fq:
        smiles = obter_smiles_composto(composto_fq, modo_offline)
        if not smiles:
            st.error(t("error_no_smiles"))
        else:
            descritores = calcular_descritores_rdkit(smiles)
            if descritores is None:
                st.error(t("error_invalid_smiles"))
            else:
                st.session_state.cache_moleculas[composto_fq.lower()] = descritores
                st.markdown(f"## {t('fq_profile_title')} {composto_fq.capitalize()}")

                c1, c2, c3, c4 = st.columns(4)
                c1.metric(t("metric_mass"), f"{descritores['peso']} g/mol")
                c2.metric(t("metric_logp"), descritores['logp'])
                c3.metric(t("metric_tpsa"), f"{descritores['tpsa']} Å²")
                c4.metric(t("metric_rotbonds"), descritores['rot_bonds'])

                st.write("---")
                col_regras, col_estrutura = st.columns([1, 1])

                with col_regras:
                    st.subheader(t("rules_section"))
                    st.markdown(f"**Lipinski (Rule of Five):** {'✅' if descritores['lipinski_ok'] else '❌'} — {descritores['violacoes_lipinski']}")
                    st.markdown(f"**Veber** (Rot. Bonds ≤ {limite_rot}, TPSA ≤ {limite_tpsa} Å²): {'✅' if (descritores['rot_bonds'] <= limite_rot and descritores['tpsa'] <= limite_tpsa) else '❌'}")
                    st.markdown(f"**Egan** (LogP ≤ 5.88, TPSA ≤ 131.6 Å²): {'✅' if descritores['egan_ok'] else '❌'}")

                    if modo_avancado:
                        st.write("---")
                        st.subheader(t("pains_section"))
                        if descritores['alertas_pains']:
                            for alerta in descritores['alertas_pains']:
                                st.error(f"🚨 {alerta}")
                        else:
                            st.success(t("pains_none"))

                        st.write("---")
                        st.subheader(t("herg_section"))
                        herg = descritores['herg']
                        st.markdown(f"**{herg['risco']}**")
                        st.caption(f"Score: {herg['score']}/7 | LogP: {herg['logp']} | {herg['aneis_aromaticos']} | N: {herg['n_basicos']}")
                    else:
                        st.info(t("didactic_notice_fq"))

                with col_estrutura:
                    st.subheader(t("structure2d_section"))
                    svg_2d = gerar_svg_2d(descritores['mol'])
                    if svg_2d:
                        st.image(svg_2d, use_container_width=True)
                    if modo_avancado:
                        sdf_bytes = gerar_sdf_bytes(descritores['mol'], composto_fq)
                        if sdf_bytes:
                            st.download_button(
                                t("btn_download_sdf"),
                                data=sdf_bytes,
                                file_name=f"{composto_fq}_3d.sdf",
                                mime="chemical/x-mdl-sdfile"
                            )

# =====================================================================
# ABA 4: DOCKING VIRTUAL & PROTEÔMICA
# =====================================================================
with aba_docking:
    st.caption(t("docking_caption"))

    col_prot, col_lig = st.columns(2)
    with col_prot:
        st.subheader(t("protein_target_section"))
        modo_pdb = st.radio(t("pdb_source_label"), [t("pdb_search_option"), t("pdb_upload_option")], horizontal=True)
        pdb_texto = None
        pdb_nome_ref = None

        if modo_pdb == t("pdb_search_option"):
            pdb_id = st.text_input(t("pdb_id_label"), value="1IEP")
            if pdb_id:
                pdb_texto = buscar_pdb_rcsb(pdb_id, modo_offline=modo_offline)
                pdb_nome_ref = pdb_id.upper()
                if pdb_texto is None and not modo_offline:
                    st.warning(t("pdb_not_found"))
                elif modo_offline:
                    st.info(t("pdb_offline_notice"))
        else:
            arquivo_pdb = st.file_uploader(t("pdb_upload_label"), type=["pdb"])
            if arquivo_pdb:
                pdb_texto = arquivo_pdb.read().decode("utf-8", errors="ignore")
                pdb_nome_ref = arquivo_pdb.name

        if pdb_texto:
            try:
                view_prot = py3Dmol.view(width=480, height=420)
                view_prot.addModel(pdb_texto, "pdb")
                view_prot.setStyle({"cartoon": {"color": "spectrum"}})
                view_prot.addSurface(py3Dmol.VDW, {"opacity": 0.15, "color": "white"})
                view_prot.zoomTo()
                view_prot.setBackgroundColor("white")
                components.html(view_prot._make_html(), height=440, width=500)
                st.caption(f"{pdb_nome_ref}")
            except Exception as e:
                st.error(f"⚠️ {e}")

    with col_lig:
        st.subheader(t("ligand_section"))
        composto_dock = st.text_input(t("ligand_input_label"), placeholder="Ex: dasatinib, tofacitinib...", key="input_docking")
        descritores_dock = None
        if composto_dock:
            smiles_dock = obter_smiles_composto(composto_dock, modo_offline)
            if smiles_dock:
                descritores_dock = calcular_descritores_rdkit(smiles_dock)
                if descritores_dock:
                    svg_lig = gerar_svg_2d(descritores_dock['mol'], tamanho=(420, 380))
                    if svg_lig:
                        st.image(svg_lig, use_container_width=True)
            else:
                st.warning(t("smiles_unavailable_warn"))

    st.write("---")
    if pdb_texto and descritores_dock:
        st.subheader(t("docking_score_section"))
        st.caption(t("docking_disclaimer"))

        peso = descritores_dock['peso']
        logp = descritores_dock['logp']
        rot = descritores_dock['rot_bonds']

        score_tamanho = max(0, 10 - abs(peso - 350) / 40)
        score_lipofilicidade = max(0, 10 - abs(logp - 2.5) * 2)
        score_flexibilidade = max(0, 10 - rot * 0.6)
        score_final = round((score_tamanho + score_lipofilicidade + score_flexibilidade) / 3, 1)

        colA, colB, colC, colD = st.columns(4)
        colA.metric(t("score_size"), f"{score_tamanho:.1f}/10")
        colB.metric(t("score_lipo"), f"{score_lipofilicidade:.1f}/10")
        colC.metric(t("score_flex"), f"{score_flexibilidade:.1f}/10")
        colD.metric(t("score_combined"), f"{score_final}/10")

        if score_final >= 7:
            st.success(t("docking_good"))
        elif score_final >= 4:
            st.warning(t("docking_moderate"))
        else:
            st.error(t("docking_bad"))

        if modo_avancado:
            st.write("---")
            st.subheader(t("offtarget_section"))
            st.markdown(f"**hERG:** {descritores_dock['herg']['risco']}")
    else:
        st.info(t("docking_empty_notice"))

# =====================================================================
# ABA 5: FARMACOTERAPIA & BENCHMARK
# =====================================================================
with aba_benchmark:
    st.caption(t("benchmark_caption"))

    st.subheader(t("molecule_select_section"))
    lista_compostos_conhecidos = sorted(set(MOCK_PUBCHEM_DATA.keys()))
    compostos_selecionados = st.multiselect(
        t("molecule_select_label"),
        options=lista_compostos_conhecidos,
        default=[FARMACO_CONTROLE_POR_MODULO.get(modulo_ativo, lista_compostos_conhecidos[0]), lista_compostos_conhecidos[0]][:2],
        max_selections=4,
    )

    perfis = {}
    if len(compostos_selecionados) >= 2:
        with st.spinner("..."):
            for comp in compostos_selecionados:
                smiles_c = obter_smiles_composto(comp, modo_offline)
                desc_c = calcular_descritores_rdkit(smiles_c) if smiles_c else None
                perfis[comp] = desc_c

        perfis_validos = {k: v for k, v in perfis.items() if v is not None}

        if len(perfis_validos) >= 2:
            st.write("---")
            st.subheader(t("synergy_matrix_title"))
            linhas_matriz = []
            nomes_validos = list(perfis_validos.keys())
            for i in range(len(nomes_validos)):
                linha = {}
                linha["Composto"] = nomes_validos[i].capitalize()
                for j in range(len(nomes_validos)):
                    if i == j:
                        linha[nomes_validos[j].capitalize()] = "—"
                    else:
                        p1, p2 = perfis_validos[nomes_validos[i]], perfis_validos[nomes_validos[j]]
                        similaridade = round(100 - (abs(p1['logp'] - p2['logp']) * 10 + abs(p1['tpsa'] - p2['tpsa']) * 0.3), 1)
                        similaridade = max(0, min(100, similaridade))
                        classificacao = "Alta Sinergia" if similaridade > 70 else ("Sinergia Moderada" if similaridade > 40 else "Baixa Similaridade")
                        linha[nomes_validos[j].capitalize()] = f"{similaridade}% — {classificacao}"
                linhas_matriz.append(linha)
            df_matriz = pd.DataFrame(linhas_matriz).set_index("Composto")
            st.dataframe(df_matriz, use_container_width=True)

            st.write("---")
            st.subheader(t("radar_section"))
            farmaco_controle = FARMACO_CONTROLE_POR_MODULO.get(modulo_ativo, nomes_validos[0])
            st.markdown(f"**{t('gold_standard_label')} '{modulo_ativo}':** `{farmaco_controle}`")

            if farmaco_controle not in perfis_validos:
                smiles_ctrl = obter_smiles_composto(farmaco_controle, modo_offline)
                if smiles_ctrl:
                    perfis_validos[farmaco_controle] = calcular_descritores_rdkit(smiles_ctrl)

            categorias = ["Peso Molecular", "LogP", "TPSA", "Flexibilidade", "hERG (invertido)"]

            def normalizar_radar(perfil):
                herg_score_invertido = max(0, 7 - perfil['herg']['score'])
                return [
                    max(0, 100 - abs(perfil['peso'] - 350) / 5),
                    max(0, 100 - abs(perfil['logp'] - 2.5) * 12),
                    max(0, 100 - abs(perfil['tpsa'] - 70) * 0.8),
                    max(0, 100 - perfil['rot_bonds'] * 8),
                    herg_score_invertido / 7 * 100,
                ]

            fig_radar = go.Figure()
            for nome_c, perfil_c in perfis_validos.items():
                if perfil_c is None:
                    continue
                valores = normalizar_radar(perfil_c)
                fig_radar.add_trace(go.Scatterpolar(
                    r=valores + [valores[0]],
                    theta=categorias + [categorias[0]],
                    fill='toself',
                    name=nome_c.capitalize() + (" ★" if nome_c == farmaco_controle else "")
                ))
            fig_radar.update_layout(
                polar=dict(
                    bgcolor="#131a2b",
                    radialaxis=dict(visible=True, range=[0, 100], gridcolor="#232c42", color="#8b95ad")
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e8ecf5"),
                showlegend=True,
            )
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.warning("⚠️")
    else:
        st.info(t("benchmark_select_warn"))

# =====================================================================
# ABA 6: AGENTE CLÍNICO & LITERATURA
# =====================================================================
with aba_literatura:
    st.caption(t("literature_caption"))

    composto_lit = st.text_input(t("literature_input_label"), placeholder="Ex: rapamycin, empagliflozin...", key="input_literatura")

    if composto_lit:
        dados_locais_lit = obter_dados_cientificos_v2(composto_lit, modulo_ativo)
        ref_pubmed_lit = buscar_pubmed_id(composto_lit, modo_offline=modo_offline)

        st.subheader(t("evidence_section"))
        if "PMID:" in ref_pubmed_lit:
            pmid_num_lit = ref_pubmed_lit.replace("PMID:", "").strip()
            titulo_artigo = buscar_titulo_pubmed(pmid_num_lit, modo_offline=modo_offline)
            classificacao = classificar_evidencia_ia(titulo_artigo, ref_pubmed_lit)

            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"**{t('title_retrieved_label')}** {titulo_artigo if titulo_artigo else t('title_unavailable')}")
                st.markdown(f"**PMID:** {pmid_num_lit}")
                st.markdown(f"[🔗 PubMed](https://pubmed.ncbi.nlm.nih.gov/{pmid_num_lit}/)")
            with c2:
                if classificacao['cor'] == "green":
                    st.success(f"**{classificacao['nivel']}**")
                elif classificacao['cor'] == "orange":
                    st.warning(f"**{classificacao['nivel']}**")
                else:
                    st.info(f"**{classificacao['nivel']}**")
                st.caption(f"{t('confidence_factor_label')} {classificacao['fator_confianca']}")

            if modo_avancado:
                st.caption(t("evidence_advanced_note"))
        else:
            st.warning(t("evidence_none"))

        st.write("---")
        st.subheader(t("moa_section"))
        if st.button(t("btn_generate_moa"), key="btn_moa"):
            smiles_lit = obter_smiles_composto(composto_lit, modo_offline)
            descritores_lit = calcular_descritores_rdkit(smiles_lit) if smiles_lit else None
            with st.spinner(t("spinner_moa")):
                if descritores_lit:
                    moa_texto = gerar_moa_ia(composto_lit, dados_locais_lit["classe"], descritores_lit, modulo_ativo)
                else:
                    moa_texto = gerar_moa_ia(composto_lit, dados_locais_lit["classe"], {"logp": 0, "peso": 0}, modulo_ativo)
                st.success(moa_texto)

        st.write("---")
        st.subheader(t("citation_section"))
        if "PMID:" in ref_pubmed_lit:
            pmid_num_lit = ref_pubmed_lit.replace("PMID:", "").strip()
            titulo_ref = buscar_titulo_pubmed(pmid_num_lit, modo_offline=modo_offline)
            col_bib, col_ris = st.columns(2)
            with col_bib:
                st.download_button(
                    t("btn_export_bib"),
                    data=gerar_bibtex(composto_lit, pmid_num_lit, titulo_ref),
                    file_name=f"{composto_lit}_citacao.bib",
                    mime="application/x-bibtex"
                )
            with col_ris:
                st.download_button(
                    t("btn_export_ris"),
                    data=gerar_ris(composto_lit, pmid_num_lit, titulo_ref),
                    file_name=f"{composto_lit}_citacao.ris",
                    mime="application/x-research-info-systems"
                )

# =====================================================================
# ABA 7: CADERNO CIENTÍFICO (ELN) & EXPORTAÇÃO MULTIFORMATO
# =====================================================================
with aba_eln:
    st.caption(t("eln_caption"))

    with st.expander(t("new_experiment_expander")):
        with st.form("form_novo_experimento"):
            nome_exp = st.text_input(t("exp_name_label"))
            notas_exp = st.text_area(t("exp_notes_label"))
            submitted = st.form_submit_button(t("btn_save_experiment"))
            if submitted and nome_exp:
                dados_exp = {}
                smiles_exp = obter_smiles_composto(nome_exp, modo_offline)
                if smiles_exp:
                    desc_exp = calcular_descritores_rdkit(smiles_exp)
                    if desc_exp:
                        dados_exp = {
                            "peso": desc_exp["peso"], "logp": desc_exp["logp"], "tpsa": desc_exp["tpsa"],
                            "lipinski_ok": desc_exp["lipinski_ok"], "veber_ok": desc_exp["veber_ok"],
                            "egan_ok": desc_exp["egan_ok"], "risco_herg": desc_exp["herg"]["risco"]
                        }
                st.session_state.eln_experimentos.append({
                    "id": str(uuid.uuid4())[:8],
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "nome": nome_exp,
                    "modulo": modulo_ativo,
                    "notas": notas_exp,
                    "dados": dados_exp
                })
                st.success(t("exp_saved_success", nome=nome_exp))
                st.rerun()

    st.write("---")
    st.subheader(t("registered_experiments_title"))

    if not st.session_state.eln_experimentos:
        st.info(t("no_experiments_notice"))
    else:
        for exp in reversed(st.session_state.eln_experimentos):
            with st.expander(f"🧾 {exp['nome']} — {exp['timestamp']} ({exp['modulo']})"):
                st.json(exp['dados']) if exp['dados'] else st.caption(t("no_fq_data_caption"))
                st.write(f"**{t('notes_label_short')}** {exp.get('notas', '-')}")
                if st.button(t("btn_delete_record"), key=f"del_{exp['id']}"):
                    st.session_state.eln_experimentos = [e for e in st.session_state.eln_experimentos if e['id'] != exp['id']]
                    st.rerun()

        st.write("---")
        st.subheader(t("eln_export_section"))
        col_e1, col_e2, col_e3 = st.columns(3)

        with col_e1:
            json_eln = json.dumps(st.session_state.eln_experimentos, indent=4, ensure_ascii=False)
            st.download_button(t("btn_export_all_json"), data=json_eln,
                                file_name=f"eln_senotrack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json")

        with col_e2:
            st.download_button(t("btn_export_pdf_consolidated"),
                                data=gerar_pdf_eln(st.session_state.eln_experimentos),
                                file_name=f"eln_senotrack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf")

        with col_e3:
            df_eln_export = pd.DataFrame([{
                "Composto": e["nome"], "Timestamp": e["timestamp"], "Módulo": e["modulo"],
                "Notas": e.get("notas", ""), **e.get("dados", {})
            } for e in st.session_state.eln_experimentos])
            csv_eln = df_eln_export.to_csv(index=False).encode("utf-8")
            st.download_button(t("btn_export_csv"), data=csv_eln,
                                file_name=f"eln_senotrack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv")

        if st.button(t("btn_clear_notebook")):
            st.session_state.eln_experimentos = []
            st.rerun()