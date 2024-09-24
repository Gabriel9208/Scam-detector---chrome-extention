import React, { useContext, useEffect, useState, useMemo } from 'react';
import { GlobalContext } from '../Popup.jsx';

import axios from 'axios';

export const Analysis = () => {
  const { whoisInfo, tlsInfo, businessInfo, pageInfo, setRiskScore } = useContext(GlobalContext);
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
      return {};
    }

    const creationDate = parseCustomDateToUTC8(creationDateString);
    const expirationDate = parseCustomDateToUTC8(expirationDateString);
    const tlsExpirationDate = parseCustomDateToUTC8(tlsExpirationDateString);
    
    if (!creationDate || !expirationDate || !tlsExpirationDate) {
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
      if (tlsInfo && tlsInfo.issuer && tlsInfo.issuer["Common Name"]) {
        try {
          const response = await axios.post('http://localhost:8000/scam-detector/analysis/ca/', {
            ca: tlsInfo.issuer["Common Name"]
          }, {
            headers: {
              'Content-Type': 'application/json',
            },
          });

          // Axios automatically throws an error for non-2xx status codes
          const data = response.data;
          console.log("CA status data:",  data);
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
    };

    checkCAStatus();
  }, [tlsInfo]);

  useEffect(() => {
    const newRiskScore = 
      (domainExpired ? 2 : 0) + 
      (tlsExpired ? 2 : 0) + 
      (isDomainExpiringSoon ? 0.5 : 0) + 
      (isTLSExpiringSoon ? 0.5 : 0) + 
      (caStatus ? 0 : 2) +
      (isDomainNew ? 0.5 : 0) +

      (businessInfo ? 0 : 0.5) +
      (pageInfo ? 0 : 0.5)+
      (tlsInfo ? 0 : 0.5)+
      (whoisInfo ? 0 : 0.5);
    
    setRiskScore(newRiskScore);
  }, [domainExpired, tlsExpired, isDomainExpiringSoon, isTLSExpiringSoon, caStatus, isDomainNew]);

  return (
    <div style={{marginBottom: "50px"}}>
      <h2 style={{marginBottom: "20px"}}>Domain Analysis</h2>
      <h3>Risk Assessment :</h3>
      <ul>
        {isDomainNew && <li>Warning: This is a relatively new domain, which may pose higher risk.</li>}
        {isDomainExpiringSoon && <li>Warning: The domain is expiring soon. This could indicate neglect or potential abandonment.</li>}
        {isTLSExpiringSoon && <li>Warning: The TLS certificate is expiring soon. This could lead to security warnings in browsers.</li>}
        {domainExpired && <li>Malicious: The domain has expired.</li>}
        {tlsExpired && <li>Malicious: The TLS certificate has expired.</li>}
        {!isDomainNew && !isDomainExpiringSoon && !isTLSExpiringSoon && <li>No immediate time-related risks detected.</li>}
        {(() => {
          if (caStatus === null) return <li>Checking the Certificate Authority status...</li>;
          if (caError) return <li>Warning: Unable to verify the Certificate Authority (CA) status.</li>;
          if (caStatus === true) return <li>The Certificate Authority is trusted.</li>;
          if (caStatus === false) return <li>Malicious: The Certificate Authority is not trusted.</li>;
          return null;
        })()}
      </ul>

      <h3>Time Analysis :</h3>
      
      {domainExpired && <p>Warning: The domain has expired.</p>}
      {tlsExpired && <p>Warning: The TLS certificate has expired.</p>}
      {!domainExpired && !tlsExpired && 
      <>
      <p>Domain Age: {domainAge} days {isDomainNew ? '(New Domain)' : '(Established Domain)'}</p>
      <p>Days until Domain Expiration: {daysUntilExpiration} {isDomainExpiringSoon ? '(Expiring Soon!)' : ''}</p>
      <p>Days until TLS Certificate Expiration: {daysUntilTLSExpiration} {isTLSExpiringSoon ? '(Expiring Soon!)' : ''}</p>
      </>
      }

      <h3>Validity Analysis :</h3>
      <p>The TLS certificate CA is: {
        caError ? caError :
        caStatus === null ? "Checking..." :
        caStatus ? "Trusted" : "Not Trusted"
      }</p>

      <h3>Data Availability :</h3>
        {tlsInfo ? <p>TLS information is available.</p> : <p>Warning: TLS information is not available.</p>}
        {whoisInfo ? <p>Whois information is available.</p> : <p>Warning: Whois information is not available.</p>}
        {businessInfo ? <p>Business information is available.</p> : <p>Warning: Business information is not available.</p>}
        {pageInfo ? <p>Page information is available.</p> : <p>Warning: Page information is not available.</p>}
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
// Example usage:
// <Analysis dateString="2029-07-12 00:00:00 (UTC+8)" />
// or
// <Analysis dateString="Mar 3 23:59:59 2025 GMT" />
