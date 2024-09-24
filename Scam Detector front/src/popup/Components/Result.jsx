import { useState, useEffect, useContext } from 'react'
import { GlobalContext } from '../Popup.jsx'

export const Result = () => {
  const { riskScore } = useContext(GlobalContext);
  return (
    <div>
      <h3>Result</h3>      
      <p>Risk Score: {riskScore}</p>
      {riskScore > 2 ? (
        <p style={{color: 'red'}}>This website is risky. Exercise extreme caution.</p>
      ) : riskScore > 1 ? (
        <p style={{color: 'orange'}}>Be cautious when interacting with this website.</p>
      ) : (
        <p style={{color: 'green'}}>No malicious activity detected.</p>
      )}
    </div>
  )
}