import React from 'react'
import ReactDOM from 'react-dom/client'
import { Popup } from './Popup'
import { GlobalProvider } from './GlobalProvider.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('app')).render(
  <React.StrictMode>
    <GlobalProvider>
      <Popup />
    </GlobalProvider>
  </React.StrictMode>,
)
