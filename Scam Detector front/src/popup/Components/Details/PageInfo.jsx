import { useState, useEffect, useContext, useCallback } from 'react'
import { GlobalContext } from '../../Popup.jsx'

import axios from 'axios';

export const PageInfo = ({url}) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const { setPageInfo } = useContext(GlobalContext);

    const fetchPageData = useCallback(async () => { 
            if (!url) return;

            setLoading(true);
            setError(null);

            try {                
                const response = await axios.post('http://localhost:8000/scam-detector/detail/web-content/', {
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

                setPageInfo(decodedData);
            } 
            catch (err) {
                setError(err.message);
                setPageInfo(null);
            } 
            finally {
                setLoading(false);
            }
    }, [url]);

    useEffect(() => {
        fetchPageData();
    }, [fetchPageData]);

    const { pageInfo } = useContext(GlobalContext);

    return (
        <div>
            <p style={{fontWeight: 'bold'}}>Page information</p>
            {loading ? (
                <div>Loading page information...</div>
            ) : error ? (
                <div>Error: {error}</div>
            ) : !pageInfo ? (
                <span></span>
            ) : (
                Object.entries(pageInfo).map(([key, value]) => (
                    <div key={key}>
                        <strong>{key}:</strong> {value}
                    </div>
                ))
            )}
        </div>
    );
}
