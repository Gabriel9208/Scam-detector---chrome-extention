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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
    setRiskScore,
    loading,
    setLoading,
    error,
    setError
  }), [whoisInfo, tlsInfo, businessInfo, pageInfo, riskScore, loading, error]);

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
        <div className='content-container'>
          <GlobalProvider>
            <Result />
            <Analysis url={submitUrl}/>
            <Detail url={submitUrl}/>
          </GlobalProvider>
        </div>
      )}
    </main>
  )
}

export default Popup
