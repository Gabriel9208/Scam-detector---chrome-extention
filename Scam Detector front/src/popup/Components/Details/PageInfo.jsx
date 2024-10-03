import { useContext } from 'react'
import { GlobalContext } from '../../Popup.jsx'

export const PageInfo = () => {
    const { pageInfo, loading, error } = useContext(GlobalContext);

    return (
        <div>
            <p style={{fontWeight: 'bold', color: '#2a4467'}}>Page information</p>
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
