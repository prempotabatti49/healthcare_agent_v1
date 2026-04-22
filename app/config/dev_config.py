# Kept for backward compatibility. New code should use app.config.settings.
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.DEBUG = True
        self.CONFIG_1 = "sqlite:///dev.db"
        self.CONFIG_2 = False
        self.SUPERMEMORY_KEY = os.environ.get("SUPERMEMORY_API_KEY", "")

    def __repr__(self):
        return f"<Config DEBUG={self.DEBUG}>"

    def supermemory_key(self) -> str:
        return self.SUPERMEMORY_KEY
