import React, { useContext, useEffect, useState, useMemo } from 'react';
import { GlobalContext } from '../GlobalProvider.jsx';

import axios from 'axios';

export const scoreContributions = {
  domainExpired: 2,
  tlsExpired: 2,
  inPhishDB: 10,
  isDomainExpiringSoon: 0.5,
  isTLSExpiringSoon: 0.5,
  caStatus: 2,
  isDomainNew: 0.5,
  businessInfo: 1,
  pageInfo: 0.5,
  tlsInfo: 1,
  whoisInfo: 1,
  fakeDomain: 1
};

export const Analysis = ({ url }) => {
  const { whoisInfo, tlsInfo, businessInfo, pageInfo, setRiskScore, inPhishDB, setInPhishDB, loading, fakeDomain } = useContext(GlobalContext);
  const [caStatus, setCaStatus] = useState(null);
  const [caError, setCaError] = useState(null);

  // Memoize the date calculations
  const {
    domainAge,
    daysUntilExpiration,
    daysUntilTLSExpiration,
    domainExpired,
    tlsExpired,
    isDomainNew,
    isDomainExpiringSoon,
    isTLSExpiringSoon
  } = useMemo(() => {
    // Check for multiple possible field names for creation date
    const creationDateString =
      whoisInfo?.["creationDate"] ||
      whoisInfo?.['Record created'] ||
      whoisInfo?.['Creation Date'] ||
      whoisInfo?.['Created Date'] ||
      whoisInfo?.['Registration Time'] ||
      whoisInfo?.['Creation Time'] ||
      whoisInfo?.['Creation Time'];

    // Check for multiple possible field names for expiration date
    const expirationDateString =
      whoisInfo?.expirationDate ||
      whoisInfo?.['Registry Expiry Date'] ||
      whoisInfo?.['Expiration Date'] ||
      whoisInfo?.['Registrar Registration Expiration Date'] ||
      whoisInfo?.['Record expires'] ||
      whoisInfo?.['Expiration Time'];

    const tlsExpirationDateString = tlsInfo?.notAfter;

    if (!creationDateString || !expirationDateString || !tlsExpirationDateString) {
      console.log('Score calculation: Missing date information');
      return {};
    }

    function parseCustomDateToUTC8(dateString) {
      if (!dateString || typeof dateString !== 'string') {
        console.error('Invalid or missing date string:', dateString);
        return null;
      }
    
      let date;
    
      // Check if the date string matches the "2029-07-12 00:00:00 (UTC+8)" format
      const isoFormatRegex = /^\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s+\(UTC([+-]\d+)\)\s*$/;
      const isoMatch = dateString.match(isoFormatRegex);
    
      if (isoMatch) {
        const [, datePart, timePart, offsetHours] = isoMatch;
        date = new Date(`${datePart}T${timePart}Z`); // Treat as UTC
        const offsetMilliseconds = parseInt(offsetHours) * 60 * 60 * 1000;
        date = new Date(date.getTime() + offsetMilliseconds);
      } else {
        // Check if the date string matches the "2025-04-21T04:00:00Z" format
        const isoUtcRegex = /^\s*(\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}[Zz])\s*$/;
        const isoUtcMatch = dateString.match(isoUtcRegex);
    
        if (isoUtcMatch) {
          date = new Date(dateString);
        } else {
          // Check if the date string matches the "2025-04-04T07:55:39" format
          const isoWithoutTimezoneRegex = /^\s*(\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2})\s*$/;
          const isoWithoutTimezoneMatch = dateString.match(isoWithoutTimezoneRegex);
    
          if (isoWithoutTimezoneMatch) {
            date = new Date(dateString);
          } else {
            // Check if the date string matches the "Mar 3 23:59:59 2025 GMT" format
            const humanReadableRegex = /^\s*(\w{3})\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2})\s+(\d{4})\s+GMT\s*$/;
            const humanReadableMatch = dateString.match(humanReadableRegex);
    
            if (humanReadableMatch) {
              const [, month, day, time, year] = humanReadableMatch;
              const dateString = `${month} ${day} ${year} ${time} GMT`;
              date = new Date(dateString);
            } else {
              // Check if the date string matches the "2024-03-25 00:11:03" format
              const simpleFormatRegex = /^\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s*$/;
              const simpleMatch = dateString.match(simpleFormatRegex);
    
              if (simpleMatch) {
                const [, datePart, timePart] = simpleMatch;
                date = new Date(`${datePart}T${timePart}Z`); // Treat as UTC
              } else {
                console.error('Unrecognized date format:', dateString);
                return null;
              }
            }
          }
        }
      }
    
      // Convert to UTC+8
      const utc8Offset = 8 * 60 * 60 * 1000; // 8 hours in milliseconds
      return new Date(date.getTime() + utc8Offset);
    }
    
    // Function to calculate the difference between two dates in days
    function calculateDaysDifference(date1, date2) {
      try {
        if (!date1 || !date2 || !(date1 instanceof Date) || !(date2 instanceof Date)) {
          console.error('Invalid date inputs:', { date1, date2 });
          return -1;
        }
    
        // Calculate the actual difference without Math.abs()
        const diffTime = date2.getTime() - date1.getTime();
        return Math.floor(diffTime / (1000 * 60 * 60 * 24));
      } catch (error) {
        console.error('Error calculating days difference:', error);
        return -1;
      }
    }

    const creationDate = parseCustomDateToUTC8(creationDateString);
    const expirationDate = parseCustomDateToUTC8(expirationDateString);
    const tlsExpirationDate = parseCustomDateToUTC8(tlsExpirationDateString);

    if (!creationDate || !expirationDate || !tlsExpirationDate) {
      console.log('Score calculation: Failed to parse date information');
      return {};
    }

    const currentDateUTC8 = new Date(Date.now() + 8 * 60 * 60 * 1000);

    const domainAgeDay = calculateDaysDifference(creationDate, currentDateUTC8);
    const daysUntilExpirationDay = calculateDaysDifference(currentDateUTC8, expirationDate);
    const daysUntilTLSExpirationDay = calculateDaysDifference(currentDateUTC8, tlsExpirationDate);

    let domainExpiredDay = false;
    let tlsExpiredDay = false;
    let isDomainNewDay = false;
    let isDomainExpiringSoonDay = false;
    let isTLSExpiringSoonDay = false;

    if (daysUntilExpirationDay < 0){
      domainExpiredDay = true;
    }

    if(daysUntilTLSExpirationDay < 0){
      tlsExpiredDay = true ;
    }

    if (domainAgeDay > 0 && domainAgeDay <= 365) {
      isDomainNewDay = true;
    }
    
    if(daysUntilExpirationDay > 0 && daysUntilExpirationDay <= 30){
      isDomainExpiringSoonDay = true;
    }

    if(daysUntilTLSExpirationDay > 0 && daysUntilTLSExpirationDay <= 30){
      isTLSExpiringSoonDay = true;
    }

    return {
      domainAge: domainAgeDay,
      daysUntilExpiration: daysUntilExpirationDay,
      daysUntilTLSExpiration: daysUntilTLSExpirationDay,
      domainExpired: domainExpiredDay,
      tlsExpired: tlsExpiredDay,
      isDomainNew: isDomainNewDay,
      isDomainExpiringSoon: isDomainExpiringSoonDay,
      isTLSExpiringSoon: isTLSExpiringSoonDay
    };
  }, [whoisInfo, tlsInfo]);

  useEffect(() => {
    console.log("Analysis effect running, tlsInfo:", tlsInfo);
    const checkCAStatus = async () => {
      if (tlsInfo && tlsInfo.issuer && ("Common Name" in tlsInfo.issuer || "commonName" in tlsInfo.issuer)) {
        const caName = "Common Name" in tlsInfo.issuer ? tlsInfo.issuer["Common Name"] : tlsInfo.issuer["commonName"];
        try {
          const response = await axios.post('http://localhost:8000/scam-detector/analysis/ca/', {
            ca: caName
          }, {
            headers: {
              'Content-Type': 'application/json',
            },
          });

          // Axios automatically throws an error for non-2xx status codes
          const data = response.data;
          console.log("CA status data:", data);
          setCaStatus(data.result.is_trusted_ca);
        } catch (error) {
          console.error("Error checking CA status:", error);
          setCaError("Failed to verify CA status");
        }
      }
      else {
        console.log("TLS issuer Common Name not yet available");
        setCaStatus(null);
        setCaError(null);
      }
      
      if (url) {
        try {
          const response = await axios.post('http://localhost:8000/scam-detector/analysis/phish/', {
            url: url
          }, {
            headers: {
              'Content-Type': 'application/json',
            },
          });

          // Axios automatically throws an error for non-2xx status codes
          const data = response.data;
          setInPhishDB(data.result.in_phish_db);
        } catch (error) {
          console.error("Error checking CA status:", error);
          setCaError("Failed to verify CA status");
        }
      }
    };

    checkCAStatus();
  }, [tlsInfo]);

  useEffect(() => {
    const calculatedScoreContributions = {
      domainExpired: domainExpired ? scoreContributions.domainExpired : 0,
      tlsExpired: tlsExpired ? scoreContributions.tlsExpired : 0,
      inPhishDB: inPhishDB ? scoreContributions.inPhishDB : 0,
      isDomainExpiringSoon: isDomainExpiringSoon ? scoreContributions.isDomainExpiringSoon : 0,
      isTLSExpiringSoon: isTLSExpiringSoon ? scoreContributions.isTLSExpiringSoon : 0,
      caStatus: caStatus === null ? scoreContributions.caStatus / 2 : (caStatus ? 0 : scoreContributions.caStatus),
      isDomainNew: isDomainNew ? scoreContributions.isDomainNew : 0,
      businessInfo: businessInfo && Object.keys(businessInfo).length > 0 && !("detail" in businessInfo) && !("details" in businessInfo) && !("error" in businessInfo) ? 0 : scoreContributions.businessInfo,
      pageInfo: pageInfo && Object.keys(pageInfo).length > 0 && !("detail" in pageInfo) && !("details" in pageInfo) && !("error" in pageInfo) ? 0 : scoreContributions.pageInfo,
      tlsInfo: tlsInfo && Object.keys(tlsInfo).length > 0 && !("detail" in tlsInfo) && !("details" in tlsInfo) && !("error" in tlsInfo) ? 0 : scoreContributions.tlsInfo,
      whoisInfo: whoisInfo && Object.keys(whoisInfo).length > 0 && !("detail" in whoisInfo) && !("details" in whoisInfo) && !("error" in whoisInfo) ? 0 : scoreContributions.whoisInfo,
      fakeDomain: fakeDomain ? scoreContributions.fakeDomain : 0
    };

    const newRiskScore = Object.values(calculatedScoreContributions).reduce((a, b) => a + b, 0);

    console.log("Risk score contributions:", calculatedScoreContributions);
    
    console.log('Score:', newRiskScore);

    setRiskScore(newRiskScore);
  }, [url, domainExpired, tlsExpired, isDomainExpiringSoon, isTLSExpiringSoon, caStatus, isDomainNew, inPhishDB, businessInfo, pageInfo, tlsInfo, whoisInfo]);

  return (
    <div style={{ marginBottom: "50px" }}>
      <h2 style={{ marginBottom: "30px" }}>風險評估</h2>
      <div className='indent-container'>
        <div>
          {inPhishDB && <p>惡意: 此網站被收錄於釣魚網站資料庫中。</p>}
          {isDomainNew && <p>小心: 這是一個相對較新的域名，可能存在較高的風險。</p>}
          {isDomainExpiringSoon && <p>小心: 域名即將到期。這可能表明域名被忽視或可能被放棄。</p>}
          {isTLSExpiringSoon && <p>小心: TLS 證書即將到期。這可能會在瀏覽器中導致安全警告。</p>}
          {domainExpired && <p>惡意: 域名已過期。</p>}
          {tlsExpired && <p>惡意: TLS 證書已過期。</p>}
          {!isDomainNew && !isDomainExpiringSoon && !isTLSExpiringSoon && <p>未檢測到立即的時間相關風險。</p>}
          {(() => {
              if (caStatus === null && loading) return <p>正在檢查證書授權機構的狀態...</p>;
              else if (caStatus === null && !loading) return <p>警告: 無法驗證證書授權機構 (CA) 的狀態。</p>;
              if (caError) return <p>警告: 無法驗證證書授權機構 (CA) 的狀態。</p>;
              if (caStatus === true) return <p>證書授權機構已獲信任。</p>;
              if (caStatus === false) return <p>惡意: 證書授權機構未獲信任。</p>;
              return null;
            })()}
          {fakeDomain && <p>警告: 此網站可能是假冒的。</p>}
        </div>
        <h3>時間分析 :</h3>
        <div className='indent-container'>
          {domainExpired && <p>惡意: 域名已過期。</p>}
          {tlsExpired && <p>惡意: TLS 證書已過期。</p>}
          {whoisInfo && whoisInfo!={} && !("error" in whoisInfo) && !domainExpired &&
            <>
              <p>域齡: 已建立 {domainAge} 天 {isDomainNew ? '(新域名)' : '(已建立域名)'}</p>
              <p>域名到期日: 還剩 {daysUntilExpiration} 天過期 {isDomainExpiringSoon ? '(即將到期!)' : ''}</p>
            </>
          }
          {tlsInfo && tlsInfo!={} && !("error" in tlsInfo) && !tlsExpired &&
            <>
              <p>TLS 證書到期日: 還剩 {daysUntilTLSExpiration} 天過期 {isTLSExpiringSoon ? '(即將到期!)' : ''}</p>
            </>
          }
        </div>
        <h3>有效性分析 :</h3>
        <div className='indent-container'>
          <p>{
            caError ? caError :
              caStatus === null ? (loading ? "檢查中..." : "警告: 無法驗證證書授權機構 (CA) 的狀態。") :
                caStatus ? "TLS 證書 CA 已獲信任" : "TLS 證書 CA 未獲信任"
          }</p>
        </div>
        <h3>數據可用性 :</h3>
        <div className='indent-container'>
          {tlsInfo && Object.keys(tlsInfo).length > 0 && !("detail" in tlsInfo) && !("details" in tlsInfo) && !("error" in tlsInfo) ? <p>TLS 資訊可用。</p> : <p>警告: 找不到 TLS 資訊。</p>}
          {whoisInfo && Object.keys(whoisInfo).length > 0 && !("detail" in whoisInfo) && !("details" in whoisInfo) && !("error" in whoisInfo) ? <p>Whois 資訊可用。</p> : <p>警告: 找不到 Whois 資訊。</p>}
          {businessInfo && Object.keys(businessInfo).length > 0 && !("detail" in businessInfo) && !("details" in businessInfo) && !("error" in businessInfo) ? <p>Business 資訊可用。</p> : <p>警告: 找不到 Business 資訊。</p>}
          {pageInfo && Object.keys(pageInfo).length > 0 && !("detail" in pageInfo) && !("details" in pageInfo) && !("error" in pageInfo) ? <p>Page 資訊可用。</p> : <p>小心: 找不到 Page 資訊。</p>}
        </div>
      </div>
    </div>
  );
};


