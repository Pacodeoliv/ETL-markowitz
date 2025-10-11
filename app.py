# app.py

import streamlit as st
import pandas as pd
import os
import io
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
import plotly.express as px

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configurações do Azure ---
AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
PROCESSED_CONTAINER_NAME = "processed"

# --- Otimização de Performance com Cache do Streamlit ---
# O decorator @st.cache_data diz ao Streamlit para não re-executar esta função
# a menos que os argumentos mudem. Isso evita baixar os dados do Azure toda vez
# que o usuário interage com o dashboard, tornando-o muito mais rápido.
@st.cache_data
def load_data_from_azure(connection_string, container_name):
    """
    Conecta-se ao Azure, baixa os dois arquivos de resultado da pasta 'processed'
    e os retorna como DataFrames.
    """
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Baixar os pesos otimizados
        weights_blob_client = blob_service_client.get_blob_client(container=container_name, blob="optimized_weights.parquet")
        weights_downloader = weights_blob_client.download_blob()
        weights_bytes = weights_downloader.readall()
        weights_df = pd.read_parquet(io.BytesIO(weights_bytes))

        # Baixar a performance do portfólio
        performance_blob_client = blob_service_client.get_blob_client(container=container_name, blob="portfolio_performance.parquet")
        performance_downloader = performance_blob_client.download_blob()
        performance_bytes = performance_downloader.readall()
        performance_df = pd.read_parquet(io.BytesIO(performance_bytes))

        print("Dados carregados do Azure com sucesso!")
        return weights_df, performance_df

    except Exception as e:
        st.error(f"Erro ao carregar dados do Azure: {e}")
        return None, None

# --- Construção da Interface do Dashboard ---

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Otimização de Portfólio",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título do Dashboard
st.title("📈 Dashboard de Otimização de Portfólio de Markowitz")
st.markdown("Este dashboard apresenta o resultado de um pipeline de ETL que calcula a alocação ótima de ativos segundo a Teoria de Markowitz.")

# Carregar os dados
weights_df, performance_df = load_data_from_azure(AZURE_CONNECTION_STRING, PROCESSED_CONTAINER_NAME)

# Se os dados foram carregados com sucesso, exibe o dashboard
if weights_df is not None and performance_df is not None:
    
    st.header("Performance Esperada do Portfólio Otimizado")
    
    # Exibir as métricas de performance em cards
    col1, col2, col3 = st.columns(3)
    
    # Extrai os valores do DataFrame de performance
    retorno_anual = performance_df.loc['Retorno Anual Esperado']['Valor']
    volatilidade_anual = performance_df.loc['Volatilidade Anual']['Valor']
    sharpe_ratio = performance_df.loc['Índice de Sharpe']['Valor']

    col1.metric("Retorno Anual Esperado", f"{retorno_anual:.2%}")
    col2.metric("Volatilidade Anual", f"{volatilidade_anual:.2%}")
    col3.metric("Índice de Sharpe", f"{sharpe_ratio:.2f}")

    st.header("Alocação de Ativos Recomendada")

    col1_chart, col2_table = st.columns([2, 1]) # Coluna do gráfico maior que a da tabela

    with col1_chart:
        # Gráfico de Pizza com a alocação dos ativos
        fig = px.pie(
            weights_df, 
            names=weights_df.index, 
            values='Peso', 
            title='Distribuição de Pesos no Portfólio',
            hole=.3 # Para criar um gráfico de "rosca"
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2_table:
        # Tabela com os pesos
        st.dataframe(
            weights_df.style.format({'Peso': '{:.2%}'}),
            use_container_width=True
        )

else:
    st.warning("Não foi possível carregar os dados do Azure. Verifique a conexão e as configurações.")