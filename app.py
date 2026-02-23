import streamlit as st
import pandas as pd
import os

# Configuração da página
st.set_page_config(page_title="Gerenciador de Patrimônio", layout="centered")

st.title("📦 Sistema de Etiquetas")

# 1. Instruções conforme a imagem
st.info("""
**Instruções:**
1. O arquivo `base_patrimonio.xlsx` deve estar na mesma pasta do repositório.
2. A busca/filtro é feita na Coluna B.
3. O relatório exportado contém as informações das Colunas B, C, E e F.
""")

# 2. Seleção do tipo de etiqueta
tipo_etiqueta = st.selectbox("Selecione o tipo de etiqueta:", ["Papel", "Metal"])

# 3. Processamento do Arquivo
arquivo_entrada = "base_patrimonio.xlsx"

if os.path.exists(arquivo_entrada):
    try:
        # Carrega o Excel
        df = pd.read_excel(arquivo_entrada)

        # Seleção das Colunas (B, C, E, F) - Índices 1, 2, 4, 5
        # Coluna B (1), C (2), E (4), F (5)
        df_filtrado = df.iloc[:, [1, 2, 4, 5]]

        st.success(f"Arquivo carregado com sucesso! Pronto para gerar etiqueta de **{tipo_etiqueta}**.")
        
        # Visualização prévia
        st.write("### Prévia dos dados (Colunas B, C, E, F):")
        st.dataframe(df_filtrado.head())

        # 4. Botão para Download do resultado
        # Transformamos o dataframe em um arquivo Excel na memória
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_filtrado.to_excel(writer, index=False, sheet_name='Relatorio')
        
        st.download_button(
            label=f"📥 Baixar Relatório de {tipo_etiqueta}",
            data=output.getvalue(),
            file_name=f"relatorio_{tipo_etiqueta.lower()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
else:
    st.error(f"⚠️ O arquivo `{arquivo_entrada}` não foi encontrado no repositório GitHub.")
    st.warning("Certifique-se de que o arquivo Excel foi enviado (upload) para a mesma pasta do app.py no GitHub.")
