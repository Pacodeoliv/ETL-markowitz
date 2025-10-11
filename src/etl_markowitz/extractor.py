# ETL-markowitz/etl_markowitz/extractor.py

import yfinance as yf
import pandas as pd
from datetime import datetime
import os # Importamos a biblioteca 'os' para lidar com caminhos de arquivos
from dotenv import load_dotenv  # Nova importação
from azure.storage.blob import BlobServiceClient # Nova importação

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configurações Iniciais ---
TICKERS = [
    "AAPL", "MSFT", "JPM", "PG", "XOM", 
    "MGLU3.SA", "PETR4.SA"
]
START_DATE = "2020-01-01"
END_DATE = datetime.now().strftime('%Y-%m-%d')
OUTPUT_DIR = "data" # Nome da pasta onde salvaremos os dados
FILE_NAME = "raw_stock_prices.parquet" # Nome do nosso arquivo de saída

# Configurações do Azure
AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = "raw"  # Vamos criar um 'container' chamado 'raw' para os dados brutos
LOCAL_FILE_PATH = "data/raw_stock_prices.parquet"


# --- Funções do ETL ---
def fetch_stock_data(tickers, start_date, end_date):
    """Busca os dados históricos de preços de fechamento ajustado."""
    print(f"Buscando dados para {len(tickers)} ativos...")
    data = yf.download(tickers, start=start_date, end=end_date)['Close']
    data.dropna(inplace=True)
    print("Dados extraídos com sucesso!")
    return data


def save_to_parquet_local(df, file_path):
    # (Esta função agora só salva o arquivo localmente)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    print(f"Salvando arquivo localmente em {file_path}...")
    df.to_parquet(file_path)
    print("Arquivo salvo localmente!")

# NOVA FUNÇÃO DE UPLOAD
def upload_to_adls(connection_string, container_name, file_path):
    """Faz o upload de um arquivo local para o Azure Data Lake Storage."""
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Cria o container se ele não existir
        try:
            container_client = blob_service_client.create_container(container_name)
            print(f"Container '{container_name}' criado.")
        except Exception as e:
            # Se o container já existe, apenas o obtemos
            container_client = blob_service_client.get_container_client(container_name)
            print(f"Container '{container_name}' já existe.")

        blob_client = container_client.get_blob_client(blob=os.path.basename(file_path))

        print(f"Fazendo upload do arquivo para o Azure Data Lake: {blob_client.url}...")
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        print("Upload concluído com sucesso!")

    except Exception as e:
        print(f"Ocorreu um erro durante o upload: {e}")
 
 
 # --- Execução Principal ---
if __name__ == "__main__":
    # 1. Extração
    price_data = fetch_stock_data(TICKERS, START_DATE, END_DATE)
    
    # 2. Salvamento local
    save_to_parquet_local(price_data, LOCAL_FILE_PATH)
    
    # --- ADICIONE AS LINHAS ABAIXO PARA VERIFICAR ---
    print("\n--- Verificando a Connection String ---")
    print(f"Valor lido do .env: '{AZURE_CONNECTION_STRING}'")
    print("Certifique-se de que o valor acima começa com 'DefaultEndpointsProtocol=https;...'")
    print("--------------------------------------\n")
    # -----------------------------------------------

    # 3. Carregamento (Upload) para a Nuvem
    if AZURE_CONNECTION_STRING:
        upload_to_adls(AZURE_CONNECTION_STRING, CONTAINER_NAME, LOCAL_FILE_PATH)
    else:
        print("A variável de ambiente AZURE_STORAGE_CONNECTION_STRING não foi encontrada.")
        print("Certifique-se de que seu arquivo .env está configurado corretamente.")