import os
import io
import logging
from azure.storage.blob import BlobServiceClient
import pandas as pd

# Configura o logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def upload_dataframe_to_adls(df, connection_string, container_name, blob_name):
    """Converte um DataFrame para Parquet em memória e faz o upload para o Azure."""
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        try:
            container_client = blob_service_client.create_container(container_name)
            logging.info(f"Container '{container_name}' criado.")
        except Exception:
            container_client = blob_service_client.get_container_client(container_name)
            logging.info(f"Container '{container_name}' já existe.")

        output_buffer = io.BytesIO()
        df.to_parquet(output_buffer, index=True)
        output_buffer.seek(0)

        blob_client = container_client.get_blob_client(blob=blob_name)
        
        logging.info(f"Fazendo upload do resultado para: {blob_client.url}...")
        blob_client.upload_blob(output_buffer, overwrite=True)
        logging.info("Upload do resultado concluído com sucesso!")

    except Exception as e:
        logging.error(f"Ocorreu um erro durante o upload do resultado: {e}")
        raise e

def download_blob_to_dataframe(connection_string, container_name, blob_name):
    """Baixa um blob (arquivo) do Azure e o carrega em um DataFrame pandas."""
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

        logging.info(f"Baixando dados do blob: {blob_name} do container: {container_name}...")
        
        downloader = blob_client.download_blob()
        blob_bytes = downloader.readall()
        
        dataframe = pd.read_parquet(io.BytesIO(blob_bytes))
        
        logging.info("Download e carregamento para DataFrame concluídos com sucesso!")
        return dataframe

    except Exception as e:
        logging.error(f"Ocorreu um erro durante o download: {e}")
        return None