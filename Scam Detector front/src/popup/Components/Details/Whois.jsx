import { useState, useEffect, useContext, useCallback } from 'react'
import { GlobalContext } from '../../Popup.jsx' // Adjust the import path as needed

import axios from 'axios';

export const Whois = ({ url }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { setWhoisInfo, whoisInfo } = useContext(GlobalContext);

  const fetchWhoisData = useCallback(async () => {
    if (!url) return;

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('http://localhost:8000/scam-detector/detail/whois/', {
        url: url,
      }, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const decodedData = Object.fromEntries(
        Object.entries(response.data).map(([key, value]) => [
          key,
          typeof value === 'string' ? decodeURIComponent(JSON.parse(`"${value}"`)) : value
        ])
      );

      setWhoisInfo(decodedData);
    } 
    catch (err) {
      setError(err.message);
      setWhoisInfo(null);
    } 
    finally {
      setLoading(false);
    }
  }, [url]);

  useEffect(() => {
    fetchWhoisData();
  }, [fetchWhoisData]);

  return (
    <div>
      <p style={{fontWeight: 'bold'}}>Whois data</p> 
      {loading ? (
        <div>Loading Whois data...</div>
      ) : error ? (
        <div>Error: {error}</div>
      ) : !whoisInfo ? (
        <span></span>
      ) : (
        Object.entries(whoisInfo).map(([key, value]) => (
          <div key={key}>
            <strong>{key}:</strong> {value}
          </div>
        ))
      )}
    </div>
  )
}
