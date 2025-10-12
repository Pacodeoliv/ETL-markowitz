import yfinance as yf
import pandas as pd
import logging
import os
from dotenv import load_dotenv
from . import settings 
from . import azure_connector 

load_dotenv()

# Configura o logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Obtém a connection string das variáveis de ambiente
AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

def fetch_stock_data(tickers, start_date, end_date):
    """Busca os dados históricos de preços de fechamento."""
    logging.info(f"Buscando dados para {len(tickers)} ativos...") 
    data = yf.download(tickers, start=start_date, end=end_date)['Close']
    data.dropna(inplace=True)
    logging.info("Dados extraídos com sucesso!") 
    return data

def run_extraction(): 
    """
    Executa o pipeline de extração completo:
    1. Busca dados da API yfinance.
    2. Faz o upload para a Zona Bruta do Azure Data Lake.
    """
    if not AZURE_CONNECTION_STRING:
        logging.error("A variável de ambiente AZURE_STORAGE_CONNECTION_STRING não foi encontrada.") 
        return

    # 1. Extração
    price_data = fetch_stock_data(settings.TICKERS, settings.START_DATE, settings.END_DATE) 
    
    # 2. Carregamento para a Nuvem
    azure_connector.upload_dataframe_to_adls( 
        df=price_data,
        connection_string=AZURE_CONNECTION_STRING,
        container_name=settings.RAW_CONTAINER_NAME, 
        blob_name=settings.RAW_BLOB_NAME 
    )


if __name__ == "__main__":
    run_extraction()