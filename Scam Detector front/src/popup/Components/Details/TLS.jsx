import { useState, useEffect, useContext, useCallback } from 'react'
import { GlobalContext } from '../../Popup.jsx'

import axios from 'axios';

export const TLS = ({ url }) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const { setTlsInfo } = useContext(GlobalContext);

    const fetchTLSData = useCallback(async () => {
        if (!url) return;

        setLoading(true);
        setError(null);

        try {
            const response = await axios.post('http://localhost:8000/scam-detector/detail/tls/', {
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
            console.log("tls decodedData: ", decodedData);
            setTlsInfo(decodedData);
        }
        catch (err) {
            setError(err.message);
            setTlsInfo(null);
        }
        finally {
            setLoading(false);
        }
    }, [url]);

    useEffect(() => {
        fetchTLSData();
    }, [fetchTLSData]);

    const { tlsInfo } = useContext(GlobalContext);

    return (
        <div>
            <p style={{fontWeight: 'bold'}}>TLS data</p>
            {loading ? (
                <div>Loading TLS data...</div>
            ) : error ? (
                <div>Error: {error}</div>
            ) : !tlsInfo ? (
                <span></span>
            ) : (
                <div>
                    {tlsInfo.subject && (
                        <div>
                            <strong>Subject:</strong>
                            <ul>
                                {Object.entries(tlsInfo.subject).map(([key, value]) => (
                                    <li key={key}>{key}: {value}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                    {tlsInfo.issuer && (
                        <div>
                            <strong>Issuer:</strong>
                            <ul>
                                {Object.entries(tlsInfo.issuer).map(([key, value]) => (
                                    <li key={key}>{key}: {value}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                    {tlsInfo.version && <div><strong>Version:</strong> {tlsInfo.version}</div>}
                    {tlsInfo.serialNumber && <div><strong>Serial Number:</strong> {tlsInfo.serialNumber}</div>}
                    {tlsInfo.notBefore && <div><strong>Not Before:</strong> {tlsInfo.notBefore}</div>}
                    {tlsInfo.notAfter && <div><strong>Not After:</strong> {tlsInfo.notAfter}</div>}
                    {tlsInfo.subjectAltName && (
                        <div>
                            <strong>Subject Alternative Name:</strong>
                            <ul>
                                {tlsInfo.subjectAltName.map((name, index) => (
                                    <li key={index}>{name}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                    {tlsInfo.OCSP && <div><strong>OCSP:</strong> {tlsInfo.OCSP}</div>}
                    {tlsInfo.caIssuers && <div><strong>CA Issuers:</strong> {tlsInfo.caIssuers}</div>}
                    {tlsInfo.crlDistributionPoints && (
                        <div><strong>CRL Distribution Points:</strong> {tlsInfo.crlDistributionPoints}</div>
                    )}
                </div>
            )}
        </div>
    )
}
