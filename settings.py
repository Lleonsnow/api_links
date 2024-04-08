from pydantic_settings import BaseSettings
from pydantic import SecretStr
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    TOKEN: SecretStr = os.getenv("token", None)
