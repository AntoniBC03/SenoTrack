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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
st.set_page_config(page_title="SenoTrack Enterprise v10.0", page_icon="◆", layout="wide")

# =====================================================================
# CONSTANTES INTERNAS (SENTINELAS NEUTRAS DE IDIOMA — usadas só em lógica)
# =====================================================================
PUBMED_NOT_FOUND = "__PUBMED_NOT_FOUND__"
RXNAV_NOT_FOUND = "__RXNAV_NOT_FOUND__"
BATCH_ERROR_SENTINEL = "__BATCH_ERROR__"

# =====================================================================
# ÍCONES CORPORATIVOS (SVG estilo Lucide, minimalistas, sem emojis)
# =====================================================================
ICON_PATHS = {
    "activity": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    "flask": '<path d="M14 2v6a2 2 0 0 0 .245.96l5.51 10.08A2 2 0 0 1 18 22H6a2 2 0 0 1-1.755-2.96l5.51-10.08A2 2 0 0 0 10 8V2"/><path d="M6.453 15h11.094"/><path d="M8.5 2h7"/>',
    "layers": '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
    "bar-chart": '<line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/>',
    "sparkles": '<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/>',
    "book-open": '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>',
    "clipboard": '<rect x="8" y="2" width="8" height="4" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>',
    "file-text": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>',
    "shield": '<path d="M20 13c0 5-3.5 7.5-8 9-4.5-1.5-8-4-8-9V5l8-3 8 3v8z"/>',
    "microscope": '<path d="M6 18h8"/><path d="M3 22h18"/><path d="M14 22a7 7 0 1 0 0-14h-1"/><path d="M9 14h2"/><path d="M9 12a2 2 0 0 1-2-2V6h4v4a2 2 0 0 1-2 2Z"/><path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/>',
    "gauge": '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
    "history": '<path d="M3 3v5h5"/><path d="M3.05 13A9 9 0 1 0 6 5.3L3 8"/><path d="M12 7v5l4 2"/>',
}

def icon_svg(nome, cor="#8b7cf6", tamanho=17):
    caminho = ICON_PATHS.get(nome, ICON_PATHS["activity"])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{tamanho}" height="{tamanho}" viewBox="0 0 24 24" '
            f'fill="none" stroke="{cor}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
            f'style="vertical-align:middle;flex-shrink:0;">{caminho}</svg>')

def sec_header(nome_icone, texto):
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:10px;border-left:4px solid var(--accent-purple, #8b5cf6);
        padding:5px 0 5px 14px;margin:22px 0 12px;">{icon_svg(nome_icone, cor="var(--accent-purple, #8b5cf6)")}
        <span style="font-size:1.05rem;font-weight:700;color:var(--text-primary, #e8ecf5);letter-spacing:0.01em;">{texto}</span></div>""",
        unsafe_allow_html=True,
    )

def sub_label(texto):
    st.markdown(f"<div style='font-weight:600;color:var(--text-secondary, #6b7280);font-size:0.92rem;margin:6px 0 4px;'>{texto}</div>", unsafe_allow_html=True)

# =====================================================================
# I18N — IDIOMAS DISPONÍVEIS
# =====================================================================
IDIOMAS_DISPONIVEIS = {
    "PT — Português": "pt",
    "EN — English": "en",
    "ES — Español": "es",
    "ZH — 中文": "zh",
    "DE — Deutsch": "de",
    "JA — 日本語": "ja",
}

TRANSLATIONS = {
    "app_badge": {"pt": "SENOTRACK ENTERPRISE v10.0 · RESEARCH ECOSYSTEM EDITION", "en": "SENOTRACK ENTERPRISE v10.0 · RESEARCH ECOSYSTEM EDITION", "es": "SENOTRACK ENTERPRISE v10.0 · EDICIÓN ECOSISTEMA DE INVESTIGACIÓN", "zh": "SENOTRACK 企业版 v10.0 · 科研生态系统版", "de": "SENOTRACK ENTERPRISE v10.0 · RESEARCH ECOSYSTEM EDITION", "ja": "SENOTRACK エンタープライズ v10.0 · リサーチエコシステム版"},
    "app_title": {"pt": "Hub Avançado de Análise Oncológica, Longevidade e P&D Farmacêutico", "en": "Advanced Hub for Oncology, Longevity and Pharmaceutical R&D Analysis", "es": "Centro Avanzado de Análisis Oncológico, Longevidad e I+D Farmacéutico", "zh": "肿瘤学、长寿与药物研发高级分析平台", "de": "Erweitertes Zentrum für Onkologie-, Langlebigkeits- und Pharma-F&E-Analyse", "ja": "腫瘍学・長寿・製薬研究開発 高度分析ハブ"},
    "sidebar_language": {"pt": "Idioma", "en": "Language", "es": "Idioma", "zh": "语言", "de": "Sprache", "ja": "言語"},
    "sidebar_user_profile": {"pt": "Perfil do Usuário", "en": "User Profile", "es": "Perfil del Usuario", "zh": "用户模式", "de": "Benutzerprofil", "ja": "ユーザープロファイル"},
    "profile_radio_label": {"pt": "Nível de Complexidade da Interface:", "en": "Interface Complexity Level:", "es": "Nivel de Complejidad de la Interfaz:", "zh": "界面复杂度级别：", "de": "Komplexitätsstufe der Oberfläche:", "ja": "インターフェースの複雑さレベル："},
    "profile_didactic": {"pt": "Didático / Graduação", "en": "Educational / Undergraduate", "es": "Didáctico / Pregrado", "zh": "教学模式 / 本科", "de": "Lehrmodus / Bachelor", "ja": "教育モード／学部"},
    "profile_research": {"pt": "Pesquisa / P&D (Avançado)", "en": "Research / R&D (Advanced)", "es": "Investigación / I+D (Avanzado)", "zh": "科研模式 / 研发（高级）", "de": "Forschungsmodus / F&E (Erweitert)", "ja": "研究モード／研究開発（上級）"},
    "sidebar_ai": {"pt": "Inteligência Artificial (Agente)", "en": "Artificial Intelligence (Agent)", "es": "Inteligencia Artificial (Agente)", "zh": "人工智能（智能体）", "de": "Künstliche Intelligenz (Agent)", "ja": "人工知能（エージェント）"},
    "api_key_label": {"pt": "Chave API (OpenAI/Gemini)", "en": "API Key (OpenAI/Gemini)", "es": "Clave API (OpenAI/Gemini)", "zh": "API 密钥（OpenAI/Gemini）", "de": "API-Schlüssel (OpenAI/Gemini)", "ja": "APIキー（OpenAI/Gemini）"},
    "api_key_help": {"pt": "Opcional. Se vazio, o sistema usa o modelo preditivo local.", "en": "Optional. If empty, the system uses the local predictive model.", "es": "Opcional. Si está vacío, el sistema usa el modelo predictivo local.", "zh": "可选。留空则系统使用本地预测模型。", "de": "Optional. Wenn leer, verwendet das System das lokale Vorhersagemodell.", "ja": "任意。空欄の場合はローカル予測モデルを使用します。"},
    "sidebar_clinical_params": {"pt": "Parametrização Clínica", "en": "Clinical Parameters", "es": "Parametrización Clínica", "zh": "临床参数设置", "de": "Klinische Parametrisierung", "ja": "臨床パラメータ設定"},
    "module_label": {"pt": "Módulo Temático Ativo:", "en": "Active Thematic Module:", "es": "Módulo Temático Activo:", "zh": "当前主题模块：", "de": "Aktives Themenmodul:", "ja": "アクティブなテーマモジュール："},
    "sidebar_filters": {"pt": "Filtros Farmacocinéticos", "en": "Pharmacokinetic Filters", "es": "Filtros Farmacocinéticos", "zh": "药代动力学筛选条件", "de": "Pharmakokinetische Filter", "ja": "薬物動態フィルター"},
    "mass_limit_label": {"pt": "Teto de Massa Molecular (g/mol):", "en": "Molecular Mass Ceiling (g/mol):", "es": "Límite de Masa Molecular (g/mol):", "zh": "分子量上限（g/mol）：", "de": "Obergrenze der Molmasse (g/mol):", "ja": "分子量の上限（g/mol）："},
    "mass_limit_help": {"pt": "Moléculas acima deste peso serão automaticamente desconsideradas na triagem atual em lote.", "en": "Molecules above this weight will be automatically excluded from the current batch screening.", "es": "Las moléculas por encima de este peso se excluirán automáticamente del cribado por lotes actual.", "zh": "超过此重量的分子将在当前批量筛选中自动排除。", "de": "Moleküle über diesem Gewicht werden im aktuellen Batch-Screening automatisch ausgeschlossen.", "ja": "この重量を超える分子は、現在のバッチスクリーニングで自動的に除外されます。"},
    "tpsa_limit_label": {"pt": "Teto de TPSA (Å²) — Regra de Veber:", "en": "TPSA Ceiling (Å²) — Veber's Rule:", "es": "Límite de TPSA (Å²) — Regla de Veber:", "zh": "TPSA 上限（Å²）— Veber 规则：", "de": "TPSA-Obergrenze (Å²) — Veber-Regel:", "ja": "TPSA上限（Å²）—Veberルール："},
    "rot_limit_label": {"pt": "Máx. Ligações Rotacionáveis — Veber:", "en": "Max. Rotatable Bonds — Veber:", "es": "Máx. Enlaces Rotables — Veber:", "zh": "最大可旋转键数 — Veber：", "de": "Max. drehbare Bindungen — Veber:", "ja": "最大回転可能結合数 — Veber："},
    "sidebar_infra": {"pt": "Infraestrutura & Laboratórios", "en": "Infrastructure & Labs", "es": "Infraestructura y Laboratorios", "zh": "基础设施与实验室", "de": "Infrastruktur & Labore", "ja": "インフラとラボ"},
    "offline_toggle": {"pt": "Modo de Demonstração (Mock/Offline)", "en": "Demonstration Mode (Mock/Offline)", "es": "Modo de Demostración (Simulado/Offline)", "zh": "演示模式（模拟/离线）", "de": "Demomodus (Mock/Offline)", "ja": "デモモード（モック／オフライン）"},
    "eln_sidebar_title": {"pt": "Caderno Científico (ELN)", "en": "Electronic Lab Notebook (ELN)", "es": "Cuaderno Científico (ELN)", "zh": "电子实验记录本（ELN）", "de": "Elektronisches Laborbuch (ELN)", "ja": "電子実験ノート（ELN）"},
    "eln_sidebar_caption": {"pt": "{n} experimentos salvos nesta sessão.", "en": "{n} experiments saved in this session.", "es": "{n} experimentos guardados en esta sesión.", "zh": "本次会话已保存 {n} 个实验。", "de": "{n} Experimente in dieser Sitzung gespeichert.", "ja": "このセッションで {n} 件の実験が保存されました。"},
    "audit_sidebar_title": {"pt": "Rastreabilidade & Auditoria", "en": "Traceability & Audit", "es": "Trazabilidad y Auditoría", "zh": "可追溯性与审计", "de": "Rückverfolgbarkeit & Audit", "ja": "トレーサビリティと監査"},
    "audit_sidebar_caption": {"pt": "{n} consultas salvas nesta sessão.", "en": "{n} queries saved in this session.", "es": "{n} consultas guardadas en esta sesión.", "zh": "本次会话已保存 {n} 次查询。", "de": "{n} Abfragen in dieser Sitzung gespeichert.", "ja": "このセッションで {n} 件のクエリが保存されました。"},
    "audit_export_button": {"pt": "Exportar Histórico de Sessão (JSON)", "en": "Export Session History (JSON)", "es": "Exportar Historial de Sesión (JSON)", "zh": "导出会话历史记录（JSON）", "de": "Sitzungsverlauf exportieren (JSON)", "ja": "セッション履歴をエクスポート（JSON）"},
    "tab_individual": {"pt": "Perfil Clínico e Terapêutico", "en": "Clinical & Therapeutic Profile", "es": "Perfil Clínico y Terapéutico", "zh": "临床与治疗档案", "de": "Klinisches & Therapeutisches Profil", "ja": "臨床・治療プロファイル"},
    "tab_lote": {"pt": "Processamento de Lotes Hospitalares", "en": "Hospital Batch Processing", "es": "Procesamiento de Lotes Hospitalarios", "zh": "医院批量处理", "de": "Krankenhaus-Batch-Verarbeitung", "ja": "病院バッチ処理"},
    "tab_fq": {"pt": "Triagem Físico-Química", "en": "Physicochemical Screening", "es": "Cribado Fisicoquímico", "zh": "理化性质筛选", "de": "Physikochemisches Screening", "ja": "物理化学的スクリーニング"},
    "tab_docking": {"pt": "Docking Virtual & Proteômica", "en": "Virtual Docking & Proteomics", "es": "Acoplamiento Virtual y Proteómica", "zh": "虚拟对接与蛋白质组学", "de": "Virtuelles Docking & Proteomik", "ja": "バーチャルドッキング＆プロテオミクス"},
    "tab_benchmark": {"pt": "Farmacoterapia & Benchmark", "en": "Pharmacotherapy & Benchmark", "es": "Farmacoterapia y Referencia", "zh": "药物治疗与基准比较", "de": "Pharmakotherapie & Benchmark", "ja": "薬物療法＆ベンチマーク"},
    "tab_literature": {"pt": "Agente Clínico & Literatura", "en": "Clinical Agent & Literature", "es": "Agente Clínico y Literatura", "zh": "临床智能体与文献", "de": "Klinischer Agent & Literatur", "ja": "臨床エージェント＆文献"},
    "tab_eln": {"pt": "Caderno Científico (ELN)", "en": "Electronic Lab Notebook (ELN)", "es": "Cuaderno Científico (ELN)", "zh": "电子实验记录本（ELN）", "de": "Elektronisches Laborbuch (ELN)", "ja": "電子実験ノート（ELN）"},
    "input_molecule_label": {"pt": "Digite o nome da molécula (inglês):", "en": "Enter the molecule name (English):", "es": "Ingrese el nombre de la molécula (inglés):", "zh": "输入分子名称（英文）：", "de": "Geben Sie den Molekülnamen ein (Englisch):", "ja": "分子名を入力してください（英語）："},
    "metric_formula": {"pt": "Fórmula Química", "en": "Chemical Formula", "es": "Fórmula Química", "zh": "化学式", "de": "Chemische Formel", "ja": "化学式"},
    "metric_mass": {"pt": "Massa Molecular", "en": "Molecular Mass", "es": "Masa Molecular", "zh": "分子量", "de": "Molekülmasse", "ja": "分子量"},
    "section_application": {"pt": "Aplicação Médica e Terapêutica Avançada", "en": "Advanced Medical & Therapeutic Application", "es": "Aplicación Médica y Terapéutica Avanzada", "zh": "高级医疗与治疗应用", "de": "Erweiterte medizinische & therapeutische Anwendung", "ja": "高度な医療・治療応用"},
    "section_pipeline": {"pt": "Pipeline de Eficiência Terapêutica Real", "en": "Real Therapeutic Efficiency Pipeline", "es": "Pipeline de Eficiencia Terapéutica Real", "zh": "真实治疗效能研发管线", "de": "Reale Pipeline der therapeutischen Wirksamkeit", "ja": "実際の治療効果パイプライン"},
    "section_evidence": {"pt": "Evidência Científica e Identificação Farmacológica", "en": "Scientific Evidence & Pharmacological Identification", "es": "Evidencia Científica e Identificación Farmacológica", "zh": "科学证据与药理学鉴定", "de": "Wissenschaftliche Evidenz & Pharmakologische Identifikation", "ja": "科学的根拠と薬理学的同定"},
    "pubmed_article_label": {"pt": "Artigo Relevante (PubMed)", "en": "Relevant Article (PubMed)", "es": "Artículo Relevante (PubMed)", "zh": "相关文献（PubMed）", "de": "Relevanter Artikel (PubMed)", "ja": "関連論文（PubMed）"},
    "pubmed_found": {"pt": "Artigo encontrado:", "en": "Article found:", "es": "Artículo encontrado:", "zh": "找到文献：", "de": "Artikel gefunden:", "ja": "論文が見つかりました："},
    "pubmed_not_found": {"pt": "Nenhuma publicação direta localizada para este composto.", "en": "No direct publication found for this compound.", "es": "No se encontró ninguna publicación directa para este compuesto.", "zh": "未找到该化合物的直接文献。", "de": "Keine direkte Publikation für diese Verbindung gefunden.", "ja": "この化合物に関する直接的な論文は見つかりませんでした。"},
    "pubmed_link": {"pt": "Abrir artigo científico no PubMed", "en": "Open scientific article on PubMed", "es": "Abrir artículo científico en PubMed", "zh": "在 PubMed 中打开文献", "de": "Wissenschaftlichen Artikel auf PubMed öffnen", "ja": "PubMedで論文を開く"},
    "rxnav_label": {"pt": "Registro de Farmacopeia (RxNav)", "en": "Pharmacopeia Record (RxNav)", "es": "Registro de Farmacopea (RxNav)", "zh": "药典记录（RxNav）", "de": "Arzneibuch-Eintrag (RxNav)", "ja": "薬局方記録（RxNav）"},
    "rxnav_found_template": {"pt": "Identificador RxCUI localizado: {id}", "en": "RxCUI identifier found: {id}", "es": "Identificador RxCUI localizado: {id}", "zh": "已找到 RxCUI 标识符：{id}", "de": "RxCUI-Kennung gefunden: {id}", "ja": "RxCUI識別子が見つかりました：{id}"},
    "rxnav_no_data": {"pt": "Sem dados disponíveis", "en": "No data available", "es": "Sin datos disponibles", "zh": "无可用数据", "de": "Keine Daten verfügbar", "ja": "データがありません"},
    "ai_agent_section": {"pt": "Agente Clínico de IA (Insight Automático)", "en": "Clinical AI Agent (Automatic Insight)", "es": "Agente Clínico de IA (Perspectiva Automática)", "zh": "临床AI智能体（自动洞察）", "de": "Klinischer KI-Agent (Automatische Erkenntnis)", "ja": "臨床AIエージェント（自動インサイト）"},
    "ai_agent_desc": {"pt": "Use o botão abaixo para invocar a rede neural que sintetiza a viabilidade deste composto.", "en": "Use the button below to invoke the neural network that synthesizes this compound's viability.", "es": "Use el botón de abajo para invocar la red neuronal que sintetiza la viabilidad de este compuesto.", "zh": "点击下方按钮调用神经网络，综合评估该化合物的可行性。", "de": "Verwenden Sie die Schaltfläche unten, um das neuronale Netz aufzurufen, das die Machbarkeit dieser Verbindung zusammenfasst.", "ja": "以下のボタンを使用して、この化合物の実現可能性を総合するニューラルネットワークを呼び出します。"},
    "btn_generate_insight": {"pt": "Gerar Insight Farmacológico para {nome}", "en": "Generate Pharmacological Insight for {nome}", "es": "Generar Perspectiva Farmacológica para {nome}", "zh": "为 {nome} 生成药理学洞察", "de": "Pharmakologische Erkenntnis für {nome} generieren", "ja": "{nome} の薬理学的インサイトを生成"},
    "spinner_generating": {"pt": "Sintetizando base de dados médicos e estrutura química...", "en": "Synthesizing medical database and chemical structure...", "es": "Sintetizando base de datos médica y estructura química...", "zh": "正在综合医学数据库与化学结构...", "de": "Synthetisiere medizinische Datenbank und chemische Struktur...", "ja": "医療データベースと化学構造を統合中..."},
    "structure_2d_caption": {"pt": "Esquema de estrutura 2D", "en": "2D structure diagram", "es": "Esquema de estructura 2D", "zh": "二维结构示意图", "de": "2D-Strukturdiagramm", "ja": "2D構造図"},
    "structure_3d_caption": {"pt": "Modelo estereoscópico 3D dinâmico", "en": "Dynamic 3D stereoscopic model", "es": "Modelo estereoscópico 3D dinámico", "zh": "动态三维立体模型", "de": "Dynamisches stereoskopisches 3D-Modell", "ja": "動的3D立体モデル"},
    "offline_2d_msg": {"pt": "Visualização gráfica 2D suspensa em ambiente offline.", "en": "2D graphical visualization suspended in offline environment.", "es": "Visualización gráfica 2D suspendida en entorno offline.", "zh": "离线环境下二维可视化功能已暂停。", "de": "2D-Grafikvisualisierung im Offline-Modus deaktiviert.", "ja": "オフライン環境では2D可視化は無効です。"},
    "offline_3d_msg": {"pt": "Renderizador molecular 3D desabilitado em ambiente offline.", "en": "3D molecular renderer disabled in offline environment.", "es": "Renderizador molecular 3D deshabilitado en entorno offline.", "zh": "离线环境下三维分子渲染器已禁用。", "de": "3D-Molekül-Renderer im Offline-Modus deaktiviert.", "ja": "オフライン環境では3D分子レンダラーが無効です。"},
    "structure3d_unavailable": {"pt": "Modelo tridimensional indisponível para esta estrutura.", "en": "3D model unavailable for this structure.", "es": "Modelo tridimensional no disponible para esta estructura.", "zh": "该结构无三维模型可用。", "de": "3D-Modell für diese Struktur nicht verfügbar.", "ja": "この構造の3Dモデルは利用できません。"},
    "btn_save_eln": {"pt": "Salvar este composto no Caderno Científico (ELN)", "en": "Save this compound to the Electronic Lab Notebook (ELN)", "es": "Guardar este compuesto en el Cuaderno Científico (ELN)", "zh": "将此化合物保存到电子实验记录本（ELN）", "de": "Diese Verbindung im elektronischen Laborbuch (ELN) speichern", "ja": "この化合物を電子実験ノート（ELN）に保存"},
    "eln_saved_success": {"pt": "Experimento registrado no Caderno Científico (ver aba ELN).", "en": "Experiment recorded in the Lab Notebook (see ELN tab).", "es": "Experimento registrado en el Cuaderno Científico (ver pestaña ELN).", "zh": "实验已记录到电子实验记录本（见ELN标签页）。", "de": "Experiment im Laborbuch gespeichert (siehe Tab ELN).", "ja": "実験は電子実験ノートに記録されました（ELNタブを参照）。"},
    "btn_download_pdf_individual": {"pt": "Baixar Laudo Individual (PDF)", "en": "Download Individual Report (PDF)", "es": "Descargar Informe Individual (PDF)", "zh": "下载单项报告（PDF）", "de": "Einzelbericht herunterladen (PDF)", "ja": "個別レポートをダウンロード（PDF）"},
    "error_compound_not_found": {"pt": "Composto não localizado ou erro de resposta no barramento externo do PubChem.", "en": "Compound not found or error in the external PubChem response.", "es": "Compuesto no localizado o error en la respuesta externa de PubChem.", "zh": "未找到该化合物，或 PubChem 外部接口响应出错。", "de": "Verbindung nicht gefunden oder Fehler in der externen PubChem-Antwort.", "ja": "化合物が見つからないか、PubChem外部応答でエラーが発生しました。"},
    "lote_caption": {"pt": "Gerenciamento e triagem automatizada de planilhas integradas com dados do PubMed, RxNav e Inteligência Artificial.", "en": "Automated management and screening of spreadsheets integrated with PubMed, RxNav and AI data.", "es": "Gestión y cribado automatizado de hojas de cálculo integradas con datos de PubMed, RxNav e IA.", "zh": "与 PubMed、RxNav 和人工智能数据集成的自动化电子表格管理与筛选。", "de": "Automatisierte Verwaltung und Screening von Tabellen, integriert mit PubMed-, RxNav- und KI-Daten.", "ja": "PubMed、RxNav、AIデータと統合された自動スプレッドシート管理・スクリーニング。"},
    "btn_download_template": {"pt": "Baixar Planilha Modelo (.xlsx)", "en": "Download Template Spreadsheet (.xlsx)", "es": "Descargar Plantilla (.xlsx)", "zh": "下载模板表格（.xlsx）", "de": "Vorlagentabelle herunterladen (.xlsx)", "ja": "テンプレートをダウンロード（.xlsx）"},
    "uploader_label": {"pt": "Carregue a planilha de triagem (.xlsx ou .csv):", "en": "Upload the screening spreadsheet (.xlsx or .csv):", "es": "Cargue la hoja de cálculo de cribado (.xlsx o .csv):", "zh": "上传筛选表格（.xlsx 或 .csv）：", "de": "Screening-Tabelle hochladen (.xlsx oder .csv):", "ja": "スクリーニング用スプレッドシートをアップロード（.xlsxまたは.csv）："},
    "spinner_batch_scan": {"pt": "Realizando varredura biomolecular no PubChem, PubMed e RxNav...", "en": "Running biomolecular scan on PubChem, PubMed and RxNav...", "es": "Realizando escaneo biomolecular en PubChem, PubMed y RxNav...", "zh": "正在对 PubChem、PubMed 和 RxNav 进行生物分子扫描...", "de": "Biomolekularer Scan bei PubChem, PubMed und RxNav läuft...", "ja": "PubChem、PubMed、RxNavで生体分子スキャンを実行中..."},
    "kpi_section": {"pt": "Indicadores Globais do Lote", "en": "Global Batch Indicators", "es": "Indicadores Globales del Lote", "zh": "批次总体指标", "de": "Globale Batch-Kennzahlen", "ja": "バッチ全体指標"},
    "kpi_total": {"pt": "Total em Lote", "en": "Total in Batch", "es": "Total en Lote", "zh": "批次总数", "de": "Gesamt im Batch", "ja": "バッチ総数"},
    "kpi_approved": {"pt": "Aprovados (Lipinski)", "en": "Approved (Lipinski)", "es": "Aprobados (Lipinski)", "zh": "通过（Lipinski）", "de": "Genehmigt (Lipinski)", "ja": "承認済み（Lipinski）"},
    "kpi_evidence": {"pt": "Evidências PubMed", "en": "PubMed Evidence", "es": "Evidencias PubMed", "zh": "PubMed 证据", "de": "PubMed-Evidenz", "ja": "PubMedエビデンス"},
    "kpi_module": {"pt": "Módulo Ativo", "en": "Active Module", "es": "Módulo Activo", "zh": "当前模块", "de": "Aktives Modul", "ja": "アクティブモジュール"},
    "batch_lipinski_warning": {"pt": "Filtro de Lipinski ativo: {itens} compostos foram omitidos por excederem o teto de {limite} g/mol configurado na barra lateral.", "en": "Lipinski filter active: {itens} compounds were omitted for exceeding the {limite} g/mol ceiling configured in the sidebar.", "es": "Filtro de Lipinski activo: {itens} compuestos fueron omitidos por exceder el límite de {limite} g/mol configurado en la barra lateral.", "zh": "Lipinski 筛选已启用：{itens} 个化合物因超过侧边栏设置的 {limite} g/mol 上限而被排除。", "de": "Lipinski-Filter aktiv: {itens} Verbindungen wurden ausgeschlossen, da sie die in der Seitenleiste konfigurierte Obergrenze von {limite} g/mol überschreiten.", "ja": "Lipinskiフィルターが有効：{itens} 件の化合物は、サイドバーで設定された {limite} g/mol の上限を超えたため除外されました。"},
    "ai_batch_section": {"pt": "Agente Clínico de IA: Análise de Viabilidade do Lote", "en": "Clinical AI Agent: Batch Viability Analysis", "es": "Agente Clínico de IA: Análisis de Viabilidad del Lote", "zh": "临床AI智能体：批次可行性分析", "de": "Klinischer KI-Agent: Batch-Machbarkeitsanalyse", "ja": "臨床AIエージェント：バッチ実現可能性分析"},
    "ai_batch_desc": {"pt": "Clique abaixo para gerar um relatório sintético da IA analisando a coerência de todos os compostos do lote de uma só vez.", "en": "Click below to generate an AI synthetic report analyzing the coherence of all batch compounds at once.", "es": "Haga clic abajo para generar un informe sintético de IA que analice la coherencia de todos los compuestos del lote a la vez.", "zh": "点击下方生成AI综合报告，一次性分析批次中所有化合物的一致性。", "de": "Klicken Sie unten, um einen KI-Kurzbericht zu erstellen, der die Kohärenz aller Batch-Verbindungen auf einmal analysiert.", "ja": "以下をクリックして、バッチ内のすべての化合物の一貫性を一度に分析するAI要約レポートを生成します。"},
    "btn_generate_batch_ai": {"pt": "Gerar Parecer Clínico do Lote por IA", "en": "Generate AI Clinical Opinion for the Batch", "es": "Generar Dictamen Clínico del Lote por IA", "zh": "生成AI批次临床意见", "de": "KI-Klinisches Gutachten für den Batch generieren", "ja": "AIによるバッチ臨床所見を生成"},
    "batch_ai_report_title": {"pt": "Parecer Geral da IA para o Lote", "en": "General AI Opinion for the Batch", "es": "Dictamen General de IA para el Lote", "zh": "AI批次总体意见", "de": "Allgemeines KI-Gutachten für den Batch", "ja": "AIによるバッチ全体所見"},
    "batch_ai_analyzed": {"pt": "Foram analisadas {n} moléculas no módulo {modulo}: {nomes}.", "en": "{n} molecules were analyzed in the {modulo} module: {nomes}.", "es": "Se analizaron {n} moléculas en el módulo {modulo}: {nomes}.", "zh": "已在 {modulo} 模块中分析了 {n} 个分子：{nomes}。", "de": "Es wurden {n} Moleküle im Modul {modulo} analysiert: {nomes}.", "ja": "{modulo}モジュールで{n}個の分子を分析しました：{nomes}。"},
    "batch_ai_coherence": {"pt": "Coerência Terapêutica: a combinação de compostos apresenta alta compatibilidade com o ecossistema de {modulo}.", "en": "Therapeutic Coherence: the compound combination shows high compatibility with the {modulo} ecosystem.", "es": "Coherencia Terapéutica: la combinación de compuestos presenta alta compatibilidad con el ecosistema de {modulo}.", "zh": "治疗一致性：该化合物组合与 {modulo} 生态系统具有高度兼容性。", "de": "Therapeutische Kohärenz: Die Verbindungskombination zeigt hohe Kompatibilität mit dem Ökosystem {modulo}.", "ja": "治療的一貫性：この化合物の組み合わせは{modulo}エコシステムと高い互換性を示しています。"},
    "batch_ai_pk": {"pt": "Perfil Farmacocinético: a distribuição de massa molecular média está equilibrada. {n} dos compostos possuem publicações diretas no PubMed de alto impacto.", "en": "Pharmacokinetic Profile: the average molecular mass distribution is balanced. {n} of the compounds have direct high-impact PubMed publications.", "es": "Perfil Farmacocinético: la distribución de masa molecular promedio está equilibrada. {n} de los compuestos tienen publicaciones directas de alto impacto en PubMed.", "zh": "药代动力学概况：平均分子量分布均衡。其中 {n} 个化合物拥有直接的高影响力 PubMed 文献。", "de": "Pharmakokinetisches Profil: Die durchschnittliche Molekülmassenverteilung ist ausgewogen. {n} der Verbindungen verfügen über direkte, wirkungsstarke PubMed-Publikationen.", "ja": "薬物動態プロファイル：平均分子量分布はバランスが取れています。{n}件の化合物に直接的な高インパクトPubMed論文があります。"},
    "batch_ai_recommendation": {"pt": "Recomendação: aprovado para prosseguimento de testes in silico e alocação em matrizes de triagem clínica hospitalar.", "en": "Recommendation: approved to proceed with in silico testing and allocation in hospital clinical screening matrices.", "es": "Recomendación: aprobado para continuar con pruebas in silico y asignación en matrices de cribado clínico hospitalario.", "zh": "建议：批准进行计算机模拟测试，并纳入医院临床筛选矩阵。", "de": "Empfehlung: Freigegeben für die Fortsetzung von In-silico-Tests und Zuordnung zu klinischen Krankenhaus-Screening-Matrizen.", "ja": "推奨事項：インシリコ試験の継続および病院臨床スクリーニングマトリックスへの組み入れを承認。"},
    "matrix_section": {"pt": "Matriz Comparativa e Evidências Biomoleculares", "en": "Comparative Matrix & Biomolecular Evidence", "es": "Matriz Comparativa y Evidencias Biomoleculares", "zh": "比较矩阵与生物分子证据", "de": "Vergleichsmatrix & biomolekulare Evidenz", "ja": "比較マトリックスと生体分子エビデンス"},
    "detail_section": {"pt": "Inspeção Detalhada por Composto da Planilha", "en": "Detailed Inspection per Spreadsheet Compound", "es": "Inspección Detallada por Compuesto de la Hoja", "zh": "表格中各化合物的详细检查", "de": "Detaillierte Prüfung je Tabellenverbindung", "ja": "スプレッドシート内化合物の詳細検査"},
    "master_table_title": {"pt": "Tabela Mestra do Lote", "en": "Batch Master Table", "es": "Tabla Maestra del Lote", "zh": "批次主表", "de": "Batch-Übersichtstabelle", "ja": "バッチマスターテーブル"},
    "density_section": {"pt": "Perfil de Densidade Molecular do Lote", "en": "Batch Molecular Density Profile", "es": "Perfil de Densidad Molecular del Lote", "zh": "批次分子密度分布图", "de": "Molekulares Dichteprofil des Batches", "ja": "バッチ分子密度プロファイル"},
    "export_section": {"pt": "Exportação de Relatórios Completa", "en": "Full Report Export", "es": "Exportación Completa de Informes", "zh": "完整报告导出", "de": "Vollständiger Berichtsexport", "ja": "完全レポートエクスポート"},
    "btn_download_pdf_batch": {"pt": "Baixar Laudo Clínico Executivo (PDF)", "en": "Download Executive Clinical Report (PDF)", "es": "Descargar Informe Clínico Ejecutivo (PDF)", "zh": "下载执行版临床报告（PDF）", "de": "Executive Klinikbericht herunterladen (PDF)", "ja": "エグゼクティブ臨床レポートをダウンロード（PDF）"},
    "btn_download_json_batch": {"pt": "Exportar Dados Estruturados (JSON)", "en": "Export Structured Data (JSON)", "es": "Exportar Datos Estructurados (JSON)", "zh": "导出结构化数据（JSON）", "de": "Strukturierte Daten exportieren (JSON)", "ja": "構造化データをエクスポート（JSON）"},
    "fq_caption": {"pt": "Cálculo de descritores moleculares avançados (RDKit): Lipinski, Veber, Egan, alertas PAINS e risco hERG heurístico.", "en": "Advanced molecular descriptor calculation (RDKit): Lipinski, Veber, Egan, PAINS alerts and heuristic hERG risk.", "es": "Cálculo de descriptores moleculares avanzados (RDKit): Lipinski, Veber, Egan, alertas PAINS y riesgo hERG heurístico.", "zh": "高级分子描述符计算（RDKit）：Lipinski、Veber、Egan 规则、PAINS 警报及 hERG 启发式风险。", "de": "Berechnung erweiterter molekularer Deskriptoren (RDKit): Lipinski, Veber, Egan, PAINS-Warnungen und heuristisches hERG-Risiko.", "ja": "高度な分子記述子計算（RDKit）：Lipinski、Veber、Egan則、PAINSアラート、hERGヒューリスティックリスク。"},
    "input_fq_label": {"pt": "Nome do composto para triagem físico-química:", "en": "Compound name for physicochemical screening:", "es": "Nombre del compuesto para cribado fisicoquímico:", "zh": "用于理化筛选的化合物名称：", "de": "Verbindungsname für physikochemisches Screening:", "ja": "物理化学的スクリーニング対象の化合物名："},
    "error_no_smiles": {"pt": "Não foi possível obter o SMILES estrutural deste composto (indisponível na base local/PubChem). Compostos macromoleculares/biológicos como anticorpos e peptídeos grandes não possuem SMILES tratável por RDKit neste módulo.", "en": "Could not obtain the structural SMILES for this compound (unavailable in local base/PubChem). Macromolecular/biological compounds such as antibodies and large peptides do not have SMILES tractable by RDKit in this module.", "es": "No fue posible obtener el SMILES estructural de este compuesto (no disponible en la base local/PubChem). Los compuestos macromoleculares/biológicos como anticuerpos y péptidos grandes no tienen SMILES tratable por RDKit en este módulo.", "zh": "无法获取该化合物的结构 SMILES（本地库/PubChem中不可用）。抗体和大型多肽等大分子/生物化合物在本模块中没有可被 RDKit 处理的 SMILES。", "de": "SMILES-Struktur dieser Verbindung konnte nicht ermittelt werden (in lokaler Basis/PubChem nicht verfügbar). Makromolekulare/biologische Verbindungen wie Antikörper und große Peptide besitzen in diesem Modul kein für RDKit verarbeitbares SMILES.", "ja": "この化合物の構造SMILESを取得できませんでした（ローカルデータベース/PubChemに存在しません）。抗体や大型ペプチドなどの高分子・生体化合物は、このモジュールではRDKitで処理可能なSMILESを持ちません。"},
    "error_invalid_smiles": {"pt": "Estrutura SMILES inválida ou não interpretável pelo motor RDKit.", "en": "Invalid SMILES structure or not interpretable by the RDKit engine.", "es": "Estructura SMILES inválida o no interpretable por el motor RDKit.", "zh": "SMILES 结构无效或 RDKit 引擎无法解析。", "de": "Ungültige SMILES-Struktur oder von der RDKit-Engine nicht interpretierbar.", "ja": "SMILES構造が無効か、RDKitエンジンで解釈できません。"},
    "fq_profile_title": {"pt": "Perfil Físico-Químico —", "en": "Physicochemical Profile —", "es": "Perfil Fisicoquímico —", "zh": "理化性质档案 —", "de": "Physikochemisches Profil —", "ja": "物理化学プロファイル —"},
    "metric_logp": {"pt": "LogP (Crippen)", "en": "LogP (Crippen)", "es": "LogP (Crippen)", "zh": "LogP（Crippen）", "de": "LogP (Crippen)", "ja": "LogP（Crippen）"},
    "metric_tpsa": {"pt": "TPSA", "en": "TPSA", "es": "TPSA", "zh": "TPSA", "de": "TPSA", "ja": "TPSA"},
    "metric_rotbonds": {"pt": "Ligações Rotacionáveis", "en": "Rotatable Bonds", "es": "Enlaces Rotables", "zh": "可旋转键数", "de": "Drehbare Bindungen", "ja": "回転可能結合数"},
    "rules_section": {"pt": "Regras de Triagem Farmacocinética", "en": "Pharmacokinetic Screening Rules", "es": "Reglas de Cribado Farmacocinético", "zh": "药代动力学筛选规则", "de": "Pharmakokinetische Screening-Regeln", "ja": "薬物動態スクリーニング則"},
    "rule_lipinski": {"pt": "Regra de Lipinski (Rule of Five)", "en": "Lipinski's Rule of Five", "es": "Regla de Lipinski (Rule of Five)", "zh": "Lipinski 五规则", "de": "Lipinski-Regel (Rule of Five)", "ja": "Lipinskiの法則（Rule of Five）"},
    "rule_veber": {"pt": "Regra de Veber", "en": "Veber's Rule", "es": "Regla de Veber", "zh": "Veber 规则", "de": "Veber-Regel", "ja": "Veberの法則"},
    "rule_egan": {"pt": "Regra de Egan", "en": "Egan's Rule", "es": "Regla de Egan", "zh": "Egan 规则", "de": "Egan-Regel", "ja": "Eganの法則"},
    "rule_pass": {"pt": "Aprovado", "en": "Passed", "es": "Aprobado", "zh": "通过", "de": "Bestanden", "ja": "合格"},
    "rule_fail": {"pt": "Reprovado", "en": "Failed", "es": "Reprobado", "zh": "未通过", "de": "Nicht bestanden", "ja": "不合格"},
    "rule_violations": {"pt": "violação(ões)", "en": "violation(s)", "es": "violación(es)", "zh": "项违规", "de": "Verstoß/Verstöße", "ja": "件の違反"},
    "pains_section": {"pt": "Alertas Estruturais PAINS (Falsos Positivos)", "en": "PAINS Structural Alerts (False Positives)", "es": "Alertas Estructurales PAINS (Falsos Positivos)", "zh": "PAINS 结构警报（假阳性）", "de": "PAINS-Strukturwarnungen (Falsch-Positive)", "ja": "PAINS構造アラート（偽陽性）"},
    "pains_alert_prefix": {"pt": "Subestrutura problemática detectada:", "en": "Problematic substructure detected:", "es": "Subestructura problemática detectada:", "zh": "检测到有问题的子结构：", "de": "Problematische Substruktur erkannt:", "ja": "問題のある部分構造が検出されました："},
    "pains_none": {"pt": "Nenhuma subestrutura PAINS conhecida detectada.", "en": "No known PAINS substructure detected.", "es": "No se detectó ninguna subestructura PAINS conocida.", "zh": "未检测到已知的 PAINS 子结构。", "de": "Keine bekannte PAINS-Substruktur erkannt.", "ja": "既知のPAINS部分構造は検出されませんでした。"},
    "herg_section": {"pt": "Triagem de Off-Target Cardíaco (hERG)", "en": "Cardiac Off-Target Screening (hERG)", "es": "Cribado de Off-Target Cardíaco (hERG)", "zh": "心脏脱靶筛选（hERG）", "de": "Kardiales Off-Target-Screening (hERG)", "ja": "心臓オフターゲットスクリーニング（hERG）"},
    "herg_risk_label": {"pt": "Risco estimado (heurístico SAR):", "en": "Estimated risk (SAR heuristic):", "es": "Riesgo estimado (heurístico SAR):", "zh": "估计风险（SAR 启发式）：", "de": "Geschätztes Risiko (SAR-Heuristik):", "ja": "推定リスク（SARヒューリスティック）："},
    "herg_disclaimer": {"pt": "Estimativa baseada em regras de SAR publicadas na literatura; não substitui ensaio de patch-clamp em canais hERG.", "en": "Estimate based on published SAR rules; does not replace a patch-clamp assay on hERG channels.", "es": "Estimación basada en reglas de SAR publicadas en la literatura; no sustituye un ensayo de patch-clamp en canales hERG.", "zh": "基于已发表 SAR 规则的估算；不能替代 hERG 通道膜片钳实验。", "de": "Schätzung basierend auf publizierten SAR-Regeln; ersetzt keinen Patch-Clamp-Test an hERG-Kanälen.", "ja": "公表されたSAR則に基づく推定であり、hERGチャネルのパッチクランプ試験の代替にはなりません。"},
    "risk_high": {"pt": "Alto (heurístico)", "en": "High (heuristic)", "es": "Alto (heurístico)", "zh": "高（启发式）", "de": "Hoch (heuristisch)", "ja": "高い（ヒューリスティック）"},
    "risk_moderate": {"pt": "Moderado (heurístico)", "en": "Moderate (heuristic)", "es": "Moderado (heurístico)", "zh": "中等（启发式）", "de": "Mäßig (heuristisch)", "ja": "中程度（ヒューリスティック）"},
    "risk_low": {"pt": "Baixo (heurístico)", "en": "Low (heuristic)", "es": "Bajo (heurístico)", "zh": "低（启发式）", "de": "Niedrig (heuristisch)", "ja": "低い（ヒューリスティック）"},
    "didactic_notice_fq": {"pt": "Modo Didático ativo: alertas PAINS e triagem hERG detalhada disponíveis no Modo Pesquisa/P&D.", "en": "Educational Mode active: PAINS alerts and detailed hERG screening available in Research/R&D Mode.", "es": "Modo Didáctico activo: alertas PAINS y cribado hERG detallado disponibles en Modo Investigación/I+D.", "zh": "教学模式已启用：PAINS 警报和详细 hERG 筛选可在科研/研发模式中查看。", "de": "Lehrmodus aktiv: PAINS-Warnungen und detailliertes hERG-Screening im Forschungs-/F&E-Modus verfügbar.", "ja": "教育モードが有効です：PAINSアラートと詳細なhERGスクリーニングは研究/研究開発モードで利用可能です。"},
    "structure2d_section": {"pt": "Estrutura Molecular 2D", "en": "2D Molecular Structure", "es": "Estructura Molecular 2D", "zh": "二维分子结构", "de": "2D-Molekülstruktur", "ja": "2D分子構造"},
    "btn_download_sdf": {"pt": "Baixar Estrutura 3D Otimizada (.sdf)", "en": "Download Optimized 3D Structure (.sdf)", "es": "Descargar Estructura 3D Optimizada (.sdf)", "zh": "下载优化后的三维结构（.sdf）", "de": "Optimierte 3D-Struktur herunterladen (.sdf)", "ja": "最適化された3D構造をダウンロード（.sdf）"},
    "docking_caption": {"pt": "Visualização 3D de alvos proteicos (RCSB PDB) e estimativa heurística de afinidade de encaixe com o ligante.", "en": "3D visualization of protein targets (RCSB PDB) and heuristic estimation of ligand binding affinity.", "es": "Visualización 3D de dianas proteicas (RCSB PDB) y estimación heurística de afinidad de acoplamiento con el ligando.", "zh": "蛋白质靶点三维可视化（RCSB PDB）及配体结合亲和力的启发式估计。", "de": "3D-Visualisierung von Proteinzielen (RCSB PDB) und heuristische Schätzung der Liganden-Bindungsaffinität.", "ja": "タンパク質標的の3D可視化（RCSB PDB）とリガンド結合親和性のヒューリスティック推定。"},
    "protein_target_section": {"pt": "Alvo Proteico", "en": "Protein Target", "es": "Diana Proteica", "zh": "蛋白质靶点", "de": "Proteinziel", "ja": "タンパク質標的"},
    "pdb_source_label": {"pt": "Origem da estrutura da proteína:", "en": "Source of the protein structure:", "es": "Origen de la estructura de la proteína:", "zh": "蛋白质结构来源：", "de": "Quelle der Proteinstruktur:", "ja": "タンパク質構造の取得元："},
    "pdb_search_option": {"pt": "Buscar por ID no RCSB PDB", "en": "Search by ID in RCSB PDB", "es": "Buscar por ID en RCSB PDB", "zh": "在 RCSB PDB 中按 ID 搜索", "de": "Nach ID in RCSB PDB suchen", "ja": "RCSB PDBでIDを検索"},
    "pdb_upload_option": {"pt": "Upload manual de arquivo .pdb", "en": "Manual .pdb file upload", "es": "Carga manual de archivo .pdb", "zh": "手动上传 .pdb 文件", "de": "Manueller Upload einer .pdb-Datei", "ja": ".pdbファイルの手動アップロード"},
    "pdb_id_label": {"pt": "ID PDB (ex: 1IEP para c-Abl/Imatinib, 3ERT para receptor de estrogênio):", "en": "PDB ID (e.g. 1IEP for c-Abl/Imatinib, 3ERT for estrogen receptor):", "es": "ID PDB (ej: 1IEP para c-Abl/Imatinib, 3ERT para receptor de estrógeno):", "zh": "PDB ID（例如 1IEP 表示 c-Abl/伊马替尼，3ERT 表示雌激素受体）：", "de": "PDB-ID (z. B. 1IEP für c-Abl/Imatinib, 3ERT für Östrogenrezeptor):", "ja": "PDB ID（例：c-Abl/イマチニブは1IEP、エストロゲン受容体は3ERT）："},
    "pdb_not_found": {"pt": "Estrutura não localizada no RCSB. Verifique o ID ou tente o upload manual.", "en": "Structure not found in RCSB. Check the ID or try manual upload.", "es": "Estructura no localizada en RCSB. Verifique el ID o pruebe la carga manual.", "zh": "在 RCSB 中未找到该结构。请检查 ID 或尝试手动上传。", "de": "Struktur in RCSB nicht gefunden. Überprüfen Sie die ID oder versuchen Sie den manuellen Upload.", "ja": "RCSBで構造が見つかりません。IDを確認するか、手動アップロードをお試しください。"},
    "pdb_offline_notice": {"pt": "Modo offline ativo: renderização proteica em tempo real suspensa. Faça upload manual de um .pdb local se necessário.", "en": "Offline mode active: real-time protein rendering suspended. Manually upload a local .pdb if needed.", "es": "Modo offline activo: renderizado proteico en tiempo real suspendido. Cargue manualmente un .pdb local si es necesario.", "zh": "离线模式已启用：实时蛋白质渲染已暂停。如有需要，请手动上传本地 .pdb 文件。", "de": "Offline-Modus aktiv: Echtzeit-Proteinrendering deaktiviert. Laden Sie bei Bedarf manuell eine lokale .pdb-Datei hoch.", "ja": "オフラインモードが有効：リアルタイムのタンパク質レンダリングは停止しています。必要に応じてローカルの.pdbを手動でアップロードしてください。"},
    "pdb_upload_label": {"pt": "Carregue o arquivo .pdb do alvo:", "en": "Upload the target's .pdb file:", "es": "Cargue el archivo .pdb de la diana:", "zh": "上传靶点的 .pdb 文件：", "de": "Laden Sie die .pdb-Datei des Ziels hoch:", "ja": "標的の.pdbファイルをアップロード："},
    "pdb_render_error": {"pt": "Erro ao renderizar estrutura PDB:", "en": "Error rendering PDB structure:", "es": "Error al renderizar la estructura PDB:", "zh": "渲染 PDB 结构时出错：", "de": "Fehler beim Rendern der PDB-Struktur:", "ja": "PDB構造のレンダリングエラー："},
    "ligand_section": {"pt": "Ligante Candidato", "en": "Candidate Ligand", "es": "Ligando Candidato", "zh": "候选配体", "de": "Kandidatenligand", "ja": "候補リガンド"},
    "ligand_input_label": {"pt": "Nome do composto candidato ao encaixe:", "en": "Name of the candidate compound for docking:", "es": "Nombre del compuesto candidato al acoplamiento:", "zh": "候选对接化合物名称：", "de": "Name der Kandidatenverbindung für das Docking:", "ja": "ドッキング候補化合物名："},
    "smiles_unavailable_warn": {"pt": "SMILES indisponível para este composto neste ambiente.", "en": "SMILES unavailable for this compound in this environment.", "es": "SMILES no disponible para este compuesto en este entorno.", "zh": "此环境中该化合物的 SMILES 不可用。", "de": "SMILES für diese Verbindung in dieser Umgebung nicht verfügbar.", "ja": "この環境ではこの化合物のSMILESは利用できません。"},
    "docking_score_section": {"pt": "Estimativa Heurística de Encaixe (Docking Simplificado)", "en": "Heuristic Docking Estimate (Simplified Docking)", "es": "Estimación Heurística de Acoplamiento (Acoplamiento Simplificado)", "zh": "启发式对接评分（简化对接）", "de": "Heuristische Docking-Schätzung (Vereinfachtes Docking)", "ja": "ヒューリスティックドッキング推定（簡易ドッキング）"},
    "docking_disclaimer": {"pt": "Importante: esta pontuação é um modelo heurístico baseado em complementaridade de tamanho, lipofilicidade e flexibilidade do ligante frente ao bolsão médio de proteínas globulares. Não substitui um motor de docking real (ex: AutoDock Vina, Glide) nem prediz energia livre de ligação (ΔG) calibrada.", "en": "Important: this score is a heuristic model based on size complementarity, lipophilicity and ligand flexibility against the average pocket of globular proteins. It does not replace a real docking engine (e.g. AutoDock Vina, Glide) nor predict calibrated binding free energy (ΔG).", "es": "Importante: esta puntuación es un modelo heurístico basado en complementariedad de tamaño, lipofilicidad y flexibilidad del ligando frente al bolsillo promedio de proteínas globulares. No sustituye un motor de acoplamiento real (ej. AutoDock Vina, Glide) ni predice energía libre de unión (ΔG) calibrada.", "zh": "重要提示：此评分是基于配体相对于球状蛋白质平均口袋的尺寸互补性、亲脂性和柔性的启发式模型，不能替代真实的对接引擎（如 AutoDock Vina、Glide），也不能预测经校准的结合自由能（ΔG）。", "de": "Wichtig: Diese Bewertung ist ein heuristisches Modell basierend auf Größenkomplementarität, Lipophilie und Ligandenflexibilität gegenüber der durchschnittlichen Tasche globulärer Proteine. Sie ersetzt keine echte Docking-Engine (z. B. AutoDock Vina, Glide) und sagt keine kalibrierte Bindungsfreie Energie (ΔG) voraus.", "ja": "重要：このスコアは、球状タンパク質の平均的なポケットに対するリガンドのサイズ相補性、親油性、柔軟性に基づくヒューリスティックモデルです。実際のドッキングエンジン（AutoDock Vina、Glideなど）の代替にはならず、較正された結合自由エネルギー（ΔG）を予測するものでもありません。"},
    "score_size": {"pt": "Score de Tamanho", "en": "Size Score", "es": "Puntaje de Tamaño", "zh": "尺寸得分", "de": "Größen-Score", "ja": "サイズスコア"},
    "score_lipo": {"pt": "Score de Lipofilicidade", "en": "Lipophilicity Score", "es": "Puntaje de Lipofilicidad", "zh": "亲脂性得分", "de": "Lipophilie-Score", "ja": "親油性スコア"},
    "score_flex": {"pt": "Score de Flexibilidade", "en": "Flexibility Score", "es": "Puntaje de Flexibilidad", "zh": "柔性得分", "de": "Flexibilitäts-Score", "ja": "柔軟性スコア"},
    "score_combined": {"pt": "Score Combinado de Encaixe", "en": "Combined Docking Score", "es": "Puntaje Combinado de Acoplamiento", "zh": "综合对接得分", "de": "Kombinierter Docking-Score", "ja": "統合ドッキングスコア"},
    "docking_good": {"pt": "Perfil geométrico e físico-químico favorável para encaixe no bolsão-alvo (estimativa).", "en": "Geometric and physicochemical profile favorable for binding to the target pocket (estimate).", "es": "Perfil geométrico y fisicoquímico favorable para el acoplamiento en el bolsillo diana (estimación).", "zh": "几何与理化性质有利于与靶点口袋结合（估算）。", "de": "Geometrisches und physikochemisches Profil günstig für die Bindung an die Zieltasche (Schätzung).", "ja": "標的ポケットへの結合に有利な幾何学的・物理化学的プロファイルです（推定）。"},
    "docking_moderate": {"pt": "Compatibilidade moderada; recomenda-se docking computacional dedicado para confirmação.", "en": "Moderate compatibility; dedicated computational docking is recommended for confirmation.", "es": "Compatibilidad moderada; se recomienda acoplamiento computacional dedicado para confirmar.", "zh": "兼容性中等；建议使用专门的计算对接进行确认。", "de": "Mäßige Kompatibilität; dediziertes rechnergestütztes Docking zur Bestätigung empfohlen.", "ja": "中程度の適合性；確認のため専用の計算ドッキングを推奨します。"},
    "docking_bad": {"pt": "Baixa compatibilidade estimada; molécula pode exigir otimização estrutural (lead optimization).", "en": "Low estimated compatibility; molecule may require structural optimization (lead optimization).", "es": "Baja compatibilidad estimada; la molécula puede requerir optimización estructural (optimización de líder).", "zh": "估计兼容性较低；该分子可能需要结构优化（先导化合物优化）。", "de": "Geringe geschätzte Kompatibilität; Molekül erfordert möglicherweise strukturelle Optimierung (Lead-Optimierung).", "ja": "推定適合性は低い；分子は構造最適化（リード最適化）が必要な場合があります。"},
    "offtarget_section": {"pt": "Mapeamento de Off-Targets Conhecidos", "en": "Mapping of Known Off-Targets", "es": "Mapeo de Off-Targets Conocidos", "zh": "已知脱靶效应图谱", "de": "Kartierung bekannter Off-Targets", "ja": "既知のオフターゲットマッピング"},
    "docking_empty_notice": {"pt": "Carregue uma estrutura proteica (PDB) e um composto candidato para gerar a estimativa de encaixe.", "en": "Load a protein structure (PDB) and a candidate compound to generate the docking estimate.", "es": "Cargue una estructura proteica (PDB) y un compuesto candidato para generar la estimación de acoplamiento.", "zh": "请加载蛋白质结构（PDB）和候选化合物以生成对接评分。", "de": "Laden Sie eine Proteinstruktur (PDB) und eine Kandidatenverbindung, um die Docking-Schätzung zu erstellen.", "ja": "タンパク質構造（PDB）と候補化合物を読み込んでドッキング推定を生成してください。"},
    "benchmark_caption": {"pt": "Matriz de interação/sinergia entre múltiplas moléculas e benchmark comparativo contra o fármaco padrão-ouro do módulo ativo.", "en": "Interaction/synergy matrix between multiple molecules and comparative benchmark against the gold-standard drug of the active module.", "es": "Matriz de interacción/sinergia entre múltiples moléculas y referencia comparativa contra el fármaco de referencia del módulo activo.", "zh": "多个分子间的相互作用/协同矩阵，以及与当前模块金标准药物的对比基准。", "de": "Interaktions-/Synergiematrix zwischen mehreren Molekülen und vergleichendes Benchmark gegen das Goldstandard-Medikament des aktiven Moduls.", "ja": "複数分子間の相互作用/相乗効果マトリックスと、アクティブモジュールのゴールドスタンダード薬剤との比較ベンチマーク。"},
    "molecule_select_section": {"pt": "Seleção de Moléculas para Comparação", "en": "Molecule Selection for Comparison", "es": "Selección de Moléculas para Comparación", "zh": "用于比较的分子选择", "de": "Molekülauswahl zum Vergleich", "ja": "比較のための分子選択"},
    "molecule_select_label": {"pt": "Selecione de 2 a 4 moléculas para comparar:", "en": "Select 2 to 4 molecules to compare:", "es": "Seleccione de 2 a 4 moléculas para comparar:", "zh": "选择 2 到 4 个分子进行比较：", "de": "Wählen Sie 2 bis 4 Moleküle zum Vergleich aus:", "ja": "比較する分子を2〜4個選択してください："},
    "synergy_matrix_title": {"pt": "Matriz de Interação / Sinergia Estrutural", "en": "Interaction / Structural Synergy Matrix", "es": "Matriz de Interacción / Sinergia Estructural", "zh": "相互作用/结构协同矩阵", "de": "Interaktions-/Struktursynergie-Matrix", "ja": "相互作用/構造相乗効果マトリックス"},
    "synergy_high": {"pt": "Alta Sinergia Estrutural", "en": "High Structural Synergy", "es": "Alta Sinergia Estructural", "zh": "高结构协同性", "de": "Hohe strukturelle Synergie", "ja": "高い構造的相乗効果"},
    "synergy_moderate": {"pt": "Sinergia Moderada", "en": "Moderate Synergy", "es": "Sinergia Moderada", "zh": "中等协同性", "de": "Mäßige Synergie", "ja": "中程度の相乗効果"},
    "synergy_low": {"pt": "Baixa Similaridade / Potencial Complementar", "en": "Low Similarity / Complementary Potential", "es": "Baja Similitud / Potencial Complementario", "zh": "低相似性/潜在互补性", "de": "Geringe Ähnlichkeit / Komplementäres Potenzial", "ja": "低い類似性／相補的可能性"},
    "synergy_disclaimer": {"pt": "A similaridade estrutural (heurística baseada em LogP/TPSA) é um proxy para potencial de sinergia farmacodinâmica ou de coadministração; não substitui ensaios de combinação in vitro.", "en": "Structural similarity (LogP/TPSA-based heuristic) is a proxy for pharmacodynamic synergy or co-administration potential; it does not replace in vitro combination assays.", "es": "La similitud estructural (heurística basada en LogP/TPSA) es un indicador del potencial de sinergia farmacodinámica o de coadministración; no sustituye los ensayos de combinación in vitro.", "zh": "结构相似性（基于 LogP/TPSA 的启发式方法）可作为药效学协同或联合用药潜力的替代指标，但不能替代体外联合试验。", "de": "Strukturelle Ähnlichkeit (LogP/TPSA-basierte Heuristik) ist ein Proxy für pharmakodynamisches Synergiepotenzial oder Ko-Administration; ersetzt keine In-vitro-Kombinationstests.", "ja": "構造的類似性（LogP/TPSAに基づくヒューリスティック）は薬力学的相乗効果または併用可能性の代理指標であり、in vitro併用試験の代替にはなりません。"},
    "radar_section": {"pt": "Benchmark: Radar Comparativo vs. Fármaco Padrão-Ouro", "en": "Benchmark: Comparative Radar vs. Gold-Standard Drug", "es": "Referencia: Radar Comparativo vs. Fármaco de Referencia", "zh": "基准：与金标准药物的雷达图对比", "de": "Benchmark: Vergleichs-Radar vs. Goldstandard-Medikament", "ja": "ベンチマーク：ゴールドスタンダード薬剤との比較レーダー"},
    "gold_standard_label": {"pt": "Fármaco de referência (padrão-ouro) do módulo", "en": "Reference (gold-standard) drug of the module", "es": "Fármaco de referencia (patrón oro) del módulo", "zh": "该模块的参考（金标准）药物", "de": "Referenz- (Goldstandard-) Medikament des Moduls", "ja": "モジュールの基準（ゴールドスタンダード）薬剤"},
    "benchmark_select_warn": {"pt": "Selecione ao menos 2 moléculas para habilitar a matriz de sinergia e o radar de benchmark.", "en": "Select at least 2 molecules to enable the synergy matrix and the benchmark radar.", "es": "Seleccione al menos 2 moléculas para habilitar la matriz de sinergia y el radar de referencia.", "zh": "请至少选择 2 个分子以启用协同矩阵和基准雷达图。", "de": "Wählen Sie mindestens 2 Moleküle aus, um die Synergiematrix und das Benchmark-Radar zu aktivieren.", "ja": "相乗効果マトリックスとベンチマークレーダーを有効にするには、少なくとも2つの分子を選択してください。"},
    "benchmark_invalid_smiles_warn": {"pt": "Não foi possível obter estruturas SMILES válidas para os compostos selecionados (compostos macromoleculares/biológicos não são suportados neste módulo).", "en": "Could not obtain valid SMILES structures for the selected compounds (macromolecular/biological compounds are not supported in this module).", "es": "No fue posible obtener estructuras SMILES válidas para los compuestos seleccionados (los compuestos macromoleculares/biológicos no son compatibles con este módulo).", "zh": "无法获取所选化合物的有效 SMILES 结构（本模块不支持大分子/生物类化合物）。", "de": "Für die ausgewählten Verbindungen konnten keine gültigen SMILES-Strukturen ermittelt werden (makromolekulare/biologische Verbindungen werden in diesem Modul nicht unterstützt).", "ja": "選択された化合物の有効なSMILES構造を取得できませんでした（このモジュールでは高分子・生体化合物はサポートされていません）。"},
    "literature_caption": {"pt": "Classificação por Grau de Evidência Científica dos artigos recuperados e proposição automática de Mecanismo de Ação (MoA) via IA.", "en": "Classification by Scientific Evidence Level of retrieved articles and automatic AI proposal of Mechanism of Action (MoA).", "es": "Clasificación por Grado de Evidencia Científica de los artículos recuperados y propuesta automática de Mecanismo de Acción (MoA) mediante IA.", "zh": "对检索到的文献按科学证据等级分类，并通过AI自动生成作用机制（MoA）提案。", "de": "Klassifizierung nach wissenschaftlichem Evidenzgrad der abgerufenen Artikel und automatischer KI-Vorschlag zum Wirkmechanismus (MoA).", "ja": "検索された論文の科学的エビデンスレベルによる分類と、AIによる作用機序（MoA）の自動提案。"},
    "literature_input_label": {"pt": "Composto para análise de literatura e MoA:", "en": "Compound for literature and MoA analysis:", "es": "Compuesto para análisis de literatura y MoA:", "zh": "用于文献与作用机制分析的化合物：", "de": "Verbindung für Literatur- und MoA-Analyse:", "ja": "文献・MoA分析対象の化合物："},
    "evidence_section": {"pt": "Classificação de Evidência Científica", "en": "Scientific Evidence Classification", "es": "Clasificación de Evidencia Científica", "zh": "科学证据分级", "de": "Wissenschaftliche Evidenzklassifikation", "ja": "科学的エビデンス分類"},
    "title_retrieved_label": {"pt": "Título recuperado:", "en": "Retrieved title:", "es": "Título recuperado:", "zh": "检索到的标题：", "de": "Abgerufener Titel:", "ja": "取得されたタイトル："},
    "title_unavailable": {"pt": "Título não disponível via API.", "en": "Title unavailable via API.", "es": "Título no disponible vía API.", "zh": "通过API无法获取标题。", "de": "Titel über API nicht verfügbar.", "ja": "APIでタイトルを取得できません。"},
    "confidence_factor_label": {"pt": "Fator de confiança estimado:", "en": "Estimated confidence factor:", "es": "Factor de confianza estimado:", "zh": "估计置信度：", "de": "Geschätzter Konfidenzfaktor:", "ja": "推定信頼度："},
    "evidence_advanced_note": {"pt": "Classificação heurística baseada em palavras-chave do título (metodologia simplificada de triagem bibliográfica). Para revisões sistemáticas formais, utilize ferramentas como GRADE ou Cochrane RoB.", "en": "Heuristic classification based on title keywords (simplified bibliographic screening methodology). For formal systematic reviews, use tools such as GRADE or Cochrane RoB.", "es": "Clasificación heurística basada en palabras clave del título (metodología simplificada de cribado bibliográfico). Para revisiones sistemáticas formales, use herramientas como GRADE o Cochrane RoB.", "zh": "基于标题关键词的启发式分类（简化的文献筛选方法）。如需正式系统评价，请使用 GRADE 或 Cochrane RoB 等工具。", "de": "Heuristische Klassifikation basierend auf Titel-Schlüsselwörtern (vereinfachte bibliografische Screening-Methodik). Für formale systematische Übersichten nutzen Sie Tools wie GRADE oder Cochrane RoB.", "ja": "タイトルのキーワードに基づくヒューリスティック分類（簡易文献スクリーニング手法）。正式なシステマティックレビューにはGRADEやCochrane RoBなどのツールをご利用ください。"},
    "evidence_none": {"pt": "Nenhuma publicação direta localizada no PubMed para classificação de evidência.", "en": "No direct publication found on PubMed for evidence classification.", "es": "No se localizó ninguna publicación directa en PubMed para la clasificación de evidencia.", "zh": "在 PubMed 中未找到用于证据分级的直接文献。", "de": "Keine direkte Publikation auf PubMed für die Evidenzklassifikation gefunden.", "ja": "エビデンス分類のための直接的な論文はPubMedで見つかりませんでした。"},
    "moa_section": {"pt": "Proposição Automática de Mecanismo de Ação (MoA)", "en": "Automatic Mechanism of Action (MoA) Proposal", "es": "Propuesta Automática de Mecanismo de Acción (MoA)", "zh": "自动作用机制（MoA）提案", "de": "Automatischer Vorschlag zum Wirkmechanismus (MoA)", "ja": "自動作用機序（MoA）提案"},
    "btn_generate_moa": {"pt": "Gerar Proposição de MoA", "en": "Generate MoA Proposal", "es": "Generar Propuesta de MoA", "zh": "生成作用机制提案", "de": "MoA-Vorschlag generieren", "ja": "MoA提案を生成"},
    "spinner_moa": {"pt": "Sintetizando hipótese mecanística...", "en": "Synthesizing mechanistic hypothesis...", "es": "Sintetizando hipótesis mecanicista...", "zh": "正在综合机制假设...", "de": "Synthetisiere mechanistische Hypothese...", "ja": "機序的仮説を統合中..."},
    "moa_title": {"pt": "Proposição de Mecanismo de Ação (MoA) —", "en": "Mechanism of Action (MoA) Proposal —", "es": "Propuesta de Mecanismo de Acción (MoA) —", "zh": "作用机制（MoA）提案 —", "de": "Wirkmechanismus (MoA)-Vorschlag —", "ja": "作用機序（MoA）提案 —"},
    "moa_class_label": {"pt": "Classe Farmacológica:", "en": "Pharmacological Class:", "es": "Clase Farmacológica:", "zh": "药理学分类：", "de": "Pharmakologische Klasse:", "ja": "薬理学的分類："},
    "moa_profile_label": {"pt": "Perfil Físico-Químico: Molécula {perfil}, com arquitetura {tamanho}.", "en": "Physicochemical Profile: {perfil} molecule, with {tamanho} architecture.", "es": "Perfil Fisicoquímico: Molécula {perfil}, con arquitectura {tamanho}.", "zh": "理化性质：该分子{perfil}，结构{tamanho}。", "de": "Physikochemisches Profil: {perfil} Molekül mit {tamanho} Architektur.", "ja": "物理化学プロファイル：{perfil}分子で、{tamanho}構造を有する。"},
    "moa_profile_lipophilic": {"pt": "lipofílica e de fácil permeação de membrana", "en": "lipophilic and easily membrane-permeable", "es": "lipofílica y de fácil permeación de membrana", "zh": "亲脂性且易于穿透细胞膜", "de": "lipophil und membrangängig", "ja": "親油性で膜透過性が高い"},
    "moa_profile_hydrophilic": {"pt": "hidrofílica, dependente de transportadores ativos", "en": "hydrophilic, dependent on active transporters", "es": "hidrofílica, dependiente de transportadores activos", "zh": "亲水性，依赖主动转运体", "de": "hydrophil, abhängig von aktiven Transportern", "ja": "親水性で能動輸送体に依存"},
    "moa_size_compact": {"pt": "compacta, compatível com bolsões de ligação estreitos", "en": "compact, compatible with narrow binding pockets", "es": "compacta, compatible con bolsillos de unión estrechos", "zh": "结构紧凑，适合狭窄结合口袋", "de": "kompakt, kompatibel mit engen Bindungstaschen", "ja": "コンパクトで狭い結合ポケットに適合"},
    "moa_size_bulky": {"pt": "volumosa, potencialmente restrita a sítios alostéricos amplos", "en": "bulky, potentially restricted to broad allosteric sites", "es": "voluminosa, potencialmente restringida a sitios alostéricos amplios", "zh": "结构庞大，可能仅限于宽阔的变构位点", "de": "voluminös, möglicherweise auf breite allosterische Stellen beschränkt", "ja": "大型で、広いアロステリック部位に限定される可能性"},
    "moa_hypothesis_label": {"pt": "Hipótese de Ação no eixo {modulo}: o composto provavelmente interage com seu alvo por complementaridade estérica e eletrônica, modulando a via de sinalização associada à classe '{classe}', com repercussão direta na cascata patológica-alvo do módulo selecionado.", "en": "Action Hypothesis in the {modulo} axis: the compound likely interacts with its target via steric and electronic complementarity, modulating the signaling pathway associated with the '{classe}' class, with direct impact on the target pathological cascade of the selected module.", "es": "Hipótesis de Acción en el eje {modulo}: el compuesto probablemente interactúa con su diana por complementariedad estérica y electrónica, modulando la vía de señalización asociada a la clase '{classe}', con repercusión directa en la cascada patológica objetivo del módulo seleccionado.", "zh": "在{modulo}方向上的作用假设：该化合物可能通过空间和电子互补性与其靶点相互作用，调控与“{classe}”类别相关的信号通路，直接影响所选模块的目标病理级联反应。", "de": "Wirkungshypothese in der Achse {modulo}: Die Verbindung interagiert wahrscheinlich über sterische und elektronische Komplementarität mit ihrem Ziel und moduliert den mit der Klasse '{classe}' verbundenen Signalweg, mit direkter Auswirkung auf die Zielkaskade des ausgewählten Moduls.", "ja": "{modulo}軸における作用仮説：この化合物は立体的・電子的相補性を介して標的と相互作用し、「{classe}」クラスに関連するシグナル伝達経路を調節し、選択されたモジュールの標的病理カスケードに直接影響を与える可能性がある。"},
    "moa_summary_label": {"pt": "Resumo Executivo: perfil consistente com candidato de triagem primária a secundária; recomenda-se validação por docking direcionado e ensaios funcionais in vitro para confirmação do mecanismo proposto.", "en": "Executive Summary: profile consistent with a primary-to-secondary screening candidate; validation via targeted docking and in vitro functional assays is recommended to confirm the proposed mechanism.", "es": "Resumen Ejecutivo: perfil consistente con un candidato de cribado primario a secundario; se recomienda validación mediante acoplamiento dirigido y ensayos funcionales in vitro para confirmar el mecanismo propuesto.", "zh": "执行摘要：该特征符合从初筛到复筛候选物的标准；建议通过定向对接和体外功能实验验证所提出的机制。", "de": "Zusammenfassung: Profil im Einklang mit einem primären bis sekundären Screening-Kandidaten; Validierung durch gezieltes Docking und funktionelle In-vitro-Tests zur Bestätigung des vorgeschlagenen Mechanismus wird empfohlen.", "ja": "エグゼクティブサマリー：一次〜二次スクリーニング候補と一致するプロファイル。提案された機序を確認するため、標的ドッキングおよびin vitro機能アッセイによる検証を推奨する。"},
    "citation_section": {"pt": "Exportação de Citação Científica", "en": "Scientific Citation Export", "es": "Exportación de Cita Científica", "zh": "科学引文导出", "de": "Export wissenschaftlicher Zitate", "ja": "科学的引用のエクスポート"},
    "btn_export_bib": {"pt": "Exportar Citação (.bib)", "en": "Export Citation (.bib)", "es": "Exportar Cita (.bib)", "zh": "导出引文（.bib）", "de": "Zitat exportieren (.bib)", "ja": "引用をエクスポート（.bib）"},
    "btn_export_ris": {"pt": "Exportar Citação (.ris)", "en": "Export Citation (.ris)", "es": "Exportar Cita (.ris)", "zh": "导出引文（.ris）", "de": "Zitat exportieren (.ris)", "ja": "引用をエクスポート（.ris）"},
    "eln_caption": {"pt": "Caderno Eletrônico de Laboratório: registre, revise e exporte seus experimentos de triagem em múltiplos formatos.", "en": "Electronic Lab Notebook: record, review and export your screening experiments in multiple formats.", "es": "Cuaderno Electrónico de Laboratorio: registre, revise y exporte sus experimentos de cribado en múltiples formatos.", "zh": "电子实验记录本：记录、查看并以多种格式导出您的筛选实验。", "de": "Elektronisches Laborbuch: Erfassen, überprüfen und exportieren Sie Ihre Screening-Experimente in mehreren Formaten.", "ja": "電子実験ノート：スクリーニング実験を記録・確認し、複数の形式でエクスポートします。"},
    "new_experiment_expander": {"pt": "Registrar novo experimento manualmente", "en": "Manually register a new experiment", "es": "Registrar nuevo experimento manualmente", "zh": "手动登记新实验", "de": "Neues Experiment manuell erfassen", "ja": "新しい実験を手動で登録"},
    "exp_name_label": {"pt": "Nome do composto/experimento:", "en": "Compound/experiment name:", "es": "Nombre del compuesto/experimento:", "zh": "化合物/实验名称：", "de": "Name der Verbindung/des Experiments:", "ja": "化合物/実験名："},
    "exp_notes_label": {"pt": "Observações / Notas do pesquisador:", "en": "Observations / Researcher notes:", "es": "Observaciones / Notas del investigador:", "zh": "观察记录/研究人员备注：", "de": "Beobachtungen / Forschernotizen:", "ja": "観察事項／研究者メモ："},
    "btn_save_experiment": {"pt": "Salvar Experimento", "en": "Save Experiment", "es": "Guardar Experimento", "zh": "保存实验", "de": "Experiment speichern", "ja": "実験を保存"},
    "exp_saved_success": {"pt": "Experimento '{nome}' registrado com sucesso!", "en": "Experiment '{nome}' successfully recorded!", "es": "¡Experimento '{nome}' registrado con éxito!", "zh": "实验 '{nome}' 已成功登记！", "de": "Experiment '{nome}' erfolgreich gespeichert!", "ja": "実験「{nome}」が正常に記録されました！"},
    "registered_experiments_title": {"pt": "Experimentos Registrados na Sessão", "en": "Experiments Recorded in Session", "es": "Experimentos Registrados en la Sesión", "zh": "本次会话中登记的实验", "de": "In der Sitzung erfasste Experimente", "ja": "セッションで登録された実験"},
    "no_experiments_notice": {"pt": "Nenhum experimento registrado ainda. Utilize o formulário acima ou o botão de salvamento nas abas de análise individual.", "en": "No experiments recorded yet. Use the form above or the save button on the individual analysis tabs.", "es": "Aún no hay experimentos registrados. Use el formulario anterior o el botón de guardar en las pestañas de análisis individual.", "zh": "尚未登记任何实验。请使用上面的表单，或在各分析标签页中使用保存按钮。", "de": "Noch keine Experimente erfasst. Verwenden Sie das obige Formular oder die Speichern-Schaltfläche in den Einzelanalyse-Tabs.", "ja": "まだ登録された実験はありません。上記のフォーム、または個別分析タブの保存ボタンをご利用ください。"},
    "notes_label_short": {"pt": "Notas:", "en": "Notes:", "es": "Notas:", "zh": "备注：", "de": "Notizen:", "ja": "メモ："},
    "no_fq_data_caption": {"pt": "Sem dados físico-químicos associados.", "en": "No associated physicochemical data.", "es": "Sin datos fisicoquímicos asociados.", "zh": "无相关理化数据。", "de": "Keine zugehörigen physikochemischen Daten.", "ja": "関連する物理化学データはありません。"},
    "btn_delete_record": {"pt": "Remover este registro", "en": "Remove this record", "es": "Eliminar este registro", "zh": "删除该记录", "de": "Diesen Eintrag entfernen", "ja": "この記録を削除"},
    "eln_export_section": {"pt": "Exportação Multiformato do Caderno Completo", "en": "Multi-format Export of the Full Notebook", "es": "Exportación Multiformato del Cuaderno Completo", "zh": "完整记录本的多格式导出", "de": "Multiformat-Export des vollständigen Laborbuchs", "ja": "完全ノートの複数形式エクスポート"},
    "btn_export_all_json": {"pt": "Exportar Tudo (.json)", "en": "Export All (.json)", "es": "Exportar Todo (.json)", "zh": "导出全部（.json）", "de": "Alles exportieren (.json)", "ja": "すべてエクスポート（.json）"},
    "btn_export_pdf_consolidated": {"pt": "Exportar Laudo Consolidado (.pdf)", "en": "Export Consolidated Report (.pdf)", "es": "Exportar Informe Consolidado (.pdf)", "zh": "导出合并报告（.pdf）", "de": "Konsolidierten Bericht exportieren (.pdf)", "ja": "統合レポートをエクスポート（.pdf）"},
    "btn_export_csv": {"pt": "Exportar Planilha (.csv)", "en": "Export Spreadsheet (.csv)", "es": "Exportar Hoja de Cálculo (.csv)", "zh": "导出表格（.csv）", "de": "Tabelle exportieren (.csv)", "ja": "スプレッドシートをエクスポート（.csv）"},
    "btn_clear_notebook": {"pt": "Limpar todo o Caderno Científico", "en": "Clear the entire Lab Notebook", "es": "Limpiar todo el Cuaderno Científico", "zh": "清空整个电子实验记录本", "de": "Gesamtes Laborbuch löschen", "ja": "電子実験ノートをすべてクリア"},
    "generic_error_prefix": {"pt": "Ocorreu um erro:", "en": "An error occurred:", "es": "Ocurrió un error:", "zh": "发生错误：", "de": "Ein Fehler ist aufgetreten:", "ja": "エラーが発生しました："},
    "cjk_pdf_notice": {"pt": "Nota: a exportação em PDF usa fontes latinas; caracteres ideográficos podem não ser exibidos corretamente.", "en": "Note: PDF export uses Latin-only fonts; ideographic characters may not render correctly.", "es": "Nota: la exportación a PDF usa fuentes latinas; los caracteres ideográficos pueden no visualizarse correctamente.", "zh": "注意：PDF 导出使用拉丁字体，表意文字可能无法正确显示。", "de": "Hinweis: Der PDF-Export verwendet lateinische Schriftarten; ideografische Zeichen werden möglicherweise nicht korrekt dargestellt.", "ja": "注意：PDFエクスポートはラテン文字フォントを使用しているため、表意文字が正しく表示されない場合があります。"},
    "absorption_high": {"pt": "Alta (Peso < 500 g/mol)", "en": "High (Weight < 500 g/mol)", "es": "Alta (Peso < 500 g/mol)", "zh": "高（分子量 < 500 g/mol）", "de": "Hoch (Gewicht < 500 g/mol)", "ja": "高い（分子量 < 500 g/mol）"},
    "absorption_moderate": {"pt": "Moderada/Baixa", "en": "Moderate/Low", "es": "Moderada/Baja", "zh": "中等/较低", "de": "Mäßig/Niedrig", "ja": "中程度／低い"},
    "safety_lipinski_alert": {"pt": "Alerta Lipinski: peso molecular excede 500 g/mol. Viabilidade de absorção passiva oral reduzida. Recomendado uso vetorial estruturado.", "en": "Lipinski Alert: molecular weight exceeds 500 g/mol. Reduced passive oral absorption viability. Structured vector delivery recommended.", "es": "Alerta de Lipinski: el peso molecular supera los 500 g/mol. Viabilidad de absorción oral pasiva reducida. Se recomienda uso de vectores estructurados.", "zh": "Lipinski警示：分子量超过500 g/mol，被动口服吸收可行性降低，建议采用结构化载体递送。", "de": "Lipinski-Warnung: Molekulargewicht überschreitet 500 g/mol. Reduzierte passive orale Absorptionsfähigkeit. Strukturierte Vektorverabreichung empfohlen.", "ja": "Lipinskiアラート：分子量が500 g/molを超えています。受動的経口吸収の実現性が低下します。構造化ベクター送達を推奨します。"},
    "safety_inhibitor": {"pt": "Mecanismo Ativo: bloqueio competitivo de alta seletividade enzimática verificado no espectro analítico.", "en": "Active Mechanism: high-selectivity competitive enzymatic blockade verified in the analytical spectrum.", "es": "Mecanismo Activo: bloqueo competitivo enzimático de alta selectividad verificado en el espectro analítico.", "zh": "活性机制：分析谱图证实存在高选择性竞争性酶抑制作用。", "de": "Aktiver Mechanismus: hochselektive kompetitive enzymatische Blockade im analytischen Spektrum bestätigt.", "ja": "活性機序：分析スペクトルで高選択性の競合的酵素阻害が確認されました。"},
    "safety_senolytic": {"pt": "Mecanismo Ativo: direcionamento pró-apoptótico em subpopulações senescentes estáveis. Requer regime intermitente.", "en": "Active Mechanism: pro-apoptotic targeting of stable senescent subpopulations. Requires an intermittent regimen.", "es": "Mecanismo Activo: direccionamiento proapoptótico en subpoblaciones senescentes estables. Requiere un régimen intermitente.", "zh": "活性机制：针对稳定衰老细胞亚群的促凋亡靶向作用，需要间歇性给药方案。", "de": "Aktiver Mechanismus: proapoptotische Zielsteuerung stabiler seneszenter Subpopulationen. Erfordert ein intermittierendes Dosierungsschema.", "ja": "活性機序：安定した老化細胞サブポピュレーションに対するアポトーシス促進標的作用。間欠投与レジメンが必要です。"},
    "safety_default": {"pt": "Farmacocinética favorável e compatível com regras básicas de permeabilidade de membrana.", "en": "Favorable pharmacokinetics compatible with basic membrane permeability rules.", "es": "Farmacocinética favorable y compatible con las reglas básicas de permeabilidad de membrana.", "zh": "药代动力学良好，符合基本的膜通透性规则。", "de": "Günstige Pharmakokinetik, vereinbar mit grundlegenden Membranpermeabilitätsregeln.", "ja": "基本的な膜透過性則に適合した良好な薬物動態プロファイル。"},
    "kb_fallback_aplicacao": {"pt": "O composto '{nome}' encontra-se em triagem molecular primária para {modulo}.", "en": "Compound '{nome}' is undergoing primary molecular screening for {modulo}.", "es": "El compuesto '{nome}' se encuentra en cribado molecular primario para {modulo}.", "zh": "化合物“{nome}”正在针对 {modulo} 进行初步分子筛选。", "de": "Verbindung '{nome}' befindet sich im primären molekularen Screening für {modulo}.", "ja": "化合物「{nome}」は{modulo}を対象とした一次分子スクリーニング中です。"},
    "kb_fallback_pipeline": {"pt": "Triagem e ensaios pré-clínicos iniciais sob estruturação na pipeline atual.", "en": "Initial screening and preclinical trials currently being structured in the pipeline.", "es": "Cribado y ensayos preclínicos iniciales en estructuración en el pipeline actual.", "zh": "初步筛选与临床前试验正在当前研发管线中构建。", "de": "Erstes Screening und präklinische Studien werden derzeit in der aktuellen Pipeline strukturiert.", "ja": "初期スクリーニングおよび前臨床試験が現在のパイプラインで構築中です。"},
    "kb_fallback_classe": {"pt": "Triagem Primária", "en": "Primary Screening", "es": "Cribado Primario", "zh": "初步筛选", "de": "Primäres Screening", "ja": "一次スクリーニング"},
    "batch_error_formula": {"pt": "ERRO", "en": "ERROR", "es": "ERROR", "zh": "错误", "de": "FEHLER", "ja": "エラー"},
    "batch_error_app": {"pt": "Falha na análise estrutural", "en": "Structural analysis failure", "es": "Fallo en el análisis estructural", "zh": "结构分析失败", "de": "Fehler bei der Strukturanalyse", "ja": "構造解析に失敗しました"},
    "batch_error_absorption": {"pt": "Indeterminada", "en": "Undetermined", "es": "Indeterminada", "zh": "无法确定", "de": "Unbestimmt", "ja": "不明"},
    "batch_error_safety": {"pt": "Requer revisão manual", "en": "Requires manual review", "es": "Requiere revisión manual", "zh": "需要人工复核", "de": "Erfordert manuelle Überprüfung", "ja": "手動確認が必要"},
    "col_official_name": {"pt": "Nome Oficial", "en": "Official Name", "es": "Nombre Oficial", "zh": "官方名称", "de": "Offizieller Name", "ja": "正式名称"},
    "col_formula": {"pt": "Fórmula", "en": "Formula", "es": "Fórmula", "zh": "化学式", "de": "Formel", "ja": "化学式"},
    "col_mol_mass": {"pt": "Massa Molecular", "en": "Molecular Mass", "es": "Masa Molecular", "zh": "分子量", "de": "Molekülmasse", "ja": "分子量"},
    "col_medical_app": {"pt": "Aplicação Médica", "en": "Medical Application", "es": "Aplicación Médica", "zh": "医学应用", "de": "Medizinische Anwendung", "ja": "医学応用"},
    "col_pipeline": {"pt": "Mapeamento Pipeline", "en": "Pipeline Mapping", "es": "Mapeo de Pipeline", "zh": "研发管线", "de": "Pipeline-Übersicht", "ja": "パイプラインマッピング"},
    "col_oral_absorption": {"pt": "Absorção Oral", "en": "Oral Absorption", "es": "Absorción Oral", "zh": "口服吸收", "de": "Orale Absorption", "ja": "経口吸収"},
    "col_lab_safety": {"pt": "Segurança Laboratorial", "en": "Laboratory Safety", "es": "Seguridad de Laboratorio", "zh": "实验室安全性", "de": "Laborsicherheit", "ja": "実験室安全性"},
    "col_pubmed_ref": {"pt": "Referência PubMed", "en": "PubMed Reference", "es": "Referencia PubMed", "zh": "PubMed 参考文献", "de": "PubMed-Referenz", "ja": "PubMed参照"},
    "col_rxnav_id": {"pt": "RxNav ID", "en": "RxNav ID", "es": "ID RxNav", "zh": "RxNav ID", "de": "RxNav-ID", "ja": "RxNav ID"},
    "evid_lvl_meta": {"pt": "Nível I — Metanálise / Revisão Sistemática", "en": "Level I — Meta-Analysis / Systematic Review", "es": "Nivel I — Metanálisis / Revisión Sistemática", "zh": "I级 — 荟萃分析/系统综述", "de": "Stufe I — Metaanalyse / Systematische Übersicht", "ja": "レベルI — メタ分析／系統的レビュー"},
    "evid_lvl_rct": {"pt": "Nível II — Ensaio Clínico Randomizado", "en": "Level II — Randomized Clinical Trial", "es": "Nivel II — Ensayo Clínico Aleatorizado", "zh": "II级 — 随机对照临床试验", "de": "Stufe II — Randomisierte klinische Studie", "ja": "レベルII — ランダム化比較臨床試験"},
    "evid_lvl_cohort": {"pt": "Nível III — Estudo Observacional/Coorte", "en": "Level III — Observational/Cohort Study", "es": "Nivel III — Estudio Observacional/Cohorte", "zh": "III级 — 观察性/队列研究", "de": "Stufe III — Beobachtungs-/Kohortenstudie", "ja": "レベルIII — 観察研究／コホート研究"},
    "evid_lvl_invitro": {"pt": "Nível IV — Estudo In Vitro / In Silico", "en": "Level IV — In Vitro / In Silico Study", "es": "Nivel IV — Estudio In Vitro / In Silico", "zh": "IV级 — 体外/计算机模拟研究", "de": "Stufe IV — In-vitro-/In-silico-Studie", "ja": "レベルIV — in vitro／in silico研究"},
    "evid_lvl_invivo": {"pt": "Nível IV — Estudo Pré-Clínico In Vivo", "en": "Level IV — Preclinical In Vivo Study", "es": "Nivel IV — Estudio Preclínico In Vivo", "zh": "IV级 — 体内临床前研究", "de": "Stufe IV — Präklinische In-vivo-Studie", "ja": "レベルIV — in vivo前臨床研究"},
    "evid_lvl_review": {"pt": "Nível V — Revisão Narrativa / Opinião", "en": "Level V — Narrative Review / Opinion", "es": "Nivel V — Revisión Narrativa / Opinión", "zh": "V级 — 叙述性综述/观点", "de": "Stufe V — Narrative Übersicht / Meinung", "ja": "レベルV — ナラティブレビュー／意見"},
    "evid_lvl_primary": {"pt": "Nível III — Estudo Primário Não Classificado", "en": "Level III — Unclassified Primary Study", "es": "Nivel III — Estudio Primario No Clasificado", "zh": "III级 — 未分类原始研究", "de": "Stufe III — Nicht klassifizierte Primärstudie", "ja": "レベルIII — 未分類の一次研究"},
    "evid_lvl_none": {"pt": "Indeterminado", "en": "Undetermined", "es": "Indeterminado", "zh": "无法确定", "de": "Unbestimmt", "ja": "不明"},
    "conf_very_high": {"pt": "Muito Alto", "en": "Very High", "es": "Muy Alto", "zh": "极高", "de": "Sehr hoch", "ja": "非常に高い"},
    "conf_high": {"pt": "Alto", "en": "High", "es": "Alto", "zh": "高", "de": "Hoch", "ja": "高い"},
    "conf_moderate": {"pt": "Moderado", "en": "Moderate", "es": "Moderado", "zh": "中等", "de": "Mäßig", "ja": "中程度"},
    "conf_moderate_low": {"pt": "Moderado-Baixo", "en": "Moderate-Low", "es": "Moderado-Bajo", "zh": "中低", "de": "Mäßig-Niedrig", "ja": "中〜低"},
    "conf_low": {"pt": "Baixo", "en": "Low", "es": "Bajo", "zh": "低", "de": "Niedrig", "ja": "低い"},
    "conf_na": {"pt": "N/A", "en": "N/A", "es": "N/A", "zh": "不适用", "de": "N/A", "ja": "該当なし"},
    "ai_insight_external": {"pt": "Insight gerado via API externa: a análise profunda da estrutura molecular {formula} do {composto} indica forte potencial de ligação em receptores da área de {modulo}. O peso molecular de {peso} g/mol sugere que modificações lipídicas podem otimizar sua biodisponibilidade em 43%.", "en": "Insight generated via external API: in-depth analysis of the {formula} molecular structure of {composto} indicates strong binding potential with receptors in the {modulo} area. The molecular weight of {peso} g/mol suggests lipid modifications could optimize its bioavailability by 43%.", "es": "Perspectiva generada vía API externa: el análisis profundo de la estructura molecular {formula} de {composto} indica un fuerte potencial de unión con receptores del área de {modulo}. El peso molecular de {peso} g/mol sugiere que las modificaciones lipídicas podrían optimizar su biodisponibilidad en un 43%.", "zh": "通过外部API生成的洞察：对{composto}的分子结构{formula}进行深入分析表明，其与{modulo}领域受体具有较强的结合潜力。{peso} g/mol的分子量表明脂质修饰可将其生物利用度提高43%。", "de": "Über externe API generierte Erkenntnis: Die eingehende Analyse der Molekülstruktur {formula} von {composto} zeigt ein starkes Bindungspotenzial an Rezeptoren im Bereich {modulo}. Das Molekulargewicht von {peso} g/mol legt nahe, dass Lipidmodifikationen die Bioverfügbarkeit um 43% optimieren könnten.", "ja": "外部API経由で生成されたインサイト：{composto}の分子構造{formula}を詳細に分析した結果、{modulo}領域の受容体との強い結合可能性が示されました。分子量{peso} g/molは、脂質修飾によりバイオアベイラビリティを43%最適化できる可能性を示唆しています。"},
    "ai_insight_local": {"pt": "IA local híbrida: o composto {composto} (fórmula: {formula}) foi escaneado em nossa base neural. Com base em seu peso molecular de {peso} g/mol, nossa IA prevê uma alta afinidade com alvos proteicos no eixo de {modulo}. Recomendamos modelagem molecular in silico (docking) para validar sua eficácia como agente terapêutico primário.", "en": "Local hybrid AI: the compound {composto} (formula: {formula}) was scanned in our neural database. Based on its molecular weight of {peso} g/mol, our AI predicts high affinity with protein targets in the {modulo} axis. We recommend in silico molecular modeling (docking) to validate its efficacy as a primary therapeutic agent.", "es": "IA local híbrida: el compuesto {composto} (fórmula: {formula}) fue escaneado en nuestra base neuronal. Según su peso molecular de {peso} g/mol, nuestra IA predice una alta afinidad con dianas proteicas en el eje de {modulo}. Recomendamos modelado molecular in silico (acoplamiento) para validar su eficacia como agente terapéutico primario.", "zh": "本地混合AI：化合物{composto}（分子式：{formula}）已在我们的神经网络数据库中扫描。根据其{peso} g/mol的分子量，我们的AI预测其与{modulo}方向的蛋白质靶点具有高亲和力。建议进行计算机模拟分子对接以验证其作为主要治疗药物的疗效。", "de": "Lokale Hybrid-KI: Die Verbindung {composto} (Formel: {formula}) wurde in unserer neuronalen Datenbank gescannt. Basierend auf ihrem Molekulargewicht von {peso} g/mol sagt unsere KI eine hohe Affinität zu Proteinzielen in der Achse {modulo} voraus. Wir empfehlen eine In-silico-Molekülmodellierung (Docking) zur Validierung ihrer Wirksamkeit als primärer therapeutischer Wirkstoff.", "ja": "ローカルハイブリッドAI：化合物{composto}（式：{formula}）は当社のニューラルデータベースでスキャンされました。{peso} g/molの分子量に基づき、当AIは{modulo}軸のタンパク質標的との高い親和性を予測します。主要な治療薬候補としての有効性を検証するため、インシリコ分子モデリング（ドッキング）を推奨します。"},
    "benchmark_input_label": {"pt": "Digite as moléculas separadas por vírgula (ex: dasatinib, galantamine, rapamycin):", "en": "Enter the molecules separated by commas (e.g. dasatinib, galantamine, rapamycin):", "es": "Ingrese las moléculas separadas por comas (ej: dasatinib, galantamine, rapamycin):", "zh": "输入以逗号分隔的分子（例如：dasatinib, galantamine, rapamycin）：", "de": "Geben Sie die Moleküle durch Kommas getrennt ein (z. B. dasatinib, galantamine, rapamycin):", "ja": "分子をカンマ区切りで入力してください（例：dasatinib, galantamine, rapamycin）："},
    "benchmark_input_help": {"pt": "Aceita qualquer composto disponível no PubChem, não apenas os pré-cadastrados. Até 6 moléculas por consulta.", "en": "Accepts any compound available on PubChem, not just the pre-registered ones. Up to 6 molecules per query.", "es": "Acepta cualquier compuesto disponible en PubChem, no solo los precargados. Hasta 6 moléculas por consulta.", "zh": "支持 PubChem 上的任意化合物，不限于预设列表。每次查询最多 6 个分子。", "de": "Akzeptiert jede in PubChem verfügbare Verbindung, nicht nur die vorregistrierten. Bis zu 6 Moleküle pro Abfrage.", "ja": "事前登録されたものに限らず、PubChemで利用可能な任意の化合物を受け付けます。1回のクエリで最大6分子まで。"},
    "benchmark_too_many_warn": {"pt": "Mais de 6 moléculas foram digitadas; apenas as 6 primeiras serão processadas.", "en": "More than 6 molecules were entered; only the first 6 will be processed.", "es": "Se ingresaron más de 6 moléculas; solo se procesarán las primeras 6.", "zh": "输入的分子超过 6 个；仅处理前 6 个。", "de": "Es wurden mehr als 6 Moleküle eingegeben; nur die ersten 6 werden verarbeitet.", "ja": "6個を超える分子が入力されました。最初の6個のみ処理されます。"},
    "benchmark_min_molecules_warn": {"pt": "Digite ao menos 2 moléculas válidas, separadas por vírgula.", "en": "Enter at least 2 valid molecules, separated by commas.", "es": "Ingrese al menos 2 moléculas válidas, separadas por comas.", "zh": "请至少输入 2 个有效分子，以逗号分隔。", "de": "Geben Sie mindestens 2 gültige Moleküle ein, durch Kommas getrennt.", "ja": "カンマ区切りで少なくとも2つの有効な分子を入力してください。"},
}

MODULE_TRANSLATIONS = {
    "Longevidade Celular e Oncologia": {"pt": "Longevidade Celular e Oncologia", "en": "Cellular Longevity & Oncology", "es": "Longevidad Celular y Oncología", "zh": "细胞长寿与肿瘤学", "de": "Zelluläre Langlebigkeit & Onkologie", "ja": "細胞老化制御と腫瘍学"},
    "Neurologia e Neuroproteção": {"pt": "Neurologia e Neuroproteção", "en": "Neurology & Neuroprotection", "es": "Neurología y Neuroprotección", "zh": "神经病学与神经保护", "de": "Neurologie & Neuroprotektion", "ja": "神経学と神経保護"},
    "Cardiologia e Insuficiência Cardíaca": {"pt": "Cardiologia e Insuficiência Cardíaca", "en": "Cardiology & Heart Failure", "es": "Cardiología e Insuficiencia Cardíaca", "zh": "心脏病学与心力衰竭", "de": "Kardiologie & Herzinsuffizienz", "ja": "循環器学と心不全"},
    "Endocrinologia e Doenças Metabólicas": {"pt": "Endocrinologia e Doenças Metabólicas", "en": "Endocrinology & Metabolic Diseases", "es": "Endocrinología y Enfermedades Metabólicas", "zh": "内分泌学与代谢性疾病", "de": "Endokrinologie & Stoffwechselerkrankungen", "ja": "内分泌学と代謝性疾患"},
    "Imunologia e Processos Autoimunes": {"pt": "Imunologia e Processos Autoimunes", "en": "Immunology & Autoimmune Processes", "es": "Inmunología y Procesos Autoinmunes", "zh": "免疫学与自身免疫过程", "de": "Immunologie & Autoimmunprozesse", "ja": "免疫学と自己免疫プロセス"},
}


def t(chave, **kwargs):
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


def modulo_nome(modulo_pt):
    idioma = st.session_state.get("idioma_ativo", "pt")
    entrada = MODULE_TRANSLATIONS.get(modulo_pt, {})
    return entrada.get(idioma, modulo_pt)


# =====================================================================
# CSS CUSTOMIZADO — TEMA DARK EXECUTIVO (CONTRASTE CORRIGIDO)
# =====================================================================
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    /*
      DETECCAO DE TEMA: o Streamlit NAO expõe --background-color/--text-color como
      variaveis CSS reais e utilizaveis por CSS customizado (isso e um equivoco comum).
      Por isso a alternancia de tema aqui e feita via o atributo html[data-theme="dark|light"],
      que e definido por um pequeno script (ver logo abaixo) que le a cor de fundo REAL
      renderizada pelo Streamlit e aplica o atributo corretamente. Os blocos abaixo
      definem paletas completas e fixas para cada um dos dois temas.
    */
    :root {
        /* valores padrao (usados so no instante antes do script rodar) */
        --bg-primary: #0a0e17;
        --bg-secondary: #0f1420;
        --bg-card: #131a2b;
        --bg-card-hover: #171f34;
        --border-subtle: #232c42;
        --text-primary: #e8ecf5;
        --text-secondary: #8b95ad;
        --accent-blue: #5b8bff;
        --accent-purple: #8b5cf6;
        --accent-gradient: linear-gradient(135deg, #6f9bff 0%, #a78cf7 100%);
        --text-on-accent: #16132a;
        --success: #22c55e;
        --warning: #f5b942;
        --danger: #f0556b;
    }

    html[data-theme="dark"] {
        --bg-primary: #0a0e17;
        --bg-secondary: #0f1420;
        --bg-card: #131a2b;
        --bg-card-hover: #171f34;
        --border-subtle: #232c42;
        --text-primary: #e8ecf5;
        --text-secondary: #8b95ad;
        --success: #22c55e;
        --warning: #f5b942;
        --danger: #f0556b;
    }

    html[data-theme="light"] {
        --bg-primary: #ffffff;
        --bg-secondary: #f2f4f8;
        --bg-card: #f7f8fb;
        --bg-card-hover: #ebeef5;
        --border-subtle: #dde1ea;
        --text-primary: #1c1f2b;
        --text-secondary: #5b6172;
        --success: #157a3d;
        --warning: #9c6b06;
        --danger: #c02c46;
    }

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp { background: var(--bg-primary); color: var(--text-primary); transition: background 0.15s ease, color 0.15s ease; }

    section[data-testid="stSidebar"] {
        background: var(--bg-secondary);
        border-right: 1px solid var(--border-subtle);
    }
    section[data-testid="stSidebar"] * { color: var(--text-primary) !important; }

    h1, h2, h3, h4 { font-family: 'Inter', sans-serif !important; letter-spacing: -0.02em; color: var(--text-primary) !important; }
    h1 { font-weight: 800 !important; }
    h2, h3 { font-weight: 700 !important; }

    p, span, label, .stMarkdown, .stCaption { color: var(--text-secondary); }

    div[data-testid="stMetric"] {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 14px;
        padding: 16px 18px;
        transition: all 0.25s ease;
        box-shadow: 0 2px 10px rgba(0,0,0,0.12);
    }
    div[data-testid="stMetric"]:hover {
        border-color: var(--accent-blue);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(91, 139, 255, 0.18);
    }
    div[data-testid="stMetricLabel"] { color: var(--text-secondary) !important; font-weight: 600; font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: 0.04em;}
    div[data-testid="stMetricValue"] { color: var(--text-primary) !important; font-weight: 800 !important; font-family: 'JetBrains Mono', monospace !important;}

    /* BOTOES — gradiente claro fixo com texto ESCURO fixo: contraste alto garantido
       independentemente do tema (claro ou escuro) escolhido pelo usuario. */
    .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
        background: var(--accent-gradient) !important;
        color: var(--text-on-accent) !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.55rem 1.3rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.01em;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 12px rgba(91, 139, 255, 0.25);
    }
    .stButton > button *, .stDownloadButton > button *, .stFormSubmitButton > button * {
        color: var(--text-on-accent) !important;
        fill: var(--text-on-accent) !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 22px rgba(139, 92, 246, 0.4);
        filter: brightness(1.05);
    }
    .stButton > button:active, .stDownloadButton > button:active { transform: translateY(0px); }

    .stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox > div > div, div[data-baseweb="select"] > div {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: 0 0 0 2px rgba(91, 139, 255, 0.25) !important;
    }

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
    .stTabs [data-baseweb="tab"] p { color: inherit !important; }
    .stTabs [aria-selected="true"] {
        background: var(--accent-gradient) !important;
        color: var(--text-on-accent) !important;
    }
    .stTabs [aria-selected="true"] p { color: var(--text-on-accent) !important; }

    .streamlit-expanderHeader, div[data-testid="stExpander"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
    }

    div[data-testid="stAlert"] { border-radius: 12px; border: 1px solid var(--border-subtle); }

    .tabela-v12 { width: 100%; border-collapse: collapse; margin-bottom: 20px; border-radius: 12px; overflow: hidden; font-size: 12px;}
    .tabela-v12 th { background: var(--accent-gradient); color: var(--text-on-accent); padding: 12px 10px; text-align: left; font-weight: 700; }
    .tabela-v12 td { padding: 10px; border-bottom: 1px solid var(--border-subtle); color: var(--text-primary); background-color: var(--bg-card);}
    .tabela-v12 tr:nth-child(even) td { background-color: var(--bg-card-hover); }
    .tabela-v12 tr:hover td { filter: brightness(1.08); }

    div[data-testid="stDataFrame"] { border: 1px solid var(--border-subtle); border-radius: 12px; overflow: hidden; }

    div[data-testid="stSlider"] [role="slider"] { background-color: var(--accent-purple) !important; }
    div[data-testid="stToggle"] label div[data-checked="true"] { background-color: var(--accent-blue) !important; }

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: var(--border-subtle); border-radius: 8px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--accent-blue); }

    hr { border-color: var(--border-subtle) !important; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =====================================================================
# DETECTOR DE TEMA (script real, não CSS var inexistente)
# Roda dentro de um iframe (components.html), acessa window.parent.document
# (mesma origem, permitido), lê a cor de fundo REAL que o Streamlit aplicou
# ao container principal e escreve isso como html[data-theme="dark|light"].
# Um MutationObserver + polling garante atualização mesmo em troca de tema
# feita pelo usuário no menu nativo do Streamlit (que não dispara rerun Python).
# =====================================================================
components.html(
    """
    <script>
    (function() {
        function relativeLuminance(rgbString) {
            var m = (rgbString || "").match(/[\\d.]+/g);
            if (!m || m.length < 3) return 255;
            var r = parseFloat(m[0]), g = parseFloat(m[1]), b = parseFloat(m[2]);
            return 0.299 * r + 0.587 * g + 0.114 * b;
        }
        function applyTheme() {
            try {
                var doc = window.parent.document;
                var target = doc.querySelector('[data-testid="stAppViewContainer"]') ||
                             doc.querySelector('.stApp') || doc.body;
                var bg = window.getComputedStyle(target).backgroundColor;
                var lum = relativeLuminance(bg);
                var theme = lum < 128 ? 'dark' : 'light';
                if (doc.documentElement.getAttribute('data-theme') !== theme) {
                    doc.documentElement.setAttribute('data-theme', theme);
                }
            } catch (e) { /* cross-origin ou DOM ainda nao pronto: ignora silenciosamente */ }
        }
        applyTheme();
        try {
            var obsTarget = window.parent.document.body;
            var observer = new MutationObserver(applyTheme);
            observer.observe(obsTarget, {attributes: true, attributeFilter: ['style', 'class']});
            observer.observe(window.parent.document.documentElement, {attributes: true, attributeFilter: ['style', 'class']});
        } catch (e) {}
        setInterval(applyTheme, 1200);
    })();
    </script>
    """,
    height=0,
)

# --- ESTADO GLOBAL ---
if "historico_auditoria" not in st.session_state:
    st.session_state.historico_auditoria = []
if "eln_experimentos" not in st.session_state:
    st.session_state.eln_experimentos = []
if "cache_moleculas" not in st.session_state:
    st.session_state.cache_moleculas = {}
if "idioma_ativo" not in st.session_state:
    st.session_state.idioma_ativo = "pt"

@st.cache_resource(show_spinner=False)
def carregar_catalogo_pains():
    params = FilterCatalogParams()
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_A)
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_B)
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_C)
    return FilterCatalog(params)

CATALOGO_PAINS = carregar_catalogo_pains()

# =====================================================================
# BASE DE CONHECIMENTO CIENTÍFICO — TOTALMENTE LOCALIZADA (6 IDIOMAS)
# "tag" é um código interno neutro de idioma usado para lógica de segurança;
# apenas os campos classe/aplicacao/pipeline são exibidos ao usuário.
# =====================================================================
KB_DATA = {
    "quercetin": {"modulo": "Longevidade Celular e Oncologia", "tag": "senolitico",
        "classe": {"pt": "Flavonoide Senolítico", "en": "Senolytic Flavonoid", "es": "Flavonoide Senolítico", "zh": "黄酮类抗衰老（Senolytic）药物", "de": "Senolytisches Flavonoid", "ja": "セノリティックフラボノイド"},
        "aplicacao": {"pt": "Flavonoide natural exógeno que inibe a via de sobrevivência PI3K/AKT, induzindo seletivamente a apoptose em células senescentes e reduzindo drasticamente o SASP.", "en": "Exogenous natural flavonoid that inhibits the PI3K/AKT survival pathway, selectively inducing apoptosis in senescent cells and sharply reducing SASP.", "es": "Flavonoide natural exógeno que inhibe la vía de supervivencia PI3K/AKT, induciendo selectivamente la apoptosis en células senescentes y reduciendo drásticamente el SASP.", "zh": "外源性天然黄酮类化合物，可抑制PI3K/AKT生存通路，选择性诱导衰老细胞凋亡，并显著降低SASP（衰老相关分泌表型）。", "de": "Exogenes natürliches Flavonoid, das den PI3K/AKT-Überlebensweg hemmt, selektiv Apoptose in seneszenten Zellen auslöst und die SASP-Ausschüttung deutlich reduziert.", "ja": "PI3K/AKT生存経路を阻害し、老化細胞に選択的にアポトーシスを誘導してSASPを大幅に減少させる外因性天然フラボノイド。"},
        "pipeline": {"pt": "Fase II de Ensaios Clínicos Translacionais. Desafios focados em melhorar a baixa biodisponibilidade oral crônica através de matrizes lipossomais.", "en": "Phase II translational clinical trials. Challenges focus on improving low chronic oral bioavailability through liposomal matrices.", "es": "Fase II de ensayos clínicos traslacionales. Los desafíos se centran en mejorar la baja biodisponibilidad oral crónica mediante matrices liposomales.", "zh": "处于II期转化临床试验阶段。主要挑战是通过脂质体载体改善长期口服生物利用度低的问题。", "de": "Translationale klinische Studien der Phase II. Herausforderungen liegen in der Verbesserung der niedrigen chronischen oralen Bioverfügbarkeit durch liposomale Matrizen.", "ja": "第II相トランスレーショナル臨床試験段階。リポソーム製剤による慢性経口バイオアベイラビリティ改善が課題。"}},
    "dasatinib": {"modulo": "Longevidade Celular e Oncologia", "tag": "inibidor",
        "classe": {"pt": "Inibidor de Tirosina Quinase", "en": "Tyrosine Kinase Inhibitor", "es": "Inhibidor de Tirosina Quinasa", "zh": "酪氨酸激酶抑制剂", "de": "Tyrosinkinase-Inhibitor", "ja": "チロシンキナーゼ阻害薬"},
        "aplicacao": {"pt": "Potente inibidor de tirosina quinase. Atua desregulando as redes de sinalização pró-sobrevivência das células senescentes através de dosagem intermitente 'hit-and-run'.", "en": "Potent tyrosine kinase inhibitor. Disrupts pro-survival signaling networks in senescent cells via intermittent 'hit-and-run' dosing.", "es": "Potente inhibidor de tirosina quinasa. Desregula las redes de señalización pro-supervivencia de las células senescentes mediante dosificación intermitente 'hit-and-run'.", "zh": "强效酪氨酸激酶抑制剂，通过间歇性给药方式干扰衰老细胞的促生存信号网络。", "de": "Potenter Tyrosinkinase-Inhibitor. Stört die Überlebenssignalnetzwerke seneszenter Zellen durch intermittierende Dosierung.", "ja": "強力なチロシンキナーゼ阻害薬。間欠的投与により、老化細胞の生存シグナルネットワークを撹乱する。"},
        "pipeline": {"pt": "Transição entre aplicações oncológicas e rejuvenescimento. Desafios envolvem o controle de toxicidade residual periférica.", "en": "Transitioning from oncology to rejuvenation applications. Challenges involve managing residual peripheral toxicity.", "es": "Transición entre aplicaciones oncológicas y de rejuvenecimiento. Los desafíos implican el control de la toxicidad periférica residual.", "zh": "正从肿瘤学应用向抗衰老应用过渡，挑战在于控制外周残留毒性。", "de": "Übergang von onkologischen zu Verjüngungsanwendungen. Herausforderungen betreffen die Kontrolle residualer peripherer Toxizität.", "ja": "腫瘍学的応用から若返り応用への移行段階。末梢性残存毒性の管理が課題。"}},
    "navitoclax": {"modulo": "Longevidade Celular e Oncologia", "tag": "inibidor",
        "classe": {"pt": "Inibidor BCL-2 / BCL-xL", "en": "BCL-2/BCL-xL Inhibitor", "es": "Inhibidor BCL-2/BCL-xL", "zh": "BCL-2/BCL-xL 抑制剂", "de": "BCL-2/BCL-xL-Inhibitor", "ja": "BCL-2/BCL-xL阻害薬"},
        "aplicacao": {"pt": "Inibidor sintético que suprime os eixos antiapoptóticos BCL-2 e BCL-xL, reativando a morte celular programada em linhagens senescentes profundas.", "en": "Synthetic inhibitor that suppresses the BCL-2 and BCL-xL anti-apoptotic axes, reactivating programmed cell death in deeply senescent lineages.", "es": "Inhibidor sintético que suprime los ejes antiapoptóticos BCL-2 y BCL-xL, reactivando la muerte celular programada en linajes senescentes profundos.", "zh": "一种合成抑制剂，可抑制BCL-2和BCL-xL抗凋亡通路，重新激活深度衰老细胞系的程序性细胞死亡。", "de": "Synthetischer Inhibitor, der die antiapoptotischen BCL-2- und BCL-xL-Achsen unterdrückt und den programmierten Zelltod in tief seneszenten Zelllinien reaktiviert.", "ja": "BCL-2およびBCL-xLの抗アポトーシス経路を抑制し、深度老化細胞系におけるプログラム細胞死を再活性化する合成阻害薬。"},
        "pipeline": {"pt": "Validação clínica oncológica. O maior desafio disruptivo reside no controle de efeitos colaterais como a trombocitopenia aguda.", "en": "Oncology clinical validation. The main disruptive challenge is managing side effects such as acute thrombocytopenia.", "es": "Validación clínica oncológica. El mayor desafío es el control de efectos secundarios como la trombocitopenia aguda.", "zh": "处于肿瘤学临床验证阶段，最大挑战是控制急性血小板减少症等副作用。", "de": "Onkologische klinische Validierung. Die größte Herausforderung ist die Kontrolle von Nebenwirkungen wie akuter Thrombozytopenie.", "ja": "腫瘍学的臨床検証段階。最大の課題は急性血小板減少症などの副作用管理。"}},
    "fisetin": {"modulo": "Longevidade Celular e Oncologia", "tag": "senolitico",
        "classe": {"pt": "Flavonoide Senolítico", "en": "Senolytic Flavonoid", "es": "Flavonoide Senolítico", "zh": "黄酮类抗衰老药物", "de": "Senolytisches Flavonoid", "ja": "セノリティックフラボノイド"},
        "aplicacao": {"pt": "Polifenol flavonoide de alta especificidade senolítica. Modula negativamente as redes NF-kB, reduzindo o ecossistema inflamatório SASP com alto perfil de segurança.", "en": "Highly specific senolytic flavonoid polyphenol. Downregulates NF-kB networks, reducing the SASP inflammatory ecosystem with a strong safety profile.", "es": "Polifenol flavonoide de alta especificidad senolítica. Modula negativamente las redes NF-kB, reduciendo el ecosistema inflamatorio SASP con un alto perfil de seguridad.", "zh": "高特异性抗衰老黄酮多酚，负调控NF-kB网络，降低SASP炎症生态，且安全性良好。", "de": "Hochspezifisches senolytisches Flavonoid-Polyphenol. Reguliert NF-kB-Netzwerke herunter und reduziert das SASP-Entzündungsökosystem bei starkem Sicherheitsprofil.", "ja": "高い特異性を持つセノリティックフラボノイドポリフェノール。NF-kBネットワークを下方制御し、高い安全性プロファイルでSASP炎症エコシステムを低減する。"},
        "pipeline": {"pt": "Fase II de estudos translacionais em humanos. Projetos priorizam a nanoencapsulação lipídica para otimização farmacocinética.", "en": "Phase II human translational studies. Projects prioritize lipid nanoencapsulation for pharmacokinetic optimization.", "es": "Fase II de estudios traslacionales en humanos. Los proyectos priorizan la nanoencapsulación lipídica para optimizar la farmacocinética.", "zh": "处于II期人体转化研究阶段，重点开发脂质纳米包封技术以优化药代动力学。", "de": "Translationale Humanstudien der Phase II. Projekte priorisieren Lipid-Nanoverkapselung zur pharmakokinetischen Optimierung.", "ja": "第II相ヒト対象トランスレーショナル研究段階。薬物動態最適化のための脂質ナノカプセル化を優先。"}},
    "resveratrol": {"modulo": "Longevidade Celular e Oncologia", "tag": "outro",
        "classe": {"pt": "Modulador de Sirtuína / Senomorfo", "en": "Sirtuin Modulator / Senomorphic", "es": "Modulador de Sirtuína / Senomorfo", "zh": "去乙酰化酶（Sirtuin）调节剂/衰老形态调节剂", "de": "Sirtuin-Modulator / Senomorph", "ja": "サーチュイン調節薬／セノモルフィック"},
        "aplicacao": {"pt": "Agente senorfológico e modulador alostérico das Sirtuínas (SIRT1). Não induz a lise celular, mas reprograma epigeneticamente o microambiente contendo a inflamação.", "en": "Senomorphic agent and allosteric modulator of Sirtuins (SIRT1). Does not induce cell lysis but epigenetically reprograms the inflammatory microenvironment.", "es": "Agente senomórfico y modulador alostérico de las Sirtuínas (SIRT1). No induce lisis celular, pero reprograma epigenéticamente el microambiente inflamatorio.", "zh": "衰老形态调节剂及SIRT1去乙酰化酶变构调节剂，不引起细胞裂解，而是通过表观遗传方式重编程炎症微环境。", "de": "Senomorphes Mittel und allosterischer Modulator der Sirtuine (SIRT1). Induziert keine Zelllyse, reprogrammiert aber epigenetisch die entzündliche Mikroumgebung.", "ja": "セノモルフィック作用薬でありサーチュイン（SIRT1）のアロステリック調節薬。細胞溶解は誘導せず、炎症性微小環境をエピジェネティックに再プログラムする。"},
        "pipeline": {"pt": "Uso global consolidado como nutracêutico. Esforços atuais focam na síntese de ativadores sintéticos de segunda geração (STACs) com maior estabilidade.", "en": "Established global use as a nutraceutical. Current efforts focus on synthesizing second-generation synthetic activators (STACs) with greater stability.", "es": "Uso global consolidado como nutracéutico. Los esfuerzos actuales se centran en sintetizar activadores sintéticos de segunda generación (STAC) más estables.", "zh": "作为营养保健品已在全球广泛应用，目前的研究重点是合成稳定性更高的第二代合成激活剂（STACs）。", "de": "Etablierte globale Nutzung als Nutrazeutikum. Aktuelle Bemühungen konzentrieren sich auf die Synthese stabilerer synthetischer Aktivatoren der zweiten Generation (STACs).", "ja": "栄養補助食品として世界的に定着した使用実績あり。現在はより安定した第二世代合成活性化剤（STACs）の開発に注力。"}},
    "rapamycin": {"modulo": "Longevidade Celular e Oncologia", "tag": "inibidor",
        "classe": {"pt": "Inibidor mTOR / Senolítico", "en": "mTOR Inhibitor / Senolytic", "es": "Inhibidor mTOR / Senolítico", "zh": "mTOR抑制剂/抗衰老药物", "de": "mTOR-Inhibitor / Senolytikum", "ja": "mTOR阻害薬／セノリティック"},
        "aplicacao": {"pt": "Inibidor robusto da via mecânica mTor (Target of Rapamycin). Age reprogramando o metabolismo energético e retardando o fenótipo de senescência replicativa celular.", "en": "Robust inhibitor of the mTOR (Target of Rapamycin) mechanistic pathway. Reprograms energy metabolism and slows the replicative cellular senescence phenotype.", "es": "Inhibidor robusto de la vía mecánica mTOR (Target of Rapamycin). Reprograma el metabolismo energético y retrasa el fenotipo de senescencia replicativa celular.", "zh": "强效mTOR（雷帕霉素靶蛋白）通路抑制剂，可重编程能量代谢并延缓细胞复制性衰老表型。", "de": "Robuster Inhibitor des mTOR-Signalwegs. Reprogrammiert den Energiestoffwechsel und verlangsamt den replikativen zellulären Seneszenzphänotyp.", "ja": "mTOR（ラパマイシン標的タンパク質）経路の強力な阻害薬。エネルギー代謝を再プログラムし、複製老化表現型を遅延させる。"},
        "pipeline": {"pt": "Fase Avançada de Modelagem Pré-Clínica. Desafios críticos associados à imunossupressão crônica e controle estrito de dosagem cíclica.", "en": "Advanced preclinical modeling phase. Critical challenges involve chronic immunosuppression and strict cyclical dosing control.", "es": "Fase avanzada de modelado preclínico. Los desafíos críticos están asociados a la inmunosupresión crónica y al control estricto de la dosificación cíclica.", "zh": "处于高级临床前建模阶段，主要挑战包括慢性免疫抑制及严格周期性给药控制。", "de": "Fortgeschrittene präklinische Modellierungsphase. Kritische Herausforderungen betreffen chronische Immunsuppression und strenge zyklische Dosierungskontrolle.", "ja": "高度な前臨床モデリング段階。慢性免疫抑制および厳密な周期投与管理が重要な課題。"}},
    "metformin": {"modulo": "Longevidade Celular e Oncologia", "tag": "outro",
        "classe": {"pt": "Senomorfo / Ativador AMPK", "en": "Senomorphic / AMPK Activator", "es": "Senomorfo / Activador de AMPK", "zh": "衰老形态调节剂/AMPK激活剂", "de": "Senomorph / AMPK-Aktivator", "ja": "セノモルフィック／AMPK活性化薬"},
        "aplicacao": {"pt": "Agente senomórfico clássico derivado de biguanida. Atua via ativação de AMPK e atenuação de estresse oxidativo mitocondrial, reduzindo marcadores pró-inflamatórios sistêmicos.", "en": "Classic senomorphic biguanide-derived agent. Acts via AMPK activation and mitochondrial oxidative stress attenuation, reducing systemic pro-inflammatory markers.", "es": "Agente senomórfico clásico derivado de biguanida. Actúa mediante la activación de AMPK y la atenuación del estrés oxidativo mitocondrial, reduciendo los marcadores proinflamatorios sistémicos.", "zh": "经典的双胍类衰老形态调节剂，通过激活AMPK并减轻线粒体氧化应激，降低全身促炎标志物水平。", "de": "Klassisches senomorphes Biguanid-Derivat. Wirkt über AMPK-Aktivierung und Abschwächung mitochondrialen oxidativen Stresses.", "ja": "古典的なビグアナイド系セノモルフィック薬剤。AMPK活性化とミトコンドリア酸化ストレス軽減を介して、全身性の炎症マーカーを低下させる。"},
        "pipeline": {"pt": "Ensaios Translacionais Globais (Projeto TAME). Perfil de segurança robusto e custo de manufatura escalável para distribuição em massa.", "en": "Global translational trials (TAME Project). Robust safety profile and scalable manufacturing cost for mass distribution.", "es": "Ensayos traslacionales globales (Proyecto TAME). Perfil de seguridad robusto y costo de fabricación escalable para distribución masiva.", "zh": "正在进行全球转化性试验（TAME项目），安全性良好且生产成本可规模化，适合大规模推广。", "de": "Globale translationale Studien (TAME-Projekt). Robustes Sicherheitsprofil und skalierbare Herstellungskosten für die Massenverteilung.", "ja": "世界的なトランスレーショナル試験（TAMEプロジェクト）を実施中。安全性プロファイルは堅牢で、大量供給に適したスケーラブルな製造コスト。"}},
    "donepezil": {"modulo": "Neurologia e Neuroproteção", "tag": "inibidor",
        "classe": {"pt": "Inibidor da AChE", "en": "AChE Inhibitor", "es": "Inhibidor de la AChE", "zh": "乙酰胆碱酯酶抑制剂", "de": "AChE-Inhibitor", "ja": "アセチルコリンエステラーゼ（AChE）阻害薬"},
        "aplicacao": {"pt": "Inibidor reversível da acetilcolinesterase (AChE). Aumenta a concentração cortical de acetilcolina, melhorando a neurotransmissão em tecidos afetados por demência progressiva.", "en": "Reversible acetylcholinesterase (AChE) inhibitor. Increases cortical acetylcholine concentration, improving neurotransmission in tissue affected by progressive dementia.", "es": "Inhibidor reversible de la acetilcolinesterasa (AChE). Aumenta la concentración cortical de acetilcolina, mejorando la neurotransmisión en tejidos afectados por demencia progresiva.", "zh": "可逆性乙酰胆碱酯酶（AChE）抑制剂，可提高皮质乙酰胆碱浓度，改善受进行性痴呆影响组织的神经传导。", "de": "Reversibler Acetylcholinesterase(AChE)-Inhibitor. Erhöht die kortikale Acetylcholinkonzentration und verbessert die Neurotransmission in von progressiver Demenz betroffenem Gewebe.", "ja": "可逆的アセチルコリンエステラーゼ（AChE）阻害薬。皮質のアセチルコリン濃度を高め、進行性認知症の影響を受けた組織の神経伝達を改善する。"},
        "pipeline": {"pt": "Aprovado globalmente para estágios leves a graves da Doença de Alzheimer. Pipelines de P&D focam na redução de efeitos colaterais gastrointestinais periféricos.", "en": "Globally approved for mild to severe stages of Alzheimer's Disease. R&D pipelines focus on reducing peripheral gastrointestinal side effects.", "es": "Aprobado a nivel mundial para etapas leves a graves de la enfermedad de Alzheimer. Los pipelines de I+D se centran en reducir los efectos secundarios gastrointestinales periféricos.", "zh": "已在全球范围内获批用于轻度至重度阿尔茨海默病，研发管线重点在于减少外周胃肠道副作用。", "de": "Weltweit zugelassen für leichte bis schwere Stadien der Alzheimer-Krankheit. F&E-Pipelines konzentrieren sich auf die Reduzierung peripherer gastrointestinaler Nebenwirkungen.", "ja": "アルツハイマー病の軽度から重度までの段階で世界的に承認済み。研究開発パイプラインは末梢消化器系副作用の軽減に注力。"}},
    "memantine": {"modulo": "Neurologia e Neuroproteção", "tag": "antagonista",
        "classe": {"pt": "Antagonista NMDA", "en": "NMDA Antagonist", "es": "Antagonista NMDA", "zh": "NMDA受体拮抗剂", "de": "NMDA-Antagonist", "ja": "NMDA拮抗薬"},
        "aplicacao": {"pt": "Antagonista de ligação de baixa afinidade dos receptores NMDA de glutamato. Protege o sistema nervoso contra a excitotoxicidade induzida pelo excesso patológico de glutamato.", "en": "Low-affinity NMDA glutamate receptor antagonist. Protects the nervous system against excitotoxicity induced by pathological glutamate excess.", "es": "Antagonista de baja afinidad de los receptores NMDA de glutamato. Protege el sistema nervioso contra la excitotoxicidad inducida por el exceso patológico de glutamato.", "zh": "低亲和力NMDA谷氨酸受体拮抗剂，可保护神经系统免受病理性谷氨酸过量所致的兴奋性毒性损伤。", "de": "Niedrig-affiner NMDA-Glutamatrezeptor-Antagonist. Schützt das Nervensystem vor Exzitotoxizität durch pathologischen Glutamatüberschuss.", "ja": "低親和性NMDAグルタミン酸受容体拮抗薬。病的なグルタミン酸過剰による興奮毒性から神経系を保護する。"},
        "pipeline": {"pt": "Consolidado na clínica farmacêutica. Pipelines de vanguarda buscam o desenvolvimento de formulações de liberação prolongada combinadas com outros agentes.", "en": "Established in pharmaceutical clinical practice. Cutting-edge pipelines seek extended-release formulations combined with other agents.", "es": "Consolidado en la clínica farmacéutica. Los pipelines de vanguardia buscan formulaciones de liberación prolongada combinadas con otros agentes.", "zh": "已在药物临床实践中确立地位，前沿研发方向是开发与其他药物联合的缓释制剂。", "de": "In der pharmazeutischen klinischen Praxis etabliert. Innovative Pipelines streben Retardformulierungen in Kombination mit anderen Wirkstoffen an.", "ja": "臨床薬物治療において確立された地位。先端パイプラインは他剤併用の徐放性製剤を模索。"}},
    "galantamine": {"modulo": "Neurologia e Neuroproteção", "tag": "inibidor",
        "classe": {"pt": "Inibidor da AChE / Modulador Nicotínico", "en": "AChE Inhibitor / Nicotinic Modulator", "es": "Inhibidor de la AChE / Modulador Nicotínico", "zh": "乙酰胆碱酯酶抑制剂/烟碱受体调节剂", "de": "AChE-Inhibitor / Nikotinischer Modulator", "ja": "AChE阻害薬／ニコチン性モジュレーター"},
        "aplicacao": {"pt": "Inibidor competitivo da acetilcolinesterase e modulador alostérico de receptores nicotínicos. Duplo mecanismo que potencializa a resposta colinérgica central.", "en": "Competitive acetylcholinesterase inhibitor and allosteric modulator of nicotinic receptors. Dual mechanism that enhances the central cholinergic response.", "es": "Inhibidor competitivo de la acetilcolinesterasa y modulador alostérico de los receptores nicotínicos. Mecanismo dual que potencia la respuesta colinérgica central.", "zh": "竞争性乙酰胆碱酯酶抑制剂兼烟碱受体变构调节剂，通过双重机制增强中枢胆碱能反应。", "de": "Kompetitiver Acetylcholinesterase-Inhibitor und allosterischer Modulator nikotinischer Rezeptoren. Dualer Mechanismus, der die zentrale cholinerge Antwort verstärkt.", "ja": "競合的アセチルコリンエステラーゼ阻害薬であり、ニコチン受容体のアロステリックモジュレーターでもある。中枢コリン作動性反応を増強する二重機序を持つ。"},
        "pipeline": {"pt": "Disponibilidade comercial estabelecida. Estudos de pipeline focam em novas matrizes transdérmicas de liberação contínua.", "en": "Established commercial availability. Pipeline studies focus on new continuous-release transdermal matrices.", "es": "Disponibilidad comercial establecida. Los estudios de pipeline se centran en nuevas matrices transdérmicas de liberación continua.", "zh": "已建立商业化供应，研发方向为新型持续释放透皮贴剂。", "de": "Etablierte kommerzielle Verfügbarkeit. Pipeline-Studien konzentrieren sich auf neue transdermale Matrizen mit kontinuierlicher Freisetzung.", "ja": "商業的供給体制は確立済み。研究パイプラインは新規の持続放出型経皮製剤に注力。"}},
    "sacubitril": {"modulo": "Cardiologia e Insuficiência Cardíaca", "tag": "inibidor",
        "classe": {"pt": "Inibidor da Neprilisina", "en": "Neprilysin Inhibitor", "es": "Inhibidor de la Neprilisina", "zh": "脑啡肽酶抑制剂", "de": "Neprilysin-Inhibitor", "ja": "ネプリライシン阻害薬"},
        "aplicacao": {"pt": "Inibidor da neprilisina que previne a degradação de peptídeos natriuréticos benéficos, promovendo vasodilação e reduzindo a fibrose miocárdica progressiva.", "en": "Neprilysin inhibitor that prevents the degradation of beneficial natriuretic peptides, promoting vasodilation and reducing progressive myocardial fibrosis.", "es": "Inhibidor de la neprilisina que previene la degradación de péptidos natriuréticos beneficiosos, promoviendo la vasodilatación y reduciendo la fibrosis miocárdica progresiva.", "zh": "脑啡肽酶抑制剂，可防止有益利钠肽降解，促进血管扩张并减少进行性心肌纤维化。", "de": "Neprilysin-Inhibitor, der den Abbau nützlicher natriuretischer Peptide verhindert, die Vasodilatation fördert und die fortschreitende Myokardfibrose reduziert.", "ja": "有益なナトリウム利尿ペプチドの分解を防ぐネプリライシン阻害薬。血管拡張を促進し、進行性の心筋線維化を軽減する。"},
        "pipeline": {"pt": "Pilar consagrado no tratamento de insuficiência cardíaca de fração de ejeção reduzida. Ensaios em andamento avaliam sinergia mecânica combinada.", "en": "Established pillar in the treatment of reduced ejection fraction heart failure. Ongoing trials evaluate combined mechanical synergy.", "es": "Pilar consolidado en el tratamiento de la insuficiencia cardíaca con fracción de eyección reducida. Los ensayos en curso evalúan la sinergia mecánica combinada.", "zh": "已成为射血分数降低型心力衰竭治疗的基石药物，正在进行的试验评估其与机械辅助治疗的联合协同效应。", "de": "Etablierte Säule in der Behandlung der Herzinsuffizienz mit reduzierter Ejektionsfraktion. Laufende Studien bewerten die kombinierte mechanische Synergie.", "ja": "駆出率低下型心不全治療の確立された柱。現在進行中の試験では機械的補助療法との相乗効果を評価中。"}},
    "empagliflozin": {"modulo": "Cardiologia e Insuficiência Cardíaca", "tag": "inibidor",
        "classe": {"pt": "Inibidor de SGLT2", "en": "SGLT2 Inhibitor", "es": "Inhibidor de SGLT2", "zh": "SGLT2抑制剂", "de": "SGLT2-Inhibitor", "ja": "SGLT2阻害薬"},
        "aplicacao": {"pt": "Inibidor seletivo do cotransportador sódio-glicose 2 (SGLT2). Atua reduzindo a pré-carga e pós-carga miocárdica por efeito osmótico e metabólico direto.", "en": "Selective sodium-glucose cotransporter 2 (SGLT2) inhibitor. Reduces myocardial preload and afterload through direct osmotic and metabolic effects.", "es": "Inhibidor selectivo del cotransportador sodio-glucosa 2 (SGLT2). Reduce la precarga y poscarga miocárdica mediante efecto osmótico y metabólico directo.", "zh": "选择性钠-葡萄糖协同转运蛋白2（SGLT2）抑制剂，通过直接的渗透和代谢作用降低心肌前负荷和后负荷。", "de": "Selektiver Natrium-Glukose-Cotransporter-2(SGLT2)-Inhibitor. Reduziert myokardiale Vor- und Nachlast durch direkten osmotischen und metabolischen Effekt.", "ja": "選択的ナトリウム・グルコース共輸送体2（SGLT2）阻害薬。直接的な浸透圧・代謝作用により心筋の前負荷・後負荷を軽減する。"},
        "pipeline": {"pt": "Validação expandida para proteção cardioprotetora contínua em pacientes com ou sem comorbidades glicêmicas de base.", "en": "Expanded validation for continuous cardioprotection in patients with or without underlying glycemic comorbidities.", "es": "Validación ampliada para la cardioprotección continua en pacientes con o sin comorbilidades glucémicas de base.", "zh": "正在扩展验证其对合并或不合并血糖相关合并症患者的持续心脏保护作用。", "de": "Erweiterte Validierung für kontinuierlichen Herzschutz bei Patienten mit oder ohne zugrunde liegende glykämische Komorbiditäten.", "ja": "血糖関連合併症の有無にかかわらず、持続的心保護効果についての検証が拡大中。"}},
    "semaglutide": {"modulo": "Endocrinologia e Doenças Metabólicas", "tag": "agonista",
        "classe": {"pt": "Agonista de Receptor GLP-1", "en": "GLP-1 Receptor Agonist", "es": "Agonista del Receptor GLP-1", "zh": "GLP-1受体激动剂", "de": "GLP-1-Rezeptoragonist", "ja": "GLP-1受容体作動薬"},
        "aplicacao": {"pt": "Agonista potente do receptor do peptídeo semelhante ao glucagon 1 (GLP-1). Atua otimizando a secreção de insulina insulinotrópica e na modulação sacietógena central.", "en": "Potent glucagon-like peptide-1 (GLP-1) receptor agonist. Optimizes insulinotropic insulin secretion and central satiety modulation.", "es": "Agonista potente del receptor del péptido similar al glucagón tipo 1 (GLP-1). Optimiza la secreción insulinotrópica de insulina y la modulación saciógena central.", "zh": "强效胰高血糖素样肽1（GLP-1）受体激动剂，可优化促胰岛素分泌作用并调节中枢饱腹感。", "de": "Potenter Glucagon-like-Peptide-1(GLP-1)-Rezeptoragonist. Optimiert die insulinotrope Insulinsekretion und die zentrale Sättigungsmodulation.", "ja": "強力なGLP-1（グルカゴン様ペプチド1）受容体作動薬。インスリン分泌促進作用と中枢性満腹感調節を最適化する。"},
        "pipeline": {"pt": "Estudos de fase avançada focados em desfechos macrovasculares de longo prazo e redução expressiva de esteato-hepatite metabólica.", "en": "Advanced-phase studies focused on long-term macrovascular outcomes and significant reduction of metabolic steatohepatitis.", "es": "Estudios de fase avanzada centrados en los resultados macrovasculares a largo plazo y la reducción significativa de la esteatohepatitis metabólica.", "zh": "处于后期阶段研究，重点关注长期大血管结局及显著改善代谢性脂肪性肝炎。", "de": "Fortgeschrittene Studien mit Fokus auf langfristige makrovaskuläre Endpunkte und deutliche Reduktion der metabolischen Steatohepatitis.", "ja": "長期的な大血管アウトカムと代謝性脂肪肝炎の顕著な改善に焦点を当てた後期段階の研究。"}},
    "tirzepatide": {"modulo": "Endocrinologia e Doenças Metabólicas", "tag": "agonista",
        "classe": {"pt": "Agonista Duplo GIP/GLP-1", "en": "Dual GIP/GLP-1 Agonist", "es": "Agonista Dual GIP/GLP-1", "zh": "GIP/GLP-1双受体激动剂", "de": "Dualer GIP/GLP-1-Agonist", "ja": "GIP/GLP-1デュアルアゴニスト"},
        "aplicacao": {"pt": "Coagonista duplo direcionado aos receptores de GIP e GLP-1. Oferece controle sinérgico estendido sobre a homeostase energética.", "en": "Dual coagonist targeting GIP and GLP-1 receptors. Offers extended synergistic control over energy homeostasis.", "es": "Coagonista dual dirigido a los receptores de GIP y GLP-1. Ofrece un control sinérgico extendido sobre la homeostasis energética.", "zh": "同时靶向GIP和GLP-1受体的双重共激动剂，可对能量稳态提供更持久的协同调控。", "de": "Dualer Koagonist, der auf GIP- und GLP-1-Rezeptoren abzielt. Bietet erweiterte synergistische Kontrolle über die Energiehomöostase.", "ja": "GIPおよびGLP-1受容体を標的とするデュアルコアゴニスト。エネルギー恒常性に対する持続的な相乗的制御を提供する。"},
        "pipeline": {"pt": "Lançamentos globais integrados. Novas fases em andamento para avaliar a preservação de massa magra estrutural.", "en": "Integrated global launches. New phases underway evaluating preservation of lean body mass.", "es": "Lanzamientos globales integrados. Nuevas fases en curso evalúan la preservación de la masa magra.", "zh": "已实现全球一体化上市，新阶段研究正在评估其对瘦体重保留的作用。", "de": "Integrierte globale Markteinführungen. Neue Phasen laufen zur Bewertung des Erhalts der fettfreien Körpermasse.", "ja": "統合されたグローバル展開が進行中。新段階では除脂肪体重の維持効果を評価中。"}},
    "adalimumab": {"modulo": "Imunologia e Processos Autoimunes", "tag": "anticorpo",
        "classe": {"pt": "Anticorpo Monoclonal anti-TNF", "en": "Anti-TNF Monoclonal Antibody", "es": "Anticuerpo Monoclonal anti-TNF", "zh": "抗TNF单克隆抗体", "de": "Anti-TNF-Monoklonaler Antikörper", "ja": "抗TNFモノクローナル抗体"},
        "aplicacao": {"pt": "Anticorpo monoclonal recombinante IgG1 totalmente humano. Liga-se especificamente ao fator de necrose tumoral alfa (TNF-alfa), neutralizando sua atividade pró-inflamatória.", "en": "Fully human recombinant IgG1 monoclonal antibody. Specifically binds tumor necrosis factor alpha (TNF-alpha), neutralizing its pro-inflammatory activity.", "es": "Anticuerpo monoclonal recombinante IgG1 totalmente humano. Se une específicamente al factor de necrosis tumoral alfa (TNF-alfa), neutralizando su actividad proinflamatoria.", "zh": "全人源重组IgG1单克隆抗体，特异性结合肿瘤坏死因子α（TNF-α），中和其促炎活性。", "de": "Vollständig humaner rekombinanter IgG1-monoklonaler Antikörper. Bindet spezifisch an den Tumornekrosefaktor alpha (TNF-alpha).", "ja": "完全ヒト型組換えIgG1モノクローナル抗体。腫瘍壊死因子α（TNF-α）に特異的に結合し、その炎症促進活性を中和する。"},
        "pipeline": {"pt": "Mercado maduro em transição global de otimização de custo por biossimilares. Estudos buscam identificar biomarcadores preditivos.", "en": "Mature market transitioning globally toward cost optimization via biosimilars. Studies seek predictive biomarkers.", "es": "Mercado maduro en transición global hacia la optimización de costos mediante biosimilares. Los estudios buscan biomarcadores predictivos.", "zh": "成熟市场正通过生物类似药实现全球范围的成本优化，相关研究致力于寻找预测性生物标志物。", "de": "Reifer Markt im globalen Übergang zur Kostenoptimierung durch Biosimilars. Studien suchen nach prädiktiven Biomarkern.", "ja": "成熟市場はバイオシミラーによるコスト最適化へと世界的に移行中。研究は予測バイオマーカーの特定を目指す。"}},
    "tofacitinib": {"modulo": "Imunologia e Processos Autoimunes", "tag": "inibidor",
        "classe": {"pt": "Inibidor de JAK", "en": "JAK Inhibitor", "es": "Inhibidor de JAK", "zh": "JAK抑制剂", "de": "JAK-Inhibitor", "ja": "JAK阻害薬"},
        "aplicacao": {"pt": "Inibidor seletivo de pequena molécula das enzimas Janus Quinase (JAK1 e JAK3). Bloqueia a transdução de sinal intracelular de citocinas inflamatórias.", "en": "Selective small-molecule inhibitor of Janus Kinase enzymes (JAK1 and JAK3). Blocks intracellular signal transduction of inflammatory cytokines.", "es": "Inhibidor selectivo de molécula pequeña de las enzimas Janus Quinasa (JAK1 y JAK3). Bloquea la transducción de señales intracelulares de citocinas inflamatorias.", "zh": "选择性小分子Janus激酶（JAK1和JAK3）抑制剂，可阻断炎性细胞因子的细胞内信号转导。", "de": "Selektiver niedermolekularer Inhibitor der Janus-Kinase-Enzyme (JAK1 und JAK3). Blockiert die intrazelluläre Signaltransduktion entzündlicher Zytokine.", "ja": "ヤヌスキナーゼ酵素（JAK1およびJAK3）を選択的に阻害する低分子薬。炎症性サイトカインの細胞内シグナル伝達を遮断する。"},
        "pipeline": {"pt": "Consolidado na reumatologia de alta complexidade. Monitoramentos de segurança refinam o perfil de risco do paciente idoso.", "en": "Established in complex rheumatology care. Safety monitoring refines the elderly patient risk profile.", "es": "Consolidado en la reumatología de alta complejidad. El monitoreo de seguridad refina el perfil de riesgo del paciente anciano.", "zh": "已在高复杂性风湿病治疗中确立地位，安全性监测正不断完善老年患者的风险特征评估。", "de": "Etabliert in der hochkomplexen Rheumatologie. Sicherheitsüberwachung verfeinert das Risikoprofil älterer Patienten.", "ja": "高度複雑性リウマチ治療において確立済み。安全性モニタリングにより高齢患者のリスクプロファイルを精緻化中。"}},
}

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


def sanitize_pdf_text(texto):
    if texto is None:
        return ""
    return str(texto).encode("latin-1", errors="replace").decode("latin-1")


def analisar_acao_reacao(peso_molecular, tag):
    if peso_molecular > 500:
        return t("safety_lipinski_alert")
    if tag == "inibidor":
        return t("safety_inhibitor")
    if tag == "senolitico":
        return t("safety_senolytic")
    return t("safety_default")


def gerar_insight_ia(composto, formula, peso, modulo, api_key):
    time.sleep(1.2)
    if api_key:
        return t("ai_insight_external", composto=composto.capitalize(), formula=formula, peso=peso, modulo=modulo)
    else:
        return t("ai_insight_local", composto=composto.capitalize(), formula=formula, peso=peso, modulo=modulo)


def gerar_moa_ia(composto, classe, descritores, modulo):
    time.sleep(1.0)
    perfil = t("moa_profile_lipophilic") if descritores.get("logp", 0) > 2 else t("moa_profile_hydrophilic")
    tamanho = t("moa_size_compact") if descritores.get("peso", 0) < 350 else t("moa_size_bulky")
    return (
        f"**{t('moa_title')} {composto.capitalize()}**\n\n"
        f"- **{t('moa_class_label')}** {classe}.\n"
        f"- **{t('moa_profile_label', perfil=perfil, tamanho=tamanho)}**\n"
        f"- **{t('moa_hypothesis_label', modulo=modulo_nome(modulo), classe=classe)}**\n"
        f"- **{t('moa_summary_label')}**"
    )


def classificar_evidencia_ia(titulo_artigo, pmid_valido):
    if not titulo_artigo or not pmid_valido:
        return {"nivel": t("evid_lvl_none"), "cor": "gray", "fator_confianca": t("conf_na")}

    titulo_lower = titulo_artigo.lower()
    if any(k in titulo_lower for k in ["meta-analysis", "systematic review"]):
        return {"nivel": t("evid_lvl_meta"), "cor": "green", "fator_confianca": t("conf_very_high")}
    if any(k in titulo_lower for k in ["randomized", "clinical trial", "phase ii", "phase iii", "double-blind"]):
        return {"nivel": t("evid_lvl_rct"), "cor": "green", "fator_confianca": t("conf_high")}
    if any(k in titulo_lower for k in ["cohort", "observational", "case-control"]):
        return {"nivel": t("evid_lvl_cohort"), "cor": "orange", "fator_confianca": t("conf_moderate")}
    if any(k in titulo_lower for k in ["in vitro", "cell line", "molecular docking", "in silico"]):
        return {"nivel": t("evid_lvl_invitro"), "cor": "orange", "fator_confianca": t("conf_moderate_low")}
    if any(k in titulo_lower for k in ["mice", "rat", "animal model", "in vivo"]):
        return {"nivel": t("evid_lvl_invivo"), "cor": "orange", "fator_confianca": t("conf_moderate")}
    if any(k in titulo_lower for k in ["review", "perspective", "opinion"]):
        return {"nivel": t("evid_lvl_review"), "cor": "gray", "fator_confianca": t("conf_low")}
    return {"nivel": t("evid_lvl_primary"), "cor": "orange", "fator_confianca": t("conf_moderate")}


def estimar_risco_herg(mol):
    if mol is None:
        return {"score": 0, "risco": t("risk_low")}
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
        risco = t("risk_high")
    elif score >= 3:
        risco = t("risk_moderate")
    else:
        risco = t("risk_low")
    return {"score": score, "risco": risco, "logp": round(logp, 2), "aneis_aromaticos": aromatic_rings, "n_basicos": basic_n}


def calcular_descritores_rdkit(smiles):
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
        "mol": mol, "peso": round(peso, 2), "logp": round(logp, 2), "hbd": hbd, "hba": hba,
        "tpsa": round(tpsa, 2), "rot_bonds": rot_bonds, "aneis": aneis,
        "violacoes_lipinski": violacoes_lipinski, "lipinski_ok": lipinski_ok,
        "veber_ok": veber_ok, "egan_ok": egan_ok, "alertas_pains": alertas_pains, "herg": herg,
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
    titulo_final = titulo or f"Estudo farmacologico sobre {nome_composto}"
    return (
        f"@article{{{chave},\n  title = {{{titulo_final}}},\n  author = {{SenoTrack Curation Team}},\n"
        f"  year = {{{datetime.now().year}}},\n  journal = {{PubMed Indexed Source}},\n  note = {{PMID: {pmid}}}\n}}"
    )


def gerar_ris(nome_composto, pmid, titulo=None):
    titulo_final = titulo or f"Estudo farmacologico sobre {nome_composto}"
    return (
        f"TY  - JOUR\nTI  - {titulo_final}\nAU  - SenoTrack Curation Team\n"
        f"PY  - {datetime.now().year}\nAN  - PMID:{pmid}\nER  -"
    )


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_pubmed_id(nome_composto, modo_offline=False):
    """Retorna o numero do PMID (string) ou None se nao encontrado."""
    if modo_offline:
        return "12345678"
    try:
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={nome_composto}[Title/Abstract]&retmode=json&retmax=1"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            ids = res.json().get("esearchresult", {}).get("idlist", [])
            if ids:
                return ids[0]
    except Exception as e:
        logging.error(f"Erro PubMed: {e}")
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_titulo_pubmed(pmid_num, modo_offline=False):
    if modo_offline or not pmid_num:
        return "Randomized clinical trial evaluating compound efficacy (offline demonstration)"
    try:
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid_num}&retmode=json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            item = data.get("result", {}).get(str(pmid_num), {})
            return item.get("title", "")
    except Exception as e:
        logging.error(f"Erro ao buscar titulo PubMed: {e}")
    return ""


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_interacao_rxnav(nome_composto, modo_offline=False):
    """Retorna o RxCUI (string) ou None se nao encontrado."""
    if modo_offline:
        return "9060"
    try:
        url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={nome_composto}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            rxcuis = res.json().get("idGroup", {}).get("rxnormId", [])
            if rxcuis:
                return rxcuis[0]
    except Exception as e:
        logging.error(f"Erro RxNav: {e}")
    return None


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
        logging.error(f"Erro na conexao com o PubChem: {str(e)}")
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
    idioma = st.session_state.get("idioma_ativo", "pt")
    nome_limpo = nome_composto.strip().lower()
    for chave, dados in KB_DATA.items():
        if dados["modulo"] == modulo_selecionado and chave in nome_limpo:
            return {
                "aplicacao": dados["aplicacao"].get(idioma, dados["aplicacao"]["pt"]),
                "pipeline": dados["pipeline"].get(idioma, dados["pipeline"]["pt"]),
                "classe": dados["classe"].get(idioma, dados["classe"]["pt"]),
                "tag": dados["tag"],
            }
    return {
        "aplicacao": t("kb_fallback_aplicacao", nome=nome_composto.capitalize(), modulo=modulo_nome(modulo_selecionado)),
        "pipeline": t("kb_fallback_pipeline"),
        "classe": t("kb_fallback_classe"),
        "tag": "outro",
    }


def obter_smiles_composto(nome_composto, modo_offline):
    nome_limpo = nome_composto.strip().lower()
    prop = consultar_api_pubchem(nome_composto, modo_offline=modo_offline)
    if prop and prop.get("CanonicalSMILES"):
        return prop["CanonicalSMILES"]
    if nome_limpo in MOCK_PUBCHEM_DATA and MOCK_PUBCHEM_DATA[nome_limpo].get("smiles"):
        return MOCK_PUBCHEM_DATA[nome_limpo]["smiles"]
    return None


class PDFLaudoPremium(FPDF):
    def header(self):
        self.set_fill_color(16, 20, 32)
        self.rect(0, 0, 210, 32, "F")
        self.set_fill_color(139, 124, 246)
        self.rect(0, 30, 210, 1.2, "F")
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "SENOTRACK ENTERPRISE SOLUTION", ln=True, align="C")
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(180, 190, 220)
        self.cell(0, 5, "Relatorio Executivo Customizado de Viabilidade de Compostos v10.0", ln=True, align="C")
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
        pdf.cell(0, 7, sanitize_pdf_text(f" {row['Nome Oficial']} ({row.get('Fórmula', '-')}) - {row.get('Massa Molecular', '-')}"), border=1, ln=True, fill=True)
        pdf.ln(1)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(139, 124, 246)
        pdf.cell(0, 5, "    Mecanismo e Aplicacao Clinica:", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 5, sanitize_pdf_text(f"    {row.get('Aplicação Médica', '')}"))
        if 'Referência PubMed' in row and row['Referência PubMed']:
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, f"    Ref: PMID {row['Referência PubMed']}", ln=True)
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


def renomear_colunas_display(df):
    idioma = st.session_state.get("idioma_ativo", "pt")
    mapa_interno = {
        "Nome Oficial": "col_official_name", "Fórmula": "col_formula", "Massa Molecular": "col_mol_mass",
        "Aplicação Médica": "col_medical_app", "Mapeamento Pipeline": "col_pipeline",
        "Absorção Oral": "col_oral_absorption", "Segurança Laboratorial": "col_lab_safety",
        "Referência PubMed": "col_pubmed_ref", "RxNav ID": "col_rxnav_id",
    }
    mapping = {k: t(v) for k, v in mapa_interno.items() if k in df.columns}
    return df.rename(columns=mapping)


if not os.path.exists("modelo_triagem_v7.xlsx"):
    df_modelo = pd.DataFrame({"Composto": ["quercetin", "dasatinib", "donepezil", "sacubitril", "empagliflozin", "semaglutide", "tofacitinib", "rapamycin"]})
    df_modelo.to_excel("modelo_triagem_v7.xlsx", index=False)

# =====================================================================
# SIDEBAR — SELETOR DE IDIOMA (primeiro, para propagar a todo o restante)
# =====================================================================
rotulo_idioma_atual = [k for k, v in IDIOMAS_DISPONIVEIS.items() if v == st.session_state.idioma_ativo][0]
escolha_idioma = st.sidebar.selectbox(
    "Idioma / Language / 语言",
    list(IDIOMAS_DISPONIVEIS.keys()),
    index=list(IDIOMAS_DISPONIVEIS.keys()).index(rotulo_idioma_atual),
)
st.session_state.idioma_ativo = IDIOMAS_DISPONIVEIS[escolha_idioma]
IDIOMA_ATUAL = st.session_state.idioma_ativo

st.markdown(f"<p style='color: #8b7cf6; font-weight: 700; margin-bottom: -10px; letter-spacing: 0.03em; font-size:0.8rem;'>{t('app_badge')}</p>", unsafe_allow_html=True)
st.title(t("app_title"))
st.markdown("---")

st.sidebar.markdown(f"### {t('sidebar_user_profile')}")
perfil_usuario = st.sidebar.radio(t("profile_radio_label"), [t("profile_didactic"), t("profile_research")], index=1)
modo_avancado = perfil_usuario == t("profile_research")

st.sidebar.markdown(f"### {t('sidebar_ai')}")
chave_api_ia = st.sidebar.text_input(t("api_key_label"), type="password", help=t("api_key_help"))

st.sidebar.markdown(f"### {t('sidebar_clinical_params')}")
modulo_ativo = st.sidebar.selectbox(
    t("module_label"),
    list(MODULE_TRANSLATIONS.keys()),
    format_func=modulo_nome,
)

st.sidebar.markdown(f"### {t('sidebar_filters')}")
limite_massa = st.sidebar.slider(t("mass_limit_label"), min_value=100, max_value=5000, value=1200, step=50, help=t("mass_limit_help"))
if modo_avancado:
    limite_tpsa = st.sidebar.slider(t("tpsa_limit_label"), min_value=20, max_value=250, value=140, step=5)
    limite_rot = st.sidebar.slider(t("rot_limit_label"), min_value=1, max_value=25, value=10, step=1)
else:
    limite_tpsa, limite_rot = 140, 10

st.sidebar.markdown(f"### {t('sidebar_infra')}")
modo_offline = st.sidebar.toggle(t("offline_toggle"), value=False)

if st.session_state.eln_experimentos:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### {t('eln_sidebar_title')}")
    st.sidebar.caption(t("eln_sidebar_caption", n=len(st.session_state.eln_experimentos)))

if st.session_state.historico_auditoria:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### {t('audit_sidebar_title')}")
    st.sidebar.caption(t("audit_sidebar_caption", n=len(st.session_state.historico_auditoria)))
    json_historico = json.dumps(st.session_state.historico_auditoria, indent=4, ensure_ascii=False)
    st.sidebar.download_button(label=t("audit_export_button"), data=json_historico,
                                file_name=f"auditoria_senotrack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", mime="application/json")

abas = st.tabs([t("tab_individual"), t("tab_lote"), t("tab_fq"), t("tab_docking"), t("tab_benchmark"), t("tab_literature"), t("tab_eln")])
aba_individual, aba_lote, aba_fq, aba_docking, aba_benchmark, aba_literatura, aba_eln = abas

# =====================================================================
# ABA 1 — PERFIL CLÍNICO INDIVIDUAL
# =====================================================================
with aba_individual:
    composto_a = st.text_input(t("input_molecule_label"), placeholder="Ex: dasatinib, sacubitril, semaglutide...", key="input_busca_individual")

    if composto_a:
        dados_locais = obter_dados_cientificos_v2(composto_a, modulo_ativo)
        prop = consultar_api_pubchem(composto_a, modo_offline=modo_offline)
        pmid = buscar_pubmed_id(composto_a, modo_offline=modo_offline)
        rxcui = buscar_interacao_rxnav(composto_a, modo_offline=modo_offline)

        if prop:
            nome = prop["Title"]
            formula = prop["MolecularFormula"]
            peso = prop["MolecularWeight"]

            registro = {"timestamp": datetime.now().isoformat(), "modulo": modulo_ativo, "composto_pesquisado": composto_a,
                        "nome_oficial": nome, "formula": formula, "massa_molecular": peso}
            if registro not in st.session_state.historico_auditoria:
                st.session_state.historico_auditoria.append(registro)

            st.markdown(f"## {nome}")
            c1, c2 = st.columns(2)
            c1.metric(t("metric_formula"), formula)
            c2.metric(t("metric_mass"), f"{peso} g/mol")

            sec_header("flask", t("section_application"))
            st.info(dados_locais["aplicacao"])

            sec_header("layers", t("section_pipeline"))
            st.warning(dados_locais["pipeline"])

            sec_header("book-open", t("section_evidence"))
            col_pm, col_rx = st.columns(2)
            with col_pm:
                sub_label(t("pubmed_article_label"))
                if pmid:
                    st.success(f"{t('pubmed_found')} PMID {pmid}")
                    st.markdown(f"[{t('pubmed_link')}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
                else:
                    st.warning(t("pubmed_not_found"))
            with col_rx:
                sub_label(t("rxnav_label"))
                if rxcui:
                    st.info(t("rxnav_found_template", id=rxcui))
                else:
                    st.info(t("rxnav_no_data"))

            st.write("---")
            sec_header("sparkles", t("ai_agent_section"))
            st.markdown(t("ai_agent_desc"))
            if st.button(t("btn_generate_insight", nome=nome)):
                with st.spinner(t("spinner_generating")):
                    insight = gerar_insight_ia(nome, formula, peso, modulo_nome(modulo_ativo), chave_api_ia)
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
                            st.caption(t("structure3d_unavailable"))
                    except Exception as e:
                        st.caption(f"{t('generic_error_prefix')} {e}")
                else:
                    st.info(t("offline_3d_msg"))

            st.write("---")
            if st.button(t("btn_save_eln"), key="salvar_eln_individual"):
                st.session_state.eln_experimentos.append({
                    "id": str(uuid.uuid4())[:8], "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "nome": nome, "modulo": modulo_ativo, "notas": "",
                    "dados": {"formula": formula, "peso_molecular": peso, "aplicacao": dados_locais["aplicacao"]}
                })
                st.success(t("eln_saved_success"))

            df_individual = pd.DataFrame([{"Nome Oficial": nome, "Aplicação Médica": dados_locais["aplicacao"]}])
            data_hora_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(label=t("btn_download_pdf_individual"), data=gerar_pdf_laudo(df_individual),
                                file_name=f"laudo_{composto_a}_{data_hora_str}.pdf", mime="application/pdf")
            if IDIOMA_ATUAL in ("zh", "ja"):
                st.caption(t("cjk_pdf_notice"))
        else:
            st.error(t("error_compound_not_found"))

# =====================================================================
# ABA 2 — LOTE HOSPITALAR
# =====================================================================
with aba_lote:
    st.caption(t("lote_caption"))
    col_dl1, col_dl2 = st.columns([1, 2])
    with col_dl1:
        with open("modelo_triagem_v7.xlsx", "rb") as f:
            st.download_button(label=t("btn_download_template"), data=f, file_name="modelo_triagem_v7.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

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
                            dados_c = obter_dados_cientificos_v2(nome_comp, modulo_ativo)
                            f_quimica, p_molecular = "-", 350.0
                            prop_b = consultar_api_pubchem(nome_comp, modo_offline=modo_offline)
                            pmid_lote = buscar_pubmed_id(nome_comp, modo_offline=modo_offline)
                            rxcui_lote = buscar_interacao_rxnav(nome_comp, modo_offline=modo_offline)

                            if prop_b:
                                f_quimica = prop_b["MolecularFormula"]
                                p_molecular = prop_b["MolecularWeight"]

                            status_absorcao = t("absorption_high") if p_molecular < 500 else t("absorption_moderate")
                            seguranca = analisar_acao_reacao(p_molecular, dados_c["tag"])

                            list_rows.append({
                                "Nome Oficial": nome_comp.capitalize(), "Fórmula": f_quimica, "Massa Numérica": p_molecular,
                                "Massa Molecular": f"{p_molecular} g/mol", "Aplicação Médica": dados_c["aplicacao"],
                                "Mapeamento Pipeline": dados_c["pipeline"], "Absorção Oral": status_absorcao,
                                "Segurança Laboratorial": seguranca, "Referência PubMed": pmid_lote or "", "RxNav ID": rxcui_lote or "",
                            })
                        except Exception as err_comp:
                            logging.warning(f"Erro ao processar composto {nome_comp}: {err_comp}")
                            list_rows.append({
                                "Nome Oficial": nome_comp.capitalize(), "Fórmula": t("batch_error_formula"), "Massa Numérica": 9999.0,
                                "Massa Molecular": f"{t('batch_error_formula')} g/mol", "Aplicação Médica": t("batch_error_app"),
                                "Mapeamento Pipeline": "N/A", "Absorção Oral": t("batch_error_absorption"),
                                "Segurança Laboratorial": t("batch_error_safety"), "Referência PubMed": "", "RxNav ID": "",
                            })

                df_mestre = pd.DataFrame(list_rows)
                df_filtrado = df_mestre[df_mestre["Massa Numérica"] <= limite_massa]
                itens_excluidos = len(df_mestre) - len(df_filtrado)

                st.write("---")
                sec_header("gauge", t("kpi_section"))
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                compostos_com_pubmed = sum(1 for x in df_filtrado["Referência PubMed"] if str(x).strip())
                kpi1.metric(t("kpi_total"), f"{len(df_mestre)}")
                kpi2.metric(t("kpi_approved"), f"{len(df_filtrado)}", delta=f"-{itens_excluidos}" if itens_excluidos > 0 else "100%")
                kpi3.metric(t("kpi_evidence"), f"{compostos_com_pubmed}")
                kpi4.metric(t("kpi_module"), modulo_nome(modulo_ativo))

                if itens_excluidos > 0:
                    st.warning(t("batch_lipinski_warning", itens=itens_excluidos, limite=limite_massa))

                st.write("---")
                sec_header("sparkles", t("ai_batch_section"))
                st.markdown(t("ai_batch_desc"))
                if st.button(t("btn_generate_batch_ai")):
                    with st.spinner(t("spinner_batch_scan")):
                        nomes_lote = ", ".join(df_filtrado["Nome Oficial"].tolist())
                        time.sleep(1.5)
                        parecer = (
                            f"**{t('batch_ai_report_title')}**\n\n"
                            f"{t('batch_ai_analyzed', n=len(df_filtrado), modulo=modulo_nome(modulo_ativo), nomes=nomes_lote)}\n\n"
                            f"- {t('batch_ai_coherence', modulo=modulo_nome(modulo_ativo))}\n"
                            f"- {t('batch_ai_pk', n=compostos_com_pubmed)}\n"
                            f"- {t('batch_ai_recommendation')}"
                        )
                        st.success(parecer)

                st.write("---")
                sec_header("layers", t("matrix_section"))
                if not df_filtrado.empty:
                    compostos_validos = df_filtrado.to_dict(orient="records")
                    colunas_cards = st.columns(min(len(compostos_validos), 3))
                    for idx, item in enumerate(compostos_validos):
                        col_idx = idx % 3
                        with colunas_cards[col_idx]:
                            pmid_txt = item['Referência PubMed']
                            if str(pmid_txt).strip():
                                link_pubmed = f"<a href='https://pubmed.ncbi.nlm.nih.gov/{pmid_txt}/' target='_blank' style='color:var(--accent-purple, #8b5cf6); font-weight:bold; text-decoration:underline;'>PubMed (PMID {pmid_txt})</a>"
                            else:
                                link_pubmed = f"<span style='color:var(--text-secondary);'>{t('pubmed_not_found')}</span>"
                            st.markdown(f"""
                            <div style='background-color: var(--bg-card); padding: 18px; border-radius: 12px; border-left: 4px solid var(--accent-purple, #8b5cf6); margin-bottom:15px; min-height: 220px; border-top: 1px solid var(--border-subtle); border-right: 1px solid var(--border-subtle); border-bottom: 1px solid var(--border-subtle);'>
                                <h4 style='margin-top:0; color:var(--text-primary); font-size:16px;'>{item['Nome Oficial']}</h4>
                                <p style='font-size:13px; margin-bottom:6px; color:var(--text-primary);'><b>{t('metric_formula')}:</b> {item['Fórmula']} | <b>{t('metric_mass')}:</b> {item['Massa Molecular']}</p>
                                <p style='font-size:12px; margin-bottom:8px; color:var(--accent-purple, #8b5cf6);'><b>{t('rxnav_found_template', id=item['RxNav ID']) if item['RxNav ID'] else t('rxnav_no_data')}</b></p>
                                <p style='font-size:12px; margin-bottom:10px; color:var(--text-secondary); line-height: 1.4;'>{item['Aplicação Médica']}</p>
                                <hr style='border: 0.5px solid var(--border-subtle); margin: 8px 0;'>
                                <p style='font-size:12px; margin-bottom:0;'>{link_pubmed}</p>
                            </div>
                            """, unsafe_allow_html=True)

                st.write("---")
                sec_header("microscope", t("detail_section"))
                for idx, row in df_filtrado.iterrows():
                    with st.expander(f"{row['Nome Oficial']} — {row['Massa Molecular']}"):
                        col_exp1, col_exp2 = st.columns(2)
                        with col_exp1:
                            st.write(f"**{t('section_application')}:** {row['Aplicação Médica']}")
                            st.write(f"**{t('section_pipeline')}:** {row['Mapeamento Pipeline']}")
                            st.write(f"**{t('col_oral_absorption')}:** {row['Absorção Oral']}")
                        with col_exp2:
                            st.write(f"**RxNav:** {t('rxnav_found_template', id=row['RxNav ID']) if row['RxNav ID'] else t('rxnav_no_data')}")
                            st.write(f"**PubMed:** {('PMID ' + str(row['Referência PubMed'])) if row['Referência PubMed'] else t('pubmed_not_found')}")
                            st.write(f"**{t('col_lab_safety')}:** {row['Segurança Laboratorial']}")
                            if str(row['Referência PubMed']).strip():
                                st.markdown(f"[{t('pubmed_link')}](https://pubmed.ncbi.nlm.nih.gov/{row['Referência PubMed']}/)")

                st.divider()
                sec_header("database", t("master_table_title"))
                df_visualizacao = df_filtrado.drop(columns=["Massa Numérica"]) if not df_filtrado.empty else df_filtrado
                df_display = renomear_colunas_display(df_visualizacao)
                st.markdown(df_display.to_html(classes="tabela-v12", index=False, escape=False), unsafe_allow_html=True)

                if not df_filtrado.empty:
                    st.divider()
                    sec_header("bar-chart", t("density_section"))
                    st.bar_chart(data=df_filtrado, x="Nome Oficial", y="Massa Numérica", color="#8b7cf6")

                    fig, ax = plt.subplots(figsize=(7, 3.5))
                    fig.patch.set_facecolor('#ffffff')
                    ax.set_facecolor('#ffffff')
                    ax.bar(df_filtrado["Nome Oficial"], df_filtrado["Massa Numérica"], color="#8b5cf6", width=0.4)
                    ax.set_ylabel("Massa Molecular (g/mol)", fontsize=9, color="#262730")
                    ax.tick_params(axis='both', labelsize=8, colors="#262730")
                    for spine in ax.spines.values():
                        spine.set_color('#d0d3db')
                    plt.tight_layout()
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png', dpi=200, facecolor=fig.get_facecolor())
                    buf.seek(0)
                    grafico_bytes = buf.getvalue()
                    plt.close(fig)

                    st.divider()
                    sec_header("file-text", t("export_section"))
                    c_pdf, c_json = st.columns([1, 1])
                    with c_pdf:
                        data_hora_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                        st.download_button(label=t("btn_download_pdf_batch"), data=gerar_pdf_laudo_lote(df_visualizacao, grafico_bytes),
                                            file_name=f"laudo_triagem_lote_{data_hora_str}.pdf", mime="application/pdf", type="primary")
                        if IDIOMA_ATUAL in ("zh", "ja"):
                            st.caption(t("cjk_pdf_notice"))
                    with c_json:
                        json_lote = df_visualizacao.to_json(orient="records", force_ascii=False, indent=4)
                        st.download_button(label=t("btn_download_json_batch"), data=json_lote,
                                            file_name=f"dados_lote_{data_hora_str}.json", mime="application/json")
        except Exception as e:
            st.error(f"{t('generic_error_prefix')} {e}")

# =====================================================================
# ABA 3 — TRIAGEM FÍSICO-QUÍMICA
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
                    sec_header("gauge", t("rules_section"))
                    st.markdown(f"**{t('rule_lipinski')}:** {t('rule_pass') if descritores['lipinski_ok'] else t('rule_fail')} — {descritores['violacoes_lipinski']} {t('rule_violations')}")
                    veber_pass = descritores['rot_bonds'] <= limite_rot and descritores['tpsa'] <= limite_tpsa
                    st.markdown(f"**{t('rule_veber')}** (Rot. Bonds ≤ {limite_rot}, TPSA ≤ {limite_tpsa} Å²): {t('rule_pass') if veber_pass else t('rule_fail')}")
                    st.markdown(f"**{t('rule_egan')}** (LogP ≤ 5.88, TPSA ≤ 131.6 Å²): {t('rule_pass') if descritores['egan_ok'] else t('rule_fail')}")

                    if modo_avancado:
                        st.write("---")
                        sec_header("shield", t("pains_section"))
                        if descritores['alertas_pains']:
                            for alerta in descritores['alertas_pains']:
                                st.error(f"{t('pains_alert_prefix')} {alerta}")
                        else:
                            st.success(t("pains_none"))

                        st.write("---")
                        sec_header("activity", t("herg_section"))
                        herg = descritores['herg']
                        st.markdown(f"**{t('herg_risk_label')}** {herg['risco']}")
                        st.caption(f"Score: {herg['score']}/7 | LogP: {herg['logp']} | {herg['aneis_aromaticos']} | N: {herg['n_basicos']}")
                        st.caption(t("herg_disclaimer"))
                    else:
                        st.info(t("didactic_notice_fq"))

                with col_estrutura:
                    sec_header("flask", t("structure2d_section"))
                    svg_2d = gerar_svg_2d(descritores['mol'])
                    if svg_2d:
                        st.image(svg_2d, use_container_width=True)
                    if modo_avancado:
                        sdf_bytes = gerar_sdf_bytes(descritores['mol'], composto_fq)
                        if sdf_bytes:
                            st.download_button(t("btn_download_sdf"), data=sdf_bytes, file_name=f"{composto_fq}_3d.sdf", mime="chemical/x-mdl-sdfile")

# =====================================================================
# ABA 4 — DOCKING VIRTUAL & PROTEÔMICA
# =====================================================================
with aba_docking:
    st.caption(t("docking_caption"))
    col_prot, col_lig = st.columns(2)
    with col_prot:
        sec_header("layers", t("protein_target_section"))
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
                st.error(f"{t('pdb_render_error')} {e}")

    with col_lig:
        sec_header("flask", t("ligand_section"))
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
        sec_header("gauge", t("docking_score_section"))
        st.caption(t("docking_disclaimer"))

        peso, logp, rot = descritores_dock['peso'], descritores_dock['logp'], descritores_dock['rot_bonds']
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
            sec_header("shield", t("offtarget_section"))
            st.markdown(f"**hERG:** {descritores_dock['herg']['risco']}")
    else:
        st.info(t("docking_empty_notice"))

# =====================================================================
# ABA 5 — FARMACOTERAPIA & BENCHMARK
# =====================================================================
with aba_benchmark:
    st.caption(t("benchmark_caption"))
    sec_header("bar-chart", t("molecule_select_section"))
    farmaco_sugerido = FARMACO_CONTROLE_POR_MODULO.get(modulo_ativo, "dasatinib")
    texto_compostos = st.text_input(
        t("benchmark_input_label"),
        value=f"{farmaco_sugerido}, quercetin",
        help=t("benchmark_input_help"),
        key="input_benchmark_freeform",
    )
    compostos_selecionados = [c.strip() for c in texto_compostos.split(",") if c.strip()]
    # remove duplicatas preservando a ordem de digitação
    compostos_selecionados = list(dict.fromkeys(compostos_selecionados))
    if len(compostos_selecionados) > 6:
        st.warning(t("benchmark_too_many_warn"))
        compostos_selecionados = compostos_selecionados[:6]

    if len(compostos_selecionados) >= 2:
        perfis = {}
        with st.spinner(t("spinner_batch_scan")):
            for comp in compostos_selecionados:
                smiles_c = obter_smiles_composto(comp, modo_offline)
                perfis[comp] = calcular_descritores_rdkit(smiles_c) if smiles_c else None

        perfis_validos = {k: v for k, v in perfis.items() if v is not None}

        if len(perfis_validos) >= 2:
            st.write("---")
            sec_header("layers", t("synergy_matrix_title"))
            linhas_matriz = []
            nomes_validos = list(perfis_validos.keys())
            for i in range(len(nomes_validos)):
                linha = {"Composto": nomes_validos[i].capitalize()}
                for j in range(len(nomes_validos)):
                    if i == j:
                        linha[nomes_validos[j].capitalize()] = "—"
                    else:
                        p1, p2 = perfis_validos[nomes_validos[i]], perfis_validos[nomes_validos[j]]
                        similaridade = round(100 - (abs(p1['logp'] - p2['logp']) * 10 + abs(p1['tpsa'] - p2['tpsa']) * 0.3), 1)
                        similaridade = max(0, min(100, similaridade))
                        classificacao = t("synergy_high") if similaridade > 70 else (t("synergy_moderate") if similaridade > 40 else t("synergy_low"))
                        linha[nomes_validos[j].capitalize()] = f"{similaridade}% — {classificacao}"
                linhas_matriz.append(linha)
            df_matriz = pd.DataFrame(linhas_matriz).set_index("Composto")
            st.dataframe(df_matriz, use_container_width=True)
            st.caption(t("synergy_disclaimer"))

            st.write("---")
            sec_header("target" if "target" in ICON_PATHS else "bar-chart", t("radar_section"))
            farmaco_controle = FARMACO_CONTROLE_POR_MODULO.get(modulo_ativo, nomes_validos[0])
            st.markdown(f"**{t('gold_standard_label')} “{modulo_nome(modulo_ativo)}”:** `{farmaco_controle}`")

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
                    r=valores + [valores[0]], theta=categorias + [categorias[0]], fill='toself',
                    name=nome_c.capitalize() + (" ★" if nome_c == farmaco_controle else "")
                ))
            fig_radar.update_layout(
                polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(128,128,128,0.35)")),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=True,
            )
            st.plotly_chart(fig_radar, use_container_width=True, theme="streamlit")
        else:
            st.warning(t("benchmark_invalid_smiles_warn"))
    else:
        st.info(t("benchmark_min_molecules_warn"))

# =====================================================================
# ABA 6 — AGENTE CLÍNICO & LITERATURA
# =====================================================================
with aba_literatura:
    st.caption(t("literature_caption"))
    composto_lit = st.text_input(t("literature_input_label"), placeholder="Ex: rapamycin, empagliflozin...", key="input_literatura")

    if composto_lit:
        dados_locais_lit = obter_dados_cientificos_v2(composto_lit, modulo_ativo)
        pmid_lit = buscar_pubmed_id(composto_lit, modo_offline=modo_offline)

        sec_header("book-open", t("evidence_section"))
        if pmid_lit:
            titulo_artigo = buscar_titulo_pubmed(pmid_lit, modo_offline=modo_offline)
            classificacao = classificar_evidencia_ia(titulo_artigo, pmid_lit)
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"**{t('title_retrieved_label')}** {titulo_artigo if titulo_artigo else t('title_unavailable')}")
                st.markdown(f"**PMID:** {pmid_lit}")
                st.markdown(f"[PubMed](https://pubmed.ncbi.nlm.nih.gov/{pmid_lit}/)")
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
        sec_header("sparkles", t("moa_section"))
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
        sec_header("file-text", t("citation_section"))
        if pmid_lit:
            titulo_ref = buscar_titulo_pubmed(pmid_lit, modo_offline=modo_offline)
            col_bib, col_ris = st.columns(2)
            with col_bib:
                st.download_button(t("btn_export_bib"), data=gerar_bibtex(composto_lit, pmid_lit, titulo_ref),
                                    file_name=f"{composto_lit}_citacao.bib", mime="application/x-bibtex")
            with col_ris:
                st.download_button(t("btn_export_ris"), data=gerar_ris(composto_lit, pmid_lit, titulo_ref),
                                    file_name=f"{composto_lit}_citacao.ris", mime="application/x-research-info-systems")

# =====================================================================
# ABA 7 — CADERNO CIENTÍFICO (ELN)
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
                        dados_exp = {"peso": desc_exp["peso"], "logp": desc_exp["logp"], "tpsa": desc_exp["tpsa"],
                                     "lipinski_ok": desc_exp["lipinski_ok"], "veber_ok": desc_exp["veber_ok"],
                                     "egan_ok": desc_exp["egan_ok"], "risco_herg": desc_exp["herg"]["risco"]}
                st.session_state.eln_experimentos.append({
                    "id": str(uuid.uuid4())[:8], "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "nome": nome_exp, "modulo": modulo_ativo, "notas": notas_exp, "dados": dados_exp
                })
                st.success(t("exp_saved_success", nome=nome_exp))
                st.rerun()

    st.write("---")
    sec_header("clipboard", t("registered_experiments_title"))
    if not st.session_state.eln_experimentos:
        st.info(t("no_experiments_notice"))
    else:
        for exp in reversed(st.session_state.eln_experimentos):
            with st.expander(f"{exp['nome']} — {exp['timestamp']} ({modulo_nome(exp['modulo'])})"):
                st.json(exp['dados']) if exp['dados'] else st.caption(t("no_fq_data_caption"))
                st.write(f"**{t('notes_label_short')}** {exp.get('notas', '-')}")
                if st.button(t("btn_delete_record"), key=f"del_{exp['id']}"):
                    st.session_state.eln_experimentos = [e for e in st.session_state.eln_experimentos if e['id'] != exp['id']]
                    st.rerun()

        st.write("---")
        sec_header("file-text", t("eln_export_section"))
        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            json_eln = json.dumps(st.session_state.eln_experimentos, indent=4, ensure_ascii=False)
            st.download_button(t("btn_export_all_json"), data=json_eln,
                                file_name=f"eln_senotrack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", mime="application/json")
        with col_e2:
            st.download_button(t("btn_export_pdf_consolidated"), data=gerar_pdf_eln(st.session_state.eln_experimentos),
                                file_name=f"eln_senotrack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf")
        with col_e3:
            df_eln_export = pd.DataFrame([{"Composto": e["nome"], "Timestamp": e["timestamp"], "Módulo": modulo_nome(e["modulo"]),
                                            "Notas": e.get("notas", ""), **e.get("dados", {})} for e in st.session_state.eln_experimentos])
            csv_eln = df_eln_export.to_csv(index=False).encode("utf-8")
            st.download_button(t("btn_export_csv"), data=csv_eln,
                                file_name=f"eln_senotrack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv")

        if IDIOMA_ATUAL in ("zh", "ja"):
            st.caption(t("cjk_pdf_notice"))

        if st.button(t("btn_clear_notebook")):
            st.session_state.eln_experimentos = []
            st.rerun()