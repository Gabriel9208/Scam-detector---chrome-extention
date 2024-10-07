import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from typing import Optional
from pydantic import BaseModel
import json
import asyncio
import traceback

from Data.whoisInfo import searchWhois
from Data.TLS_check import fetchTlsCert
from Data.findbiz import findbiz
from Data.scraper import scraper

from Analysis.IsWellKnownCA import isTrustedCA
from Analysis.checkPhishDB import checkPhishDB

# Configure logging to a file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log',  # Log messages to a file named 'app.log'
    filemode='a'  # Append to the log file (use 'w' to overwrite)
)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Url(BaseModel):
    url: str
    
class FindBizRequest(BaseModel):
    url: str
    organizationName: Optional[str] = None
    
class CARequest(BaseModel):
    ca: str
    
class URLRequest(BaseModel):
    url: str
    

@app.post("/scam-detector/detail/whois/")
async def whois(url: Url):
    try:
        logging.info(f"Received WHOIS request for URL: {url.url}")
        result = searchWhois(url.url)
        return JSONResponse(content=json.loads(json.dumps(result, default=str)))
    except Exception as e:
        logging.error(f"Error in WHOIS endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": traceback.format_exc()}
        )


@app.post("/scam-detector/detail/findbiz/")
async def findBizRegistration(request: FindBizRequest):
    try:
        logging.info(f"Received FindBiz request for URL: {request.url} and Organization: {request.organizationName}")
        result = await asyncio.to_thread(findbiz, request.url, request.organizationName)
        if result == {}:
            logging.warning(f"No business registration found for {request.url}")
            raise HTTPException(status_code=404, detail="Business registration not found or reached the limit quota.")
        return JSONResponse(content=json.loads(json.dumps(result, default=str)))
    except Exception as e:
        logging.error(f"Error in FindBiz endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scam-detector/detail/tls/")
async def tls(url: Url):
    logging.info(f"Received TLS request for URL: {url.url}")
    result = await asyncio.to_thread(fetchTlsCert, url.url)
    return JSONResponse(content=json.loads(json.dumps(result, default=str)))  # Ensure JSON response


@app.post("/scam-detector/detail/web-content/")
async def web_content(url: Url):
    try:
        logging.info(f"Received Web Content request for URL: {url.url}")
        result = await asyncio.to_thread(scraper, url.url)
        if not result:
            logging.warning(f"No web content found for {url.url}")
            raise HTTPException(status_code=404, detail="Web content not found.")
        return JSONResponse(content=json.loads(json.dumps(result, default=str)))
    except Exception as e:
        logging.error(f"Error in Web Content endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scam-detector/analysis/ca/")
async def check_ca(request: CARequest):
    try:
        logging.info(f"Received CA: /{request.ca}/")
        result = await asyncio.to_thread(isTrustedCA, request.ca)
        logging.info(f"CA No HTTPException: {result}")
        return JSONResponse(content={"result": result})  # Ensure JSON response
    except HTTPException as http_exc:
        logging.info(f"CA HTTPException: {http_exc}")
        raise http_exc
    except Exception as e:
        logging.info(f"CA Exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    
@app.post("/scam-detector/analysis/phish/")
async def check_phish(request: URLRequest):
    try:
        logging.info(f"Received PhishDB request for URL: {request.url}")
        result = await asyncio.to_thread(checkPhishDB, request.url)
        return JSONResponse(content={"result": result})  # Ensure JSON response
    except HTTPException as http_exc:
        logging.info(f"PhishDB HTTPException: {http_exc}")
        raise http_exc
    except Exception as e:
        logging.info(f"PhishDB Exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))