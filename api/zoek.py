from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import urllib.request
import json
import ssl

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

def zoek_documenten(zoekterm):
    url = "https://bodegraven-reeuwijk.qualigraf.nl/vji/public/search/action=doSearch"
    payload = {
        "text": zoekterm,
        "where": "",
        "categories": [],
        "commissions": [],
        "modules": [],
        "media": False,
        "onlyTitle": False,
        "party": [],
        "person": [],
        "documentTypes": [],
        "locations": [],
        "dates": {
            "from": "2023-01-01",
            "until": "2025-12-31"
        },
        "secties": "",
        "casecode": ""
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Referer": f"https://bodegraven-reeuwijk.qualigraf.nl/app/public/search?q={zoekterm.replace(' ', '%20')}"
    }
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE  # Disable SSL verification (use with caution)
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, context=ssl_context) as response:
            raw = response.read().decode("utf-8")
            result = json.loads(raw)

        if not isinstance(result, list) or not result:
            return []

        documenten = []
        for item in result:
            # Generate document URL if available in the response
            document_url = item.get('url', '')
            if not document_url and 'id' in item:
                document_url = f"https://bodegraven-reeuwijk.qualigraf.nl/document/{item['id']}"
                
            documenten.append({
                "title": item.get('title', ''),
                "date": item.get('date', ''),
                "party": item.get('party', ''),
                "type": item.get('type', ''),
                "document_url": document_url,
                "summary": item.get("description", "").replace("<strong>", ""),
                replace("</strong>", "")
            })
        return documenten
    except Exception as e:
        print(f"Error: {str(e)}")  # Add logging
        return {"error": str(e)}

@app.get("/zoek")
async def zoek(request: Request):
    term = request.query_params.get("term", "")
    if not term:
        return JSONResponse(content={"error": "No search term provided"})
    
    try:
        resultaat = zoek_documenten(term)
        return JSONResponse(content=resultaat)
    except Exception as e:
        print(f"API Error: {str(e)}")  # Add logging
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Add a root endpoint for testing
@app.get("/")
async def root():
    return {"message": "API is running. Use /zoek?term=your-search-term to search."}
