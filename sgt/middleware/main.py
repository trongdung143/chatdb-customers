from fastapi import FastAPI, HTTPException, Request
from crypto import decrypt, verify, encrypt, sign
from sql_service import SQLService
from conn_db import Database
from utils import dataframe_to_json
import os
import json
import time
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = Database()
    app.state.db = db
    yield
    await db.engine.dispose()


app = FastAPI(lifespan=lifespan)


@app.post("/query/v1")
async def query_api(body: dict, request: Request):
    endpoint = "query/v1"
    db = request.app.state.db
    sql_service = SQLService(db)
    encrypted_data = body.get("data")
    signature = body.get("signature")
    timestamp = body.get("timestamp")
    nonce = body.get("nonce")

    if not all([encrypted_data, signature, timestamp, nonce]):
        raise HTTPException(status_code=400, detail="Missing fields")

    now = int(time.time())
    if abs(now - int(timestamp)) > 15:
        raise HTTPException(status_code=403, detail="Request expired")

    if not verify(encrypted_data, timestamp, nonce, endpoint, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        sql = decrypt(encrypted_data)
    except Exception as decrypt_err:
        raise HTTPException(
            status_code=400, detail=f"Decrypt failed: {repr(decrypt_err)}"
        )

    if not sql.strip().lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Only SELECT allowed")

    print("SQL:", sql)

    try:
        df = await sql_service.execute(sql)
    except Exception as sql_err:
        print(sql_err)
        raise HTTPException(
            status_code=500, detail=f"SQL execution failed: {repr(sql_err)}"
        )

    result = dataframe_to_json(df)
    result_json = json.dumps(result)

    encrypted_response = encrypt(result_json)
    res_timestamp = int(time.time())
    res_nonce = os.urandom(8).hex()
    response_signature = sign(encrypted_response, res_timestamp, res_nonce, endpoint)

    return {
        "data": encrypted_response,
        "timestamp": res_timestamp,
        "nonce": res_nonce,
        "signature": response_signature,
    }
