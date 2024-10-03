import { useContext } from 'react'
import { GlobalContext } from '../../SidePanel.jsx'

export const Business = () => {
    const { businessInfo, loading, error } = useContext(GlobalContext);

    return (
        <div>
            <p style={{fontWeight: 'bold', color: '#2a4467'}}>Business registration record</p>
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
