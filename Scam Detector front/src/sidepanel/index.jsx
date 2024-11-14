import React from 'react'
import ReactDOM from 'react-dom/client'
import { SidePanel } from './SidePanel'
import { GlobalProvider } from './GlobalProvider.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('app')).render(
  <React.StrictMode>
    <GlobalProvider>
      <SidePanel />
    </GlobalProvider>
  </React.StrictMode>,
)
