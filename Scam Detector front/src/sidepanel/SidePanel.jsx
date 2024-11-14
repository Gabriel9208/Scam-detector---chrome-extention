import { useState, useContext, useCallback, useEffect } from 'react'
import {Result} from './Components/Result.jsx'
import {Analysis} from './Components/Analysis.jsx'
import {Detail} from './Components/Detail.jsx'
import './SidePanel.css'
import { GlobalContext } from './GlobalProvider.jsx'

export const SidePanel = () => {
  const [url, setUrl] = useState('');
  const [submitUrl, setSubmitUrl] = useState('');
  const [showThreshold, setShowThreshold] = useState(false);

  // Access setThreshold and threshold from GlobalContext
  const { threshold, setThreshold, setWhoisInfo, setTlsInfo, setBusinessInfo, setPageInfo, 
                      setRiskScore, setLoading, setError, setInPhishDB } = useContext(GlobalContext);

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

  const handleSubmit = useCallback(() => {
    setSubmitUrl(url);
  }, [url]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  }, [handleSubmit]); 


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
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <div className='toggle-section'>
          <div className='toggle-header' onClick={() => setShowThreshold(!showThreshold)}>
            <span className={`toggle-icon ${showThreshold ? 'open' : ''}`}>▶</span>
            <span>嚴謹度調整</span>
          </div>
          {showThreshold && (
            <div className='toggle-content threshold-container'>
              <p style={{color: '#a7a7a7'}}>預設嚴謹度在普遍情況下最為合適，但您可以根據實際需求調整。</p>
              <input 
                type="radio" 
                name="threshold" 
                value={0.5} 
                checked={threshold === 0.5}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
              />
              <label>嚴謹</label>
              <input 
                type="radio" 
                name="threshold" 
                value={1} 
                checked={threshold === 1}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
              />
              <label>預設</label>
              <input 
                type="radio" 
                name="threshold" 
                value={1.5} 
                checked={threshold === 1.5}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
              />              
              <label>寬鬆</label>
            </div>
          )}
        </div>
      </div>
      {submitUrl && (
        <div className='content-container'>
            <Result />
            <Analysis url={submitUrl}/>
            <Detail url={submitUrl}/>
        </div>
      )}
    </main>
  )
}

export default SidePanel;
