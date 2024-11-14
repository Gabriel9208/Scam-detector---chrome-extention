import { useContext } from 'react'
import { GlobalContext } from '../../GlobalProvider.jsx'

export const Business = () => {
    const { businessInfo, loading, error } = useContext(GlobalContext);

    return (
        <div>
            <p style={{fontWeight: 'bold', color: '#2a4467', marginTop: '50px'}}>公司登記記錄</p>
            {loading ? (
                <div>正在載入公司登記記錄...</div>
            ) : error ? (
                <div>載入錯誤</div>
            ) : !businessInfo || Object.keys(businessInfo).length === 0 ? (
                <span>沒有找到該公司在台灣登記的相關資訊</span>
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
