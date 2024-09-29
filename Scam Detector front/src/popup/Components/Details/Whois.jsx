import { useContext } from 'react'
import { GlobalContext } from '../../Popup.jsx'

export const Whois = () => {
    const { whoisInfo, loading, error } = useContext(GlobalContext);

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
