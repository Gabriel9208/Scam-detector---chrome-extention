import React, { useContext, useEffect, useState, useMemo } from 'react';
import { GlobalContext } from '../SidePanel.jsx';

import axios from 'axios';

export const Analysis = ({ url }) => {
  const { whoisInfo, tlsInfo, businessInfo, pageInfo, setRiskScore, inPhishDB, setInPhishDB, loading } = useContext(GlobalContext);
  const [caStatus, setCaStatus] = useState(null);
  const [caError, setCaError] = useState(null);

  // Memoize the date calculations
  const {
    creationDate,
    expirationDate,
    tlsExpirationDate,
    currentDateUTC8,
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
      whoisInfo?.creationDate ||
      whoisInfo?.['Record created'] ||
      whoisInfo?.['Creation Date'] ||
      whoisInfo?.['Created Date'];

    // Check for multiple possible field names for expiration date
    const expirationDateString =
      whoisInfo?.expirationDate ||
      whoisInfo?.['Registry Expiry Date'] ||
      whoisInfo?.['Expiration Date'] ||
      whoisInfo?.['Registrar Registration Expiration Date'] ||
      whoisInfo?.['Record expires'];

    const tlsExpirationDateString = tlsInfo?.notAfter;

    if (!creationDateString || !expirationDateString || !tlsExpirationDateString) {
      console.log('Score calculation: Missing date information');
      return {};
    }

    const creationDate = parseCustomDateToUTC8(creationDateString);
    const expirationDate = parseCustomDateToUTC8(expirationDateString);
    const tlsExpirationDate = parseCustomDateToUTC8(tlsExpirationDateString);

    if (!creationDate || !expirationDate || !tlsExpirationDate) {
      console.log('Score calculation: Failed to parse date information');
      return {};
    }

    const currentDateUTC8 = new Date(Date.now() + 8 * 60 * 60 * 1000);

    const domainAge = calculateDaysDifference(creationDate, currentDateUTC8);
    const daysUntilExpiration = calculateDaysDifference(currentDateUTC8, expirationDate);
    const daysUntilTLSExpiration = calculateDaysDifference(currentDateUTC8, tlsExpirationDate);

    const domainExpired = domainAge === -1;
    const tlsExpired = daysUntilTLSExpiration === -1;

    const isDomainNew = domainAge !== -1 && domainAge <= 365;
    const isDomainExpiringSoon = daysUntilExpiration <= 30;
    const isTLSExpiringSoon = daysUntilTLSExpiration <= 30;

    console.log('Score calculation: Domain age:', domainAge);
    console.log('Score calculation: Days until domain expiration:', daysUntilExpiration);
    console.log('Score calculation: Days until TLS expiration:', daysUntilTLSExpiration);
    console.log('Score calculation: Domain expired:', domainExpired);
    console.log('Score calculation: TLS expired:', tlsExpired);
    console.log('Score calculation: Is domain new:', isDomainNew);
    console.log('Score calculation: Is domain expiring soon:', isDomainExpiringSoon);
    console.log('Score calculation: Is TLS expiring soon:', isTLSExpiringSoon);
    return {
      creationDate,
      expirationDate,
      tlsExpirationDate,
      currentDateUTC8,
      domainAge,
      daysUntilExpiration,
      daysUntilTLSExpiration,
      domainExpired,
      tlsExpired,
      isDomainNew,
      isDomainExpiringSoon,
      isTLSExpiringSoon
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
    const scoreContributions = {
      domainExpired: domainExpired ? 2 : 0,
      tlsExpired: tlsExpired ? 2 : 0,
      inPhishDB: inPhishDB ? 10 : 0,
      isDomainExpiringSoon: isDomainExpiringSoon ? 0.5 : 0,
      isTLSExpiringSoon: isTLSExpiringSoon ? 0.5 : 0,
      caStatus: caStatus === null ? 0.5 : (caStatus ? 0 : 2),
      isDomainNew: isDomainNew ? 0.5 : 0,
      businessInfo: businessInfo ? 0 : 0.5,
      pageInfo: pageInfo ? 0 : 0.5,
      tlsInfo: tlsInfo ? 0 : 0.5,
      whoisInfo: whoisInfo ? 0 : 0.5
    };

    const newRiskScore = Object.values(scoreContributions).reduce((a, b) => a + b, 0);

    console.log("Risk score contributions:", scoreContributions);
    
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
        </div>
        <h3>時間分析 :</h3>
        <div className='indent-container'>
          {domainExpired && <p>惡意: 域名已過期。</p>}
          {tlsExpired && <p>惡意: TLS 證書已過期。</p>}
          {!domainExpired && !tlsExpired &&
            <>
              <p>域齡: {domainAge} 天 {isDomainNew ? '(新域名)' : '(已建立域名)'}</p>
              <p>域名到期日: {daysUntilExpiration} {isDomainExpiringSoon ? '(即將到期!)' : ''}</p>
              <p>TLS 證書到期日: {daysUntilTLSExpiration} {isTLSExpiringSoon ? '(即將到期!)' : ''}</p>
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
          {tlsInfo && Object.keys(tlsInfo).length > 0 ? <p>TLS 資訊可用。</p> : <p>警告: 找不到 TLS 資訊。</p>}
          {whoisInfo && Object.keys(whoisInfo).length > 0 ? <p>Whois 資訊可用。</p> : <p>警告: 找不到 Whois 資訊。</p>}
          {businessInfo && Object.keys(businessInfo).length > 0 ? <p>Business 資訊可用。</p> : <p>警告: 找不到 Business 資訊。</p>}
          {pageInfo && Object.keys(pageInfo).length > 0 ? <p>Page 資訊可用。</p> : <p>警告: 找不到 Page 資訊。</p>}
        </div>
      </div>
    </div>
  );
};


function parseCustomDateToUTC8(dateString) {
  if (!dateString || typeof dateString !== 'string') {
    console.error('Invalid or missing date string:', dateString);
    return null;
  }

  let date;

  // Check if the date string matches the "2029-07-12 00:00:00 (UTC+8)" format
  const isoFormatRegex = /^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s+\(UTC([+-]\d+)\)$/;
  const isoMatch = dateString.match(isoFormatRegex);

  if (isoMatch) {
    const [, datePart, timePart, offsetHours] = isoMatch;
    date = new Date(`${datePart}T${timePart}Z`); // Treat as UTC
    const offsetMilliseconds = parseInt(offsetHours) * 60 * 60 * 1000;
    date = new Date(date.getTime() + offsetMilliseconds);
  } else {
    // Check if the date string matches the "2025-04-21T04:00:00Z" format
    const isoUtcRegex = /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)$/;
    const isoUtcMatch = dateString.match(isoUtcRegex);

    if (isoUtcMatch) {
      date = new Date(dateString);
    } else {
      // Check if the date string matches the "2025-04-04T07:55:39" format
      const isoWithoutTimezoneRegex = /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})$/;
      const isoWithoutTimezoneMatch = dateString.match(isoWithoutTimezoneRegex);

      if (isoWithoutTimezoneMatch) {
        date = new Date(dateString);
      } else {
        // Check if the date string matches the "Mar 3 23:59:59 2025 GMT" format
        const humanReadableRegex = /^(\w{3})\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2})\s+(\d{4})\s+GMT$/;
        const humanReadableMatch = dateString.match(humanReadableRegex);

        if (humanReadableMatch) {
          const [, month, day, time, year] = humanReadableMatch;
          const dateString = `${month} ${day} ${year} ${time} GMT`;
          date = new Date(dateString);
        } else {
          console.error('Unrecognized date format:', dateString);
          return null;
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
  if (date1 > date2) {
    return -1;
  }
  const diffTime = Math.abs(date2 - date1);
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}