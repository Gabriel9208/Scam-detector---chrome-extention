import { useContext } from 'react'
import { GlobalContext } from '../../Popup.jsx'

export const Whois = () => {
    const { whoisInfo, loading, error } = useContext(GlobalContext);

    return (
        <div>
            <p style={{fontWeight: 'bold', color: '#2a4467'}}>Whois 資料</p> 
            {loading ? (
                <div>正在載入 Whois 資料...</div>
            ) : error ? (
                <div>載入錯誤</div>
            ) : !whoisInfo || Object.keys(whoisInfo).length === 0 ? (
                <span>沒有找到 Whois 資訊</span>
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
