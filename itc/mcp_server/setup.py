from dotenv import load_dotenv
import os

load_dotenv()


os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_TRACE"] = ""
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_UID = os.getenv("DB_UID")
DB_PWD = os.getenv("DB_PWD")
DB_DRIVER = os.getenv("DB_DRIVER")
