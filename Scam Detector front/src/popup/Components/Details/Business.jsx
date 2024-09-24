import { useState, useEffect, useContext, useCallback } from 'react'
import { GlobalContext } from '../../Popup.jsx'

import axios from 'axios';

export const Business = ({url}) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const { setBusinessInfo, tlsInfo, businessInfo } = useContext(GlobalContext);

    const fetchBusinessData = useCallback(async () => { 
            if (!url) return;

            setLoading(true);
            setError(null);
            console.log("orgName: ", tlsInfo.subject.Organization);

            try {                
                const response = await axios.post('http://localhost:8000/scam-detector/detail/findbiz/', {
                    url: url,
                    organizationName: tlsInfo.subject.Organization,
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
                setBusinessInfo(decodedData);
            } 
            catch (err) {
                setError(err.message);
                setBusinessInfo(null);
            } 
            finally {
                setLoading(false);
            }
    }, [url, tlsInfo]);

    useEffect(() => {
        if (tlsInfo) {
            fetchBusinessData();
        }
    }, [fetchBusinessData, tlsInfo]);

    return (
        <div>
            <p style={{fontWeight: 'bold'}}>Business registration record</p>
            {loading ? (
                <div>Loading business registration record...</div>
            ) : error ? (
                <div>Error: {error}</div>
            ) : !businessInfo ? (
                <span></span>
            ) : (
                Object.entries(businessInfo).map(([key, value]) => (
                    <div key={key}>
                        <strong>{key}:</strong> {value}
                    </div>
                ))
            )}
        </div>
    )
}
