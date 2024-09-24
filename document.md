# Scam Detector Documentation

## Overview

Scam Detector is a Chrome extension tool built with Vite, React, and Manifest v3. It provides various functionalities to detect potential scams by analyzing URLs for WHOIS information, TLS certificates, business registrations, and web content.

## Table of Contents

1. [Installation](##installation)
2. [Development](##development)
3. [Usage](##usage)
4. [API Endpoints](##api-endpoints)
5. [Components](#api-endpointscomponents)
6. [Configuration](##configuration)
7. [Testing](##testing)
8. [Building and Packaging](##building-and-packaging)
9. [License](##license)

## Installation

To install the Scam Detector app, follow these steps:

1. Ensure your `Node.js` version is >= **14**.
2. Configure the name of your extension in `src/manifest.js`.
3. Run `npm install` to install the dependencies.

```shell
$ cd scam-detector
$ npm install
```

## Development

To start the development server, run:

```shell
$ npm run dev
```

### Chrome Extension Developer Mode

1. Enable 'Developer mode' in your Chrome browser.
2. Click 'Load unpacked' and select the `scam-detector/build` folder.

### Normal FrontEnd Developer Mode

1. Access `http://0.0.0.0:3000/`.
2. For debugging the popup page, open `http://0.0.0.0:3000/popup.html`.
3. For debugging the options page, open `http://0.0.0.0:3000/options.html`.

## Usage

### Popup Interface

The popup interface allows users to enter a URL and analyze it for potential scams. It provides detailed information on WHOIS data, TLS certificates, business registration, and web content.

### Side Panel

The side panel displays synchronized data from the popup and provides additional insights.

## API Endpoints

The backend server provides several API endpoints to fetch data:

### WHOIS Information

```http
POST /scam-detector/detail/whois/
```

**Request Body:**

```json
{
  "url": "http://example.com"
}
```

**Response:**

Returns WHOIS information for the given URL.

### Business Registration

```http
POST /scam-detector/detail/findbiz/
```

**Request Body:**

```json
{
  "url": "http://example.com",
  "organizationName": "Example Org"
}
```

**Response:**

Returns business registration information for the given URL and organization name.

### TLS Certificate

```http
POST /scam-detector/detail/tls/
```

**Request Body:**

```json
{
  "url": "http://example.com"
}
```

**Response:**

Returns TLS certificate information for the given URL.

### Web Content

```http
POST /scam-detector/detail/web-content/
```

**Request Body:**

```json
{
  "url": "http://example.com"
}
```

**Response:**

Returns web content information for the given URL.

### Certificate Authority Check

```http
POST /scam-detector/analysis/ca/
```

**Request Body:**

```json
{
  "ca": "Example CA"
}
```

**Response:**

Returns whether the given Certificate Authority is trusted.

## Components

### Frontend Components

- **Popup**: The main component for the popup interface.
  
```1:89:front/src/popup/Popup.jsx
import { useState, createContext, useMemo } from 'react'
import {Result} from './Components/Result.jsx'
import {Analysis} from './Components/Analysis.jsx'
import {Detail} from './Components/Detail.jsx'

import './Popup.css'

// result - easy, single line
// analysis - in 10 lines
// details - show each field result

export const GlobalContext = createContext();

const GlobalProvider = ({ children }) => {
  const [whoisInfo, setWhoisInfo] = useState(null);
  const [tlsInfo, setTlsInfo] = useState(null);
  const [businessInfo, setBusinessInfo] = useState(null);
  const [pageInfo, setPageInfo] = useState(null);
  const [riskScore, setRiskScore] = useState(0);

  const contextValue = useMemo(() => ({
    whoisInfo,
    setWhoisInfo,
    tlsInfo,
    setTlsInfo,
    businessInfo,
    setBusinessInfo,
    pageInfo,
    setPageInfo,
    riskScore,
    setRiskScore
  }), [whoisInfo, tlsInfo, businessInfo, pageInfo, riskScore]);

  return (
    <GlobalContext.Provider value={contextValue}>
      {children}
    </GlobalContext.Provider>
  );
};

export const Popup = () => {
  

  const [url, setUrl] = useState('');
  const [submitUrl, setSubmitUrl] = useState('');

  /* Feature: Default to current tab's URL
  
  // Function to get the current tab's URL
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0] && tabs[0].url) {
      setSubmitUrl(tabs[0].url);
    }
  });
  
  // detect url change
  chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.active && tab.url) {
      setSubmitUrl(tab.url);
    }
  });

  */

  return (
    <main>
      <div className='header-container'>
        <h1>Scam Detector</h1>
      </div>
      <div className='input-container'>
        <input 
          type="text" 
          placeholder="Enter URL" 
          value={url}
          onChange={(e) => setUrl(e.target.value)}/>
        <button onClick={() => setSubmitUrl(url)}>Analyze</button>
      </div>
      {submitUrl && (
        <div className='result-container'>
          <GlobalProvider>
            <Result />
            <Analysis />
            <Detail url={submitUrl}/>
          </GlobalProvider>
        </div>
      )}
    </main>
  )
}
```


- **SidePanel**: The main component for the side panel interface.
  
```1:32:front/src/sidepanel/SidePanel.jsx
import { useState, useEffect } from 'react'

import './SidePanel.css'

export const SidePanel = () => {
  const [countSync, setCountSync] = useState(0)
  const link = 'https://github.com/guocaoyi/create-chrome-ext'

  useEffect(() => {
    chrome.storage.sync.get(['count'], (result) => {
      setCountSync(result.count || 0)
    })

    chrome.runtime.onMessage.addListener((request) => {
      if (request.type === 'COUNT') {
        setCountSync(request.count || 0)
      }
    })
  }, [])

  return (
    <main>
      <h3>SidePanel Page</h3>
      <h4>Count from Popup: {countSync}</h4>
      <a href={link} target="_blank">
        generated by create-chrome-ext
      </a>
    </main>
  )
}

export default SidePanel
```


- **DevTools**: The main component for the developer tools interface.
  
```1:16:front/src/devtools/DevTools.jsx
import './DevTools.css'

export const DevTools = () => {
  const link = 'https://github.com/guocaoyi/create-chrome-ext'

  return (
    <main>
      <h3>DevTools Page</h3>
      <a href={link} target="_blank">
        generated by create-chrome-ext
      </a>
    </main>
  )
}

export default DevTools
```


### Backend Endpoints

- **WHOIS Endpoint**: Fetches WHOIS information.
  
```37:40:back/server.py
@app.post("/scam-detector/detail/whois/")
async def whois(url: Url):
    result = searchWhois(url.url)
    return json.dumps(result)
```


- **Business Registration Endpoint**: Fetches business registration information.
  
```42:47:back/server.py
@app.post("/scam-detector/detail/findbiz/")
async def findBizRegistration(request: FindBizRequest):
    result = await asyncio.to_thread(findbiz, request.url, request.organizationName)
    if result == {}:
        raise HTTPException(status_code=404, detail="Business registration not found or reach the limit quota.")
    return JSONResponse(content=json.loads(json.dumps(result, default=str)))
```


- **TLS Certificate Endpoint**: Fetches TLS certificate information.
  
```49:52:back/server.py
@app.post("/scam-detector/detail/tls/")
async def tls(url: Url):
    result = await asyncio.to_thread(fetchTlsCert, url.url)
    return json.dumps(result)
```


- **Web Content Endpoint**: Fetches web content information.
  
```54:57:back/server.py
@app.post("/scam-detector/detail/web-content/")
async def web_content(url: Url):
    result = await asyncio.to_thread(scraper, url.url)
    return json.dumps(result)
```


- **Certificate Authority Check Endpoint**: Checks if a Certificate Authority is trusted.
  
```59:67:back/server.py
@app.post("/scam-detector/analysis/ca/")
async def check_ca(request: CARequest):
    try:
        result = isTrustedCA(request.ca)
        return result
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```


## Configuration

### Manifest Configuration

The `src/manifest.js` file contains the configuration for the Chrome extension.


```1:52:front/src/manifest.js
import { defineManifest } from '@crxjs/vite-plugin'
import packageData from '../package.json' assert { type: 'json' }

const isDev = process.env.NODE_ENV == 'development'

export default defineManifest({
  name: `${packageData.displayName || packageData.name}${isDev ? ` ➡️ Dev` : ''}`,
  description: packageData.description,
  version: packageData.version,
  manifest_version: 3,
  icons: {
    16: 'img/logo-16.png',
    32: 'img/logo-34.png',
    48: 'img/logo-48.png',
    128: 'img/logo-128.png',
  },
  action: {
    default_popup: 'popup.html',
    default_icon: 'img/logo-48.png',
  },
  options_page: 'options.html',
  devtools_page: 'devtools.html',
  background: {
    service_worker: 'src/background/index.js',
    type: 'module',
  },
  content_scripts: [
    {
      matches: ['http://*/*', 'https://*/*'],
      js: ['src/contentScript/index.js'],
    },
  ],
  side_panel: {
    default_path: 'sidepanel.html',
  },
  web_accessible_resources: [
    {
      resources: ['img/logo-16.png', 'img/logo-34.png', 'img/logo-48.png', 'img/logo-128.png'],
      matches: [],
    },
  ],
  permissions: ['sidePanel', 
                'storage', 
                'webRequest'
  ],
  host_permissions: [
    '<all_urls>'
  ],
  chrome_url_overrides: {
    newtab: 'newtab.html',
  }
})
```


### Environment Variables

Ensure to set up your environment variables correctly. Refer to `.env.example` for the required variables.

## Testing

To run tests, use the following command:

```shell
$ npm run test
```

The test configuration is defined in `jest.config.mjs`.


```1:7:front/jest.config.mjs
export default {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['@testing-library/jest-dom'],
  transform: {
    '^.+\\.(js|jsx)$': 'babel-jest',
  },
};
```


## Building and Packaging

To build the extension for production, run:

```shell
$ npm run build
```

After building, the content of the `build` folder will be the extension ready to be submitted to the Chrome Web Store.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.


```1:22:front/LICENSE
The MIT License (MIT)

Copyright (c) 2024-present, Gabrieee

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

```
