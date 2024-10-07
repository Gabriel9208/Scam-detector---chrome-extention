import { useState, createContext, useMemo, useCallback, useEffect } from 'react'
import {Result} from './Components/Result.jsx'
import {Analysis} from './Components/Analysis.jsx'
import {Detail} from './Components/Detail.jsx'

import './SidePanel.css'

// result - easy, single line
// analysis - in 10 lines
// details - show each field result

export const GlobalContext = createContext();

const GlobalProvider = ({ children, url }) => {
  const [whoisInfo, setWhoisInfo] = useState(null);
  const [tlsInfo, setTlsInfo] = useState(null);
  const [businessInfo, setBusinessInfo] = useState(null);
  const [pageInfo, setPageInfo] = useState(null);
  const [riskScore, setRiskScore] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inPhishDB, setInPhishDB] = useState(false);

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
    inPhishDB,
    setInPhishDB,
    loading,
    setLoading,
    error,
    setError
  }), [whoisInfo, tlsInfo, businessInfo, pageInfo, riskScore, loading, error, inPhishDB]);

  // Reset all states when url changes
  useEffect(() => {
    setWhoisInfo(null);
    setTlsInfo(null);
    setBusinessInfo(null);
    setPageInfo(null);
    setRiskScore(0);
    setLoading(true);
    setError(null);
    setInPhishDB(false);
  }, [url]);

  return (
    <GlobalContext.Provider value={contextValue}>
      {children}
    </GlobalContext.Provider>
  );
};

export const SidePanel = () => {
  const [url, setUrl] = useState('');
  const [submitUrl, setSubmitUrl] = useState('');

  const handleSubmit = useCallback(() => {
    setSubmitUrl(url);
  }, [url]);

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
        <button onClick={handleSubmit}>Analyze</button>
      </div>
      {submitUrl && (
        <div className='content-container'>
          <GlobalProvider url={submitUrl}>
            <Result />
            <Analysis url={submitUrl}/>
            <Detail url={submitUrl}/>
          </GlobalProvider>
        </div>
      )}
    </main>
  )
}

export default SidePanel
