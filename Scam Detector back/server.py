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
from Data.TLSCheck import fetchTlsCert
from Data.findbiz import findbiz
from Data.scraper import scraper
from Data.fakeDomain import fakeDomainDetection

from Analysis.IsWellKnownCA import isTrustedCA
from Analysis.checkPhishDB import checkPhishDB

from asyncio import TimeoutError

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
    
class FakeDomainRequest(BaseModel):
    url: str
    source: str

@app.post("/scam-detector/detail/whois/")
async def whois(url: Url):
    try:
        logging.info(f"Received WHOIS request for URL: {url.url}")
        result = await asyncio.wait_for(
            asyncio.to_thread(searchWhois, url.url),
            timeout=7.0
        )
        return JSONResponse(content=json.loads(json.dumps(result, default=str)))
    except TimeoutError:
        logging.warning(f"WHOIS request timed out for URL: {url.url}")
        return JSONResponse(content={"error": "Timeout"})
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
        result = await asyncio.wait_for(
            asyncio.to_thread(findbiz, request.url, request.organizationName),
            timeout=7.0
        )
        if result == {}:
            logging.warning(f"No business registration found for {request.url}")
            raise HTTPException(status_code=404, detail="Business registration not found or reached the limit quota.")
        return JSONResponse(content=json.loads(json.dumps(result, default=str)))
    except TimeoutError:
        logging.warning(f"FindBiz request timed out for URL: {request.url}")
        return JSONResponse(content={"error": "Timeout"})
    except Exception as e:
        logging.error(f"Error in FindBiz endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scam-detector/detail/tls/")
async def tls(url: Url):
    try:
        logging.info(f"Received TLS request for URL: {url.url}")
        result = await asyncio.wait_for(
            asyncio.to_thread(fetchTlsCert, url.url),
            timeout=7.0
        )
        return JSONResponse(content=json.loads(json.dumps(result, default=str)))  # Ensure JSON response
    except TimeoutError:
        logging.warning(f"TLS request timed out for URL: {url.url}")
        return JSONResponse(content={"error": "Timeout"})
    except Exception as e:
        logging.error(f"Error in TLS endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scam-detector/detail/web-content/")
async def web_content(url: Url):
    try:
        logging.info(f"Received Web Content request for URL: {url.url}")
        result = await asyncio.wait_for(
            asyncio.to_thread(scraper, url.url),
            timeout=7.0
        )
        if not result:
            result = {}
        return JSONResponse(content=json.loads(json.dumps(result, default=str)))
    except TimeoutError:
        logging.warning(f"Web Content request timed out for URL: {url.url}")
        return JSONResponse(content={"error": "Timeout"})
    except Exception as e:
        logging.error(f"Error in Web Content endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scam-detector/detail/fake-domain/")
async def check_fake_domain(request: FakeDomainRequest):
    try:
        logging.info(f"Received Fake Domain request for URL: {request.url} and Source: {request.source}")
        result = await asyncio.wait_for(
            asyncio.to_thread(fakeDomainDetection, request.url, request.source),
            timeout=7.0
        )
        return JSONResponse(content={"result": result}) 
    except TimeoutError:
        logging.warning(f"Fake Domain request timed out for URL: {request.url}")
        return JSONResponse(content={"error": "Timeout"})
    except Exception as e:
        logging.error(f"Error in Fake Domain endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scam-detector/analysis/ca/")
async def check_ca(request: CARequest):
    try:
        logging.info(f"Received CA: /{request.ca}/")
        result = await asyncio.wait_for(
            asyncio.to_thread(isTrustedCA, request.ca),
            timeout=7.0
        )
        logging.info(f"CA No HTTPException: {result}")
        return JSONResponse(content={"result": result})  # Ensure JSON response
    except TimeoutError:
        logging.warning(f"CA request timed out for CA: {request.ca}")
        return JSONResponse(content={"error": "Timeout"})
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
        result = await asyncio.wait_for(
            asyncio.to_thread(checkPhishDB, request.url),
            timeout=7.0
        )
        return JSONResponse(content={"result": result})  # Ensure JSON response
    except TimeoutError:
        logging.warning(f"PhishDB request timed out for URL: {request.url}")
        return JSONResponse(content={"error": "Timeout"})
    except HTTPException as http_exc:
        logging.info(f"PhishDB HTTPException: {http_exc}")
        raise http_exc
    except Exception as e:
        logging.info(f"PhishDB Exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

