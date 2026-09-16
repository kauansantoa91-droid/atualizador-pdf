import os
import re
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    Flowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# CONFIGURAÇÕES DE PASTAS E ARQUIVOS
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_LOGOS = "assets/logos"
LOGO_CABECALHO = "logo_cabecalho.png"
LOGO_RODAPE = "logo_rodape.png"
LOGO_MARCA_DAGUA = "marca_dagua.png"
QRCODE = "qrcode.png"

st.set_page_config(
    page_title="Atualizador de PDF Cadastral",
    page_icon="📄",
    layout="centered"
)

st.markdown("""
    <style>
    .main {
        background-color: #0d1117;
    }
    .stTextArea textarea {
        background-color: #161b22;
        color: #ffffff;
        border: 1px solid #30363d;
    }
    .stTextInput input {
        background-color: #161b22;
        color: #ffffff;
        border: 1px solid #30363d;
    }
    h1, h2, h3 {
        color: #ffffff !important;
    }
    .subtext {
        color: #8b949e;
        text-align: center;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>Atualizador de PDF Cadastral</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtext'>Cole a ficha do cliente abaixo para extrair os dados e gerar o PDF</p>", unsafe_allow_html=True)

# FUNÇÃO DE EXTRAÇÃO INTELIGENTE PARA O NOVO FORMATO DE FICHA
def extrair_dados_ficha(texto_ficha):
    dados = {
        "Razão Social": "NÃO IDENTIFICADO",
        "CNPJ": "00.000.000/0000-00",
        "Situação": "ATIVA",
        "CPF Master": "000.000.000-00",
        "Nome Responsável": "NÃO IDENTIFICADO",
        "Usuário(s)": "NÃO IDENTIFICADO",
    }

    if not texto_ficha.strip():
        return dados

    texto_ficha = texto_ficha.replace("\\", "/")

    # Captura do CNPJ
    match_cnpj = re.search(r"(?:CNPJ)[:\s]*([\d./-]+)", texto_ficha, re.IGNORECASE)
    if match_cnpj:
        c_limpo = re.sub(r"\D", "", match_cnpj.group(1))
        if len(c_limpo) == 14:
            dados["CNPJ"] = f"{c_limpo[:2]}.{c_limpo[2:5]}.{c_limpo[5:8]}/{c_limpo[8:12]}-{c_limpo[12:]}"

    # Captura da Empresa / Razão Social
    match_empresa = re.search(r"(?:Empresa|Raz[ãa]o\s*Social)[:\s]*([^\n]+)", texto_ficha, re.IGNORECASE)
    if match_empresa:
        dados["Razão Social"] = match_empresa.group(1).strip()

    # Captura do CPF (Documento/CPF)
    match_cpf = re.search(r"(?:Documento/CPF|CPF\s*Master|CPF)[:\s]*([\d.-]+)", texto_ficha, re.IGNORECASE)
    if match_cpf:
        cpf_limpo = re.sub(r"\D", "", match_cpf.group(1))
        if len(cpf_limpo) == 11:
            dados["CPF Master"] = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"

    # Captura do Nome
    match_nome = re.search(r"(?:Nome)[:\s]*([^\n]+)", texto_ficha, re.IGNORECASE)
    if match_nome:
        dados["Nome Responsável"] = match_nome.group(1).strip()

    # Captura do Usuário
    match_user = re.search(r"(?:usuario|usu[áa]rio)[:\s]*([A-Za-z0-9]+)", texto_ficha, re.IGNORECASE)
    if match_user:
        dados["Usuário(s)"] = match_user.group(1).strip()

    return dados

class CheckVerde(Flowable):
    def __init__(self, tamanho=9):
        Flowable.__init__(self)
        self.tamanho = tamanho
        self.width = tamanho
        self.height = tamanho

    def draw(self):
        c = self.canv
        s = self.tamanho
        r = s / 2
        c.saveState()
        c.setFillColor(colors.HexColor("#00A859"))
        c.circle(r, r, r, fill=1, stroke=0)
        c.setStrokeColor(colors.white)
        c.setLineWidth(1.2)
        c.setLineCap(1)
        c.line(s * 0.28, s * 0.48, s * 0.42, s * 0.32)
        c.line(s * 0.42, s * 0.32, s * 0.72, s * 0.68)
        c.restoreState()

class LinhaVertical(Flowable):
    def __init__(self, altura=38, cor="#B0B0B0", largura_linha=1):
        Flowable.__init__(self)
        self.altura = altura
        self.cor = cor
        self.largura_linha = largura_linha
        self.width = largura_linha
        self.height = altura

    def draw(self):
        c = self.canv
        c.saveState()
        c.setStrokeColor(colors.HexColor(self.cor))
        c.setLineWidth(self.largura_linha)
        c.line(0, 0, 0, self.altura)
        c.restoreState()

def caminho_logo(pasta_script, nome):
    return os.path.join(pasta_script, PASTA_LOGOS, nome)

def carregar_imagem(caminho, largura=None, altura=None):
    if os.path.exists(caminho):
        img = Image(caminho)
        if altura and not largura:
            fator = altura / float(img.imageHeight)
            img.drawWidth = img.imageWidth * fator
            img.drawHeight = altura
        elif largura and not altura:
            fator = largura / float(img.imageWidth)
            img.drawWidth = largura
            img.drawHeight = img.imageHeight * fator
        elif largura and altura:
            img.drawWidth = largura
            img.drawHeight = altura
        return img
    return Spacer(largura or 100, altura or 30)

def adicionar_marca_dagua(canvas, doc):
    pasta_script = os.path.dirname(os.path.abspath(__file__))
    caminho = caminho_logo(pasta_script, LOGO_MARCA_DAGUA)

    if not os.path.exists(caminho):
        caminho = caminho_logo(pasta_script, LOGO_RODAPE)

    canvas.saveState()

    try:
        canvas.setFillAlpha(0.05)
        canvas.setStrokeAlpha(0.05)
    except AttributeError:
        pass

    largura_item = 130
    altura_item = 120
    passo_x = 130
    passo_y = 120

    if os.path.exists(caminho):
        row_idx = 0
        for y in range(-20, int(A4[1]) + 70, passo_y):
            offset_x = (row_idx % 2) * (passo_x / 2)
            for x in range(-80, int(A4[0]) + 100, passo_x):
                canvas.drawImage(
                    caminho,
                    x + offset_x,
                    y,
                    width=largura_item,
                    height=altura_item,
                    mask="auto",
                    preserveAspectRatio=True,
                )
            row_idx += 1

    canvas.restoreState()

def gerar_pdf(pasta_script, dados_empresa):
    razao = dados_empresa["Razão Social"]
    razao_limpa = re.sub(r'[\\/*?:"<>|]', "", razao)
    nome_pdf = f"ATUALIZAÇÃO CADASTRAL - {razao_limpa}.pdf"
    caminho_pdf = os.path.join(pasta_script, nome_pdf)

    # Margens balanceadas (40) para manter o layout original e garantir que caiba em 1 página
    doc = SimpleDocTemplate(
        caminho_pdf,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    story = []
    styles = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        "Titulo",
        parent=styles["Heading1"],
        fontSize=13,
        leading=15,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#111111"),
        alignment=0,
    )
    estilo_sub = ParagraphStyle(
        "Sub",
        parent=styles["Heading2"],
        fontSize=10.5,
        leading=13,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#222222"),
    )
    estilo_secao = ParagraphStyle(
        "Secao",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=12,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#333333"),
    )
    estilo_texto = ParagraphStyle(
        "Texto",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#444444"),
    )
    estilo_topico = ParagraphStyle(
        "Topico",
        parent=styles["Normal"],
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#333333"),
    )
    estilo_qr_legenda = ParagraphStyle(
        "QRLegenda",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=9,
        alignment=1,
        textColor=colors.HexColor("#666666"),
    )

    logo_topo = carregar_imagem(
        caminho_logo(pasta_script, LOGO_CABECALHO), altura=60
    )
    linha_divisoria = LinhaVertical(altura=55, cor="#B0B0B0", largura_linha=1)
    p_titulo = Paragraph("COMUNICADO IMPORTANTE", estilo_titulo)

    cab = Table([[logo_topo, linha_divisoria, p_titulo]], colWidths=[195, 25, 310])
    cab.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("ALIGN", (2, 0), (2, 0), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(cab)
    story.append(Spacer(1, 14))

    story.append(Paragraph("ATUALIZAÇÃO CADASTRAL", estilo_sub))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "Em conformidade com as diretrizes de autorregulação bancária e as boas práticas "
            "estabelecidas pelo sistema financeiro nacional, comunicamos que a atualização cadastral "
            "de empresas junto ao Internet Banking Empresarial é procedimento obrigatório e periódico.",
            estilo_texto,
        )
    )
    story.append(Spacer(1, 12))

    story.append(Paragraph("DADOS DO MASTER:", estilo_secao))
    story.append(Spacer(1, 4))
    
    tabela_dados = [
        ("Razão Social", dados_empresa.get("Razão Social", "")),
        ("CNPJ", dados_empresa.get("CNPJ", "")),
        ("Situação", dados_empresa.get("Situação", "ATIVA")),
        ("CPF Master", dados_empresa.get("CPF Master", "")),
        ("Nome Responsável", dados_empresa.get("Nome Responsável", "")),
        ("Usuário(s)", dados_empresa.get("Usuário(s)", ""))
    ]
    
    tabela = [
        [Paragraph(f"<b>{k}:</b>", estilo_texto), Paragraph(str(v), estilo_texto)]
        for k, v in tabela_dados
    ]
    t = Table(tabela, colWidths=[110, 420])
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(
        Paragraph("A atualização cadastral tem como finalidade:", estilo_texto)
    )
    story.append(Spacer(1, 6))

    check = CheckVerde(tamanho=9)
    for item in [
        "Garantir a segurança das operações financeiras;",
        "Manter os dados da empresa e de seus representantes legais atualizados;",
        "Atender às exigências regulatórias vigentes;",
        "Prevenir fraudes e inconsistências cadastrais.",
    ]:
        row = Table([[check, Paragraph(item, estilo_topico)]], colWidths=[16, 514])
        row.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (0, 0), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(row)

    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Reforçamos que a não realização da atualização dentro do prazo estabelecido poderá acarretar "
            "restrições operacionais, incluindo limitações temporárias de acesso a determinados serviços bancários.",
            estilo_texto,
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "A atualização pode ser realizada diretamente pelo Bradesco Net Empresas, acessando o menu de "
            "Cadastro/Atualização Cadastral, ou mediante comparecimento à agência de relacionamento.",
            estilo_texto,
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "Em caso de dúvidas, recomenda-se entrar em contato com seu gerente de contas ou com a "
            "central de atendimento empresarial.",
            estilo_texto,
        )
    )
    story.append(Spacer(1, 16))

    # Rodapé original exato (4 colunas mantendo o QR Code e o logo lado a lado na parte inferior)
    img_rodape = carregar_imagem(caminho_logo(pasta_script, LOGO_RODAPE), altura=65)
    img_qr = carregar_imagem(caminho_logo(pasta_script, QRCODE), largura=95, altura=95)
    p_legenda_qr = Paragraph("Escaneie o QR Code para acessar o portal", estilo_qr_legenda)

    bloco_qr = Table([[img_qr], [Spacer(1, 3)], [p_legenda_qr]], colWidths=[120])
    bloco_qr.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    rod = Table([["", img_rodape, bloco_qr, ""]], colWidths=[70, 150, 130, 180])
    rod.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("ALIGN", (2, 0), (2, 0), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(rod)

    doc.build(story, onFirstPage=adicionar_marca_dagua, onLaterPages=adicionar_marca_dagua)
    return caminho_pdf

# INTERFACE DO STREAMLIT
ficha_input = st.text_area("COLE A FICHA DO CLIENTE AQUI", placeholder="Cole a linha ou o bloco de texto da ficha...", height=120)

if st.button("Processar e Gerar PDF", type="primary"):
    if ficha_input.strip():
        dados_extraidos = extrair_dados_ficha(ficha_input)
        st.session_state['dados_empresa'] = dados_extraidos
        st.success("Ficha lida e dados extraídos com sucesso!")
    else:
        st.warning("Por favor, cole uma ficha na caixa de texto acima.")

if 'dados_empresa' in st.session_state:
    dados = st.session_state['dados_empresa']
    st.markdown("---")
    st.subheader("DADOS EXTRAÍDOS PARA O PDF")
    
    col1, col2 = st.columns(2)
    with col1:
        razao_social = st.text_input("Razão Social", value=dados["Razão Social"])
        cnpj_val = st.text_input("CNPJ", value=dados["CNPJ"])
        nome_resp = st.text_input("Nome Responsável", value=dados.get("Nome Responsável", ""))
    with col2:
        situacao = st.text_input("Situação", value=dados["Situação"])
        cpf_master = st.text_input("CPF Master", value=dados["CPF Master"])
        usuario_val = st.text_input("Usuário", value=dados.get("Usuário(s)", ""))
    
    dados_atualizados = {
        "Razão Social": razao_social,
        "CNPJ": cnpj_val,
        "Situação": situacao,
        "CPF Master": cpf_master,
        "Nome Responsável": nome_resp,
        "Usuário(s)": usuario_val
    }

    if st.button("Baixar PDF Pronto"):
        caminho_pdf = gerar_pdf(PASTA_SCRIPT, dados_atualizados)
        with open(caminho_pdf, "rb") as f:
            st.download_button(
                label="📥 Clique aqui para salvar o PDF",
                data=f,
                file_name=os.path.basename(caminho_pdf),
                mime="application/pdf"
            )
