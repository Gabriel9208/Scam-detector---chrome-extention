import React, { createContext, useState, useMemo, useEffect } from 'react';

export const GlobalContext = createContext();

export const GlobalProvider = ({ children }) => {
  const [whoisInfo, setWhoisInfo] = useState(null);
  const [tlsInfo, setTlsInfo] = useState(null);
  const [businessInfo, setBusinessInfo] = useState(null);
  const [pageInfo, setPageInfo] = useState(null);
  const [riskScore, setRiskScore] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inPhishDB, setInPhishDB] = useState(false);
  const [fakeDomain, setFakeDomain] = useState(false);

  const contextValue = useMemo(() => ({
    whoisInfo,
    setWhoisInfo,
    tlsInfo,
    setTlsInfo,
    businessInfo,
    setBusinessInfo,
    pageInfo,
    setPageInfo,
    riskScore,
    setRiskScore,
    inPhishDB,
    setInPhishDB,
    loading,
    setLoading,
    error,
    setError, 
    fakeDomain,
    setFakeDomain
  }), [whoisInfo, tlsInfo, businessInfo, pageInfo, riskScore, loading, error, inPhishDB, fakeDomain]);

  return (
    <GlobalContext.Provider value={contextValue}>
      {children}
    </GlobalContext.Provider>
  );
};