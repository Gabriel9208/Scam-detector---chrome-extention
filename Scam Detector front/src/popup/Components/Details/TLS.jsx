import { useContext } from 'react'
import { GlobalContext } from '../../Popup.jsx'

export const TLS = () => {
    const { tlsInfo, loading, error } = useContext(GlobalContext);

    return (
        <div>
            <p style={{fontWeight: 'bold', color: '#2a4467', marginTop: '50px'}}>傳輸層安全憑證(TLS)資訊</p>
            {loading ? (
                <div>正在載入 TLS 資訊...</div>
            ) : error ? (
                <div>載入錯誤</div>
            ) : !tlsInfo || Object.keys(tlsInfo).length === 0 ? (
                <span>沒有找到 TLS 資訊</span>
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
