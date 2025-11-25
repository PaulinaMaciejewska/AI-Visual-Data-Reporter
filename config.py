import os
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials

_env_file = Path(__file__).parent / '.env'
if _env_file.exists():
    load_dotenv(_env_file)
else:
    load_dotenv(Path(__file__).parent.parent / '.env')

class Config:
    _openai_client = None
    _vision_client = None
    
    VISION_ENDPOINT = os.getenv('VISION_ENDPOINT')
    VISION_KEY = os.getenv('VISION_KEY')
    OPENAI_ENDPOINT = os.getenv('OPENAI_ENDPOINT')
    OPENAI_KEY = os.getenv('OPENAI_KEY')
    OPENAI_DEPLOYMENT_NAME = os.getenv('OPENAI_DEPLOYMENT_NAME')
    OPENAI_API_VERSION = os.getenv('OPENAI_API_VERSION', "2024-08-01-preview")
    
    @staticmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.validate_env_variables()
        
    @staticmethod
    def validate_env_variables():
        missing = []
        for var in ['VISION_ENDPOINT', 'VISION_KEY', 'OPENAI_ENDPOINT', 'OPENAI_KEY', 'OPENAI_DEPLOYMENT_NAME', 'OPENAI_DEPLOYMENT_NAME']:
            if not os.getenv(var):
                missing.append(var)
        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

    @staticmethod
    def get_openai_client():
        if Config._openai_client is None:
            Config._openai_client = AzureOpenAI(
            azure_endpoint = Config.OPENAI_ENDPOINT, 
            api_key = Config.OPENAI_KEY,
            api_version = Config.OPENAI_API_VERSION
        )
        return Config._openai_client

    @staticmethod
    def get_vision_client():
        if Config._vision_client is None:
            credentials = CognitiveServicesCredentials(Config.VISION_KEY)
            Config._vision_client = ComputerVisionClient(
            endpoint = Config.VISION_ENDPOINT, 
            credentials = credentials
        )
        return Config._vision_client