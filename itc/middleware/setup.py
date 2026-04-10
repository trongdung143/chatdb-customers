from dotenv import load_dotenv
import os

load_dotenv()


os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_TRACE"] = ""

DB_DRIVER = os.getenv("DB_DRIVER")
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_UID = os.getenv("DB_UID")
DB_PWD = os.getenv("DB_PWD")
AES_SALT = os.getenv("AES_SALT")
AES_IV = os.getenv("AES_IV")
AES_KEY = bytes.fromhex(os.getenv("AES_KEY"))
HMAC_KEY = bytes.fromhex(os.getenv("HMAC_KEY"))
DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING")

