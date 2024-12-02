import { Whois } from './Details/Whois.jsx'
import { PageInfo } from './Details/PageInfo.jsx'
import { TLS } from './Details/TLS.jsx'
import { Business } from './Details/Business.jsx'
import React, { useEffect, useMemo, useContext } from 'react'
import axios from 'axios';
import { GlobalContext } from '../GlobalProvider.jsx';

export const Detail = ({ url }) => {
    const { setWhoisInfo, setTlsInfo, setBusinessInfo, setPageInfo, loading, setLoading, error, setError, setFakeDomain } = useContext(GlobalContext);

    const fetchData = useMemo(() => async () => {
        if (!url) return;

        setLoading(true);
        setError(null);

        const decodeData = (data) => Object.fromEntries(
            Object.entries(data).map(([key, value]) => [
                key,
                typeof value === 'string' ? decodeURIComponent(JSON.parse(`"${value}"`)) : value
            ])
        );

        const cutStringAtNonAlpha = (str) => {
            // Decode Unicode escape sequences
            const decodedStr = str.replace(/\\u([a-fA-F0-9]{4})/g, (match, p1) => 
                String.fromCharCode(parseInt(p1, 16))
            );
            
            console.log("Decoded string:", decodedStr);
            
            const match = decodedStr.match(/^[^~!@#$%^&*()_+-=,./;':"<>?|\]\[\{\}]+/u);
            console.log("Matched string:", match ? match[0] : "No match");
            return match ? match[0].trim() : '';
        }

        let orgName = "";
        let pageSource = "";
        const orgNameHidden = ["encrypt", "protected", "disclosed", "Redacted", "privacy", "Prohibited", "Fail"]
        const fetchEndpoint = async (endpoint, setter, ...args) => {
            const startTime = Date.now();
            try {
                if(endpoint === 'findbiz'){
                    console.log("findbiz orgName:", orgName);
                }
                let response;
                
                if(endpoint === 'findbiz' && args.length > 0){
                    response = await axios.post(`http://localhost:8000/scam-detector/detail/${endpoint}/`, { url: url, organizationName: args[0] });
                }
                else if(endpoint === 'fake-domain' && args.length > 0){
                    response = await axios.post(`http://localhost:8000/scam-detector/detail/${endpoint}/`, { url: url, source: args[0] });
                }
                else{
                    response = await axios.post(`http://localhost:8000/scam-detector/detail/${endpoint}/`, { url: url });
                    if(endpoint === 'web-content'){
                        pageSource = response.data.source;
                    }
                }

                const duration = Date.now() - startTime;
                console.log(`${endpoint} request took ${duration}ms`);

                if (("details" in response.data && (response.data.details.includes("404") || response.data.details.includes("500"))) ||
                ("detail" in response.data && (response.data.detail.includes("404") || response.data.detail.includes("500"))) ||
                ("error" in response.data)) {
                    console.log("Endpoint 404 not found:", endpoint);
                    setter({});
                }
                else{
                    if(endpoint === 'web-content'){
                        setter(decodeData(response.data)['info']);
                    }
                    else if(endpoint === 'fake-domain'){
                        console.log("fake-domain:", decodeData(response.data)['result']);
                        setter(decodeData(response.data)['result']['result']);
                    }
                    else{
                        setter(decodeData(response.data));
                    }
                }

                if (endpoint === 'whois') {
                    if("Registrant" in response.data) {
                        console.log("Registrant found in response data");
                        const containsKeyword = orgNameHidden.some(keyword => cutStringAtNonAlpha(response.data.Registrant).toLowerCase().includes(keyword.toLowerCase()));
                        
                        console.log("Contains keyword:", containsKeyword);
                        if (!containsKeyword) {
                            orgName = cutStringAtNonAlpha(response.data.Registrant);
                            console.log("Registrant:", orgName);
                        } else {
                            console.log("Registrant contains a hidden keyword");
                        }
                    }
                    else if ("Registrant Organization" in response.data) {
                        console.log("Registrant Organization found in response data");
                        const containsKeyword = orgNameHidden.some(keyword => cutStringAtNonAlpha(response.data["Registrant Organization"]).toLowerCase().includes(keyword.toLowerCase()));
                        
                        console.log("Contains keyword:", containsKeyword);
                        if (!containsKeyword) {
                            orgName = cutStringAtNonAlpha(response.data["Registrant Organization"]);
                            console.log("Registrant Organization:", orgName);
                        } else {
                            console.log("Registrant Organization contains a hidden keyword");
                        }
                    } else {
                        console.log("Neither Registrant nor Registrant Organization found in response data");
                    }
                }
            } catch (err) {
                const duration = Date.now() - startTime;
                console.log(`${endpoint} request took ${duration}ms`);
                console.error(`Error fetching ${endpoint}:`, err);
                setter({});
            }
        };

        await Promise.all([
            fetchEndpoint('whois', setWhoisInfo),
            fetchEndpoint('tls', setTlsInfo),
            fetchEndpoint('web-content', setPageInfo)
        ]);

        if (orgName.trim() !== "") {
            await fetchEndpoint('fake-domain', setFakeDomain, pageSource);
            await fetchEndpoint('findbiz', setBusinessInfo, orgName);
        }
        else{
            await fetchEndpoint('fake-domain', setFakeDomain, pageSource);
            await fetchEndpoint('findbiz', setBusinessInfo);
        }

        setLoading(false);
    }, [url]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return (
        <div>
            <Whois loading={loading} error={error} />
            <TLS loading={loading} error={error} />
            <Business loading={loading} error={error} />
            <PageInfo loading={loading} error={error} />
        </div>
    )
}
