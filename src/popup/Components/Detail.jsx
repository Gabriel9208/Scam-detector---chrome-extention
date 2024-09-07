import Whois from './Details/Whois.jsx'
import PageInfo from './Details/PageInfo.jsx'
import Contact from './Details/Contact.jsx'
import Business from './Details/Business.jsx'

export const Verbose = () => {
    return (
        <div>
            <h2>Detailed information</h2>
            <Whois />
            <PageInfo />
            <Contact />
            <Business />
        </div>
    )
}

export default Verbose