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
            ) : !pageInfo || Object.keys(pageInfo).length === 0 ? (  
                <span>沒有找到該公司/組織相關資訊</span>
            ) : (
                Object.entries(pageInfo).map(([key, value]) => (
                    <div key={key}>
                        <strong>{key}:</strong> {
                            Array.isArray(value) 
                                ? value.map((item, index) => (
                                    <span key={index}>
                                        {item}
                                        {index < value.length - 1 ? ', ' : ''}
                                    </span>
                                  ))
                                : value
                        }
                    </div>
                ))
            )}
        </div>
    );
}
