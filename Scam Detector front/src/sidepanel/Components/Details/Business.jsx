import { useContext } from 'react'
import { GlobalContext } from '../../SidePanel.jsx'

export const Business = () => {
    const { businessInfo, loading, error } = useContext(GlobalContext);

    return (
        <div>
            <p style={{fontWeight: 'bold', color: '#2a4467'}}>公司登記記錄</p>
            {loading ? (
                <div>正在載入公司登記記錄...</div>
            ) : error ? (
                <div>載入錯誤</div>
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
