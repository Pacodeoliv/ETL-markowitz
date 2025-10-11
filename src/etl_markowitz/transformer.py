# src/etl_markowitz/transformer.py

import os
import pandas as pd
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
import io

from pypfopt import expected_returns
from pypfopt import risk_models
from pypfopt import EfficientFrontier

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configurações ---
AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
RAW_CONTAINER_NAME = "raw"
PROCESSED_CONTAINER_NAME = "processed" # Novo container para os resultados
RAW_BLOB_NAME = "raw_stock_prices.parquet"

# --- Funções ---
def download_blob_to_dataframe(connection_string, container_name, blob_name):
    """Baixa um blob (arquivo) do Azure e o carrega em um DataFrame pandas."""
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        print(f"Baixando dados do blob: {blob_name} do container: {container_name}...")
        downloader = blob_client.download_blob()
        blob_bytes = downloader.readall()
        dataframe = pd.read_parquet(io.BytesIO(blob_bytes))
        print("Download concluído com sucesso!")
        return dataframe
    except Exception as e:
        print(f"Ocorreu um erro durante o download: {e}")
        return None

def optimize_portfolio(price_data):
    """Calcula o portfólio ótimo (Máximo Sharpe Ratio) a partir dos dados de preço."""
    print("\nIniciando otimização do portfólio...")
    mu = expected_returns.mean_historical_return(price_data)
    S = risk_models.sample_cov(price_data)
    ef = EfficientFrontier(mu, S)
    weights = ef.max_sharpe()
    cleaned_weights = ef.clean_weights()
    print("Otimização concluída!")
    
    expected_return, annual_volatility, sharpe_ratio = ef.portfolio_performance(verbose=False)
    
    weights_df = pd.DataFrame.from_records(
        list(cleaned_weights.items()), columns=['Ativo', 'Peso']
    ).set_index('Ativo')
    
    performance_df = pd.DataFrame({
        'Métrica': ['Retorno Anual Esperado', 'Volatilidade Anual', 'Índice de Sharpe'],
        'Valor': [expected_return, annual_volatility, sharpe_ratio]
    }).set_index('Métrica')
    
    return weights_df, performance_df

# --- NOVA FUNÇÃO DE UPLOAD DE DATAFRAME ---
def upload_dataframe_to_adls(df, connection_string, container_name, blob_name):
    """Converte um DataFrame para Parquet em memória e faz o upload para o Azure."""
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        try:
            container_client = blob_service_client.create_container(container_name)
            print(f"Container '{container_name}' criado.")
        except Exception as e:
            container_client = blob_service_client.get_container_client(container_name)
            print(f"Container '{container_name}' já existe.")

        output_buffer = io.BytesIO()
        df.to_parquet(output_buffer, index=True)
        output_buffer.seek(0)

        blob_client = container_client.get_blob_client(blob=blob_name)
        
        print(f"Fazendo upload do resultado para: {blob_client.url}...")
        blob_client.upload_blob(output_buffer, overwrite=True)
        print("Upload do resultado concluído com sucesso!")

    except Exception as e:
        print(f"Ocorreu um erro durante o upload do resultado: {e}")

# --- Execução Principal ---
if __name__ == "__main__":
    if AZURE_CONNECTION_STRING:
        price_data = download_blob_to_dataframe(AZURE_CONNECTION_STRING, RAW_CONTAINER_NAME, RAW_BLOB_NAME)
        
        if price_data is not None:
            optimal_weights, portfolio_performance = optimize_portfolio(price_data)
            
            print("\n--- Pesos Ótimos do Portfólio ---")
            print(optimal_weights)
            
            print("\n--- Performance Esperada do Portfólio ---")
            print(portfolio_performance)
            
            # 3. Fazer o upload dos resultados de volta para o Azure
            upload_dataframe_to_adls(optimal_weights, AZURE_CONNECTION_STRING, PROCESSED_CONTAINER_NAME, "optimized_weights.parquet")
            upload_dataframe_to_adls(portfolio_performance, AZURE_CONNECTION_STRING, PROCESSED_CONTAINER_NAME, "portfolio_performance.parquet")
            
    else:
        print("A variável de ambiente AZURE_STORAGE_CONNECTION_STRING não foi encontrada.")