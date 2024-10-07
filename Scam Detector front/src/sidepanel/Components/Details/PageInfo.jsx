import { useContext } from 'react'
import { GlobalContext } from '../../SidePanel.jsx'

export const PageInfo = () => {
    const { pageInfo, loading, error } = useContext(GlobalContext);

    return (
        <div>
            <p style={{fontWeight: 'bold', color: '#2a4467', marginTop: '50px'}}>頁面資訊</p>
            {loading ? (
                <div>正在載入頁面資訊...</div>
            ) : error ? (
                <div>載入錯誤</div>
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
