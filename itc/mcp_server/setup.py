from dotenv import load_dotenv
import os

load_dotenv()


os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_TRACE"] = ""
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
