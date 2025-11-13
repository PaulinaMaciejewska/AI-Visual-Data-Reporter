import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()


class Config:
    
    VISION_ENDPOINT = os.getenv('VISION_ENDPOINT')
    VISION_KEY = os.getenv('VISION_KEY')
    OPENAI_ENDPOINT = os.getenv('OPENAI_ENDPOINT')
    OPENAI_KEY = os.getenv('OPENAI_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_DEPLOYMENT_NAME')
    OPENAI_API_VERSION = os.getenv('OPENAI_API_VERSION', "2024-02-15-preview")
    DOCUMENT_INTELLIGENCE_ENDPOINT = os.getenv('DOCUMENT_INTELLIGENCE_ENDPOINT')
    DOCUMENT_INTELLIGENCE_KEY = os.getenv('DOCUMENT_INTELLIGENCE_KEY')

    @staticmethod
    def validate_env_variables():
        missing = []
        for var in ['VISION_ENDPOINT', 'VISION_KEY', 'OPENAI_ENDPOINT', 'OPENAI_KEY', 'OPENAI_DEPLOYMENT_NAME']:
            if not os.getenv(var):
                missing.append(var)
        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

    @staticmethod
    def get_openai_client():
        return AzureOpenAI(
            azure_endpoint = Config.OPENAI_ENDPOINT, 
            api_key = Config.OPENAI_KEY,
            api_version = Config.OPENAI_API_VERSION
        )

    @staticmethod
    def get_vision_client():
        credentials = CognitiveServicesCredentials(Config.VISION_KEY)
        return ComputerVisionClient(
            endpoint = Config.VISION_ENDPOINT, 
            credentials = credentials
        )

    @staticmethod
    def get_document_intelligence_client():
        return DocumentIntelligenceClient(
        endpoint=Config.DOCUMENT_INTELLIGENCE_ENDPOINT, credential=AzureKeyCredential(Config.DOCUMENT_INTELLIGENCE_KEY)
    )
