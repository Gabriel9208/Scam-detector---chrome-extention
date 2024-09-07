import { useState, useEffect } from 'react'
import Result from './Components/Result.jsx'
import Analysis from './Components/Analysis.jsx'
import Details from './Components/Detail.jsx'

import './Popup.css'

// result - easy, single line
// analysis - in 10 lines
// details - show each field result

export const Popup = () => {
  return (
    <main>
      <h1>Scam Detector</h1>
      <input type="text" placeholder="Enter URL" />
      <div>
        <Result />
        <Analysis />
        <Details />
      </div>
    </main>
  )
}

export default Popup
