import { Whois } from './Details/Whois.jsx'
import { PageInfo } from './Details/PageInfo.jsx'
import { TLS } from './Details/TLS.jsx'
import { Business } from './Details/Business.jsx'
import React, { useEffect, useMemo, useContext, useState } from 'react'
import axios from 'axios';
import { GlobalContext } from '../SidePanel.jsx';

const ToggleSection = ({ title, children }) => {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="toggle-section">
            <h3 onClick={() => setIsOpen(!isOpen)} className="toggle-header">
                <span className={`toggle-icon ${isOpen ? 'open' : ''}`}>▶</span>
                {title}
            </h3>
            {isOpen && <div className="toggle-content">{children}</div>}
        </div>
    );
};

export const Detail = ({ url }) => {
    const { setWhoisInfo, setTlsInfo, setBusinessInfo, setPageInfo, loading, setLoading, error, setError } = useContext(GlobalContext);

    const fetchData = useMemo(() => async () => {
        if (!url) return;

        setLoading(true);
        setError(null);

        const decodeData = (data) => Object.fromEntries(
            Object.entries(data).map(([key, value]) => [
                key,
                typeof value === 'string' ? decodeURIComponent(JSON.parse(`"${value}"`)) : value
            ])
        );

        const fetchEndpoint = async (endpoint, setter) => {
            try {
                const response = await axios.post(`http://localhost:8000/scam-detector/detail/${endpoint}/`, { url });
                setter(decodeData(response.data));
            } catch (err) {
                console.error(`Error fetching ${endpoint}:`, err);
                setter({ error: err.response?.data?.detail || err.message });
            }
        };

        await Promise.all([
            fetchEndpoint('whois', setWhoisInfo),
            fetchEndpoint('tls', setTlsInfo),
            fetchEndpoint('findbiz', setBusinessInfo),
            fetchEndpoint('web-content', setPageInfo)
        ]);

        setLoading(false);
    }, [url]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return (
        <div>
            <ToggleSection title="Detailed information">
                <Whois loading={loading} error={error} />
                <TLS loading={loading} error={error} />
                <Business loading={loading} error={error} />
                <PageInfo loading={loading} error={error} />
            </ToggleSection>
        </div>
    )
}
