import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np
from fpdf import FPDF
import tempfile
from io import BytesIO
from datetime import datetime

# Subclasse do FPDF com rodapé personalizado
class PDFComRodape(FPDF):
    def footer(self):
        self.set_y(-15)  # 15mm do fim da página
        self.set_font("Arial", "I", 8)
        self.set_text_color(150)
        data = datetime.now().strftime("%d/%m/%Y")
        page_text = f"Emitido em: {data}    -    Página {self.page_no()} de {{nb}}"
        self.cell(0, 10, page_text, align="C")

# Função para adicionar o cabeçalho
def adicionar_cabecalho(pdf):
    pdf.set_font("Arial", "B", 14)
    pdf.set_xy(10, 10)
    pdf.cell(190, 10, "RELATÓRIO TÉCNICO", ln=True, align="C")

    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 8, "COMADO DAS BOMBAS", ln=True, align="C")

    pdf.set_font("Arial", size=10)
    pdf.cell(190, 6, "CNPJ: 10.448.503/0001-88", ln=True, align="C")
    pdf.cell(190, 6, "RUA DA CONCÓRDIA, 904 - SÃO JOSÉ - RECIFE - PE | CEP: 50020-055", ln=True, align="C")
    

    pdf.ln(10)

# STREAMLIT
st.set_page_config(page_title="Gerador de Relatório Técnico ", layout="centered")
st.title("📋 Gerador de Relatório Técnico ")

numero_os = st.text_input("Número da OS *")
cliente = st.text_input("Cliente *")
tipo_servico = st.text_area("Equipe Técnica *")
observacoes = st.text_area("Observações")
uploaded_files = st.file_uploader("📎 Adicionar Imagens (múltiplas)", accept_multiple_files=True)

st.subheader("✍️ Assinatura do Cliente")
canvas_result = st_canvas(
    fill_color="rgba(255, 255, 255, 1)",
    stroke_width=2,
    stroke_color="black",
    background_color="#eee",
    height=150,
    width=400,
    drawing_mode="freedraw",
    key="assinatura_canvas",
)

if st.button("📄 Gerar OS como PDF"):
    if not numero_os or not cliente or not tipo_servico:
        st.error("Por favor, preencha todos os campos obrigatórios marcados com *.") 
    elif canvas_result.image_data is None or np.all(canvas_result.image_data == 255):
        st.warning("Por favor, forneça uma assinatura válida.")
    elif not uploaded_files:
        st.warning("Por favor, adicione pelo menos uma imagem.")
    else:
        try:
            pdf = PDFComRodape()
            pdf.alias_nb_pages()
            pdf.set_auto_page_break(auto=True, margin=20)
            pdf.add_page()
            adicionar_cabecalho(pdf)

            pdf.set_font("Arial", size=12)
            margem_x = 10
            largura_total = 190

            pdf.set_x(margem_x)
            pdf.cell(w=largura_total, h=10, txt=f"Número da OS: {numero_os}", ln=True)
            pdf.set_x(margem_x)
            pdf.cell(w=largura_total, h=10, txt=f"Cliente: {cliente}", ln=True)

            pdf.set_font("Arial", "B", 12)
            pdf.set_x(margem_x)
            pdf.cell(w=largura_total, h=10, txt="Equipe Técnica:", ln=True)
            pdf.set_font("Arial", size=12)
            pdf.set_x(margem_x)
            pdf.multi_cell(w=largura_total, h=8, txt=tipo_servico)

            if observacoes.strip():
                pdf.ln(2)
                pdf.set_font("Arial", "B", 12)
                pdf.set_x(margem_x)
                pdf.cell(w=largura_total, h=10, txt="Observações:", ln=True)
                pdf.set_font("Arial", size=12)
                pdf.set_x(margem_x)
                pdf.multi_cell(w=largura_total, h=8, txt=observacoes)

            if pdf.get_y() > 240:
                pdf.add_page()
                adicionar_cabecalho(pdf)

            pdf.ln(5)
            pdf.set_font("Arial", "B", 12)
            pdf.set_x(margem_x)
            pdf.cell(w=largura_total, h=10, txt="Assinatura do Cliente:", ln=True)

            assinatura_array = canvas_result.image_data.astype(np.uint8)
            assinatura_pil = Image.fromarray(assinatura_array)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                assinatura_pil.save(tmpfile, format="PNG")
                assinatura_path = tmpfile.name

            y_pos = pdf.get_y()
            if y_pos + 40 > 280:
                pdf.add_page()
                adicionar_cabecalho(pdf)
                y_pos = pdf.get_y()

            pdf.image(assinatura_path, x=margem_x, y=y_pos, w=60)
            pdf.ln(50)

            pdf.set_font("Arial", "B", 12)
            pdf.set_x(margem_x)
            pdf.cell(w=largura_total, h=10, txt="Imagens do Serviço:", ln=True)

            for uploaded_file in uploaded_files:
                image = Image.open(uploaded_file)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img_file:
                    image.save(tmp_img_file, format="PNG")
                    image_path = tmp_img_file.name

                img_width, img_height = image.size
                max_width = 105  # Definindo largura máxima para as imagens (tamanho A6)
                ratio = max_width / img_width  # Calculando a proporção para ajustar a altura
                new_height = img_height * ratio

                # Verificando se a altura da imagem ultrapassa o limite da página
                if pdf.get_y() + new_height > 280:
                    pdf.add_page()
                    adicionar_cabecalho(pdf)

                pdf.image(image_path, x=15, y=pdf.get_y(), w=max_width)  # Ajusta a largura da imagem
                pdf.ln(new_height + 10)  # Deixa um espaço após a imagem

            pdf_output = BytesIO()
            pdf.output(pdf_output)
            pdf_output.seek(0)

            st.success("✅ Ordem de Serviço gerada com sucesso!")

            st.download_button(
                label="⬇️ Baixar OS como PDF",
                data=pdf_output,
                file_name=f"OS_{numero_os}.pdf",
                mime="application/pdf",
            )

        except Exception as e:
            st.error(f"Ocorreu um erro ao gerar a OS em PDF: {e}")
