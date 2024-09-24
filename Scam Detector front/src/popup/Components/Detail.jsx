import { Whois } from './Details/Whois.jsx'
import { PageInfo } from './Details/PageInfo.jsx'
import { TLS } from './Details/TLS.jsx'
import { Business } from './Details/Business.jsx'
import { useState, useContext } from 'react'
import { GlobalContext } from '../Popup.jsx';

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
    const { whoisInfo, tlsInfo, businessInfo, pageInfo } = useContext(GlobalContext);

    return (
        <div>
            <ToggleSection title="Detailed information">
                <Whois url={url} />
                <TLS url={url} />
                <Business url={url} />
                <PageInfo url={url} />
            </ToggleSection>
        </div>
    )
}
