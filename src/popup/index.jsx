import React from 'react'
import ReactDOM from 'react-dom/client'
import { Popup } from './Popup'
import './index.css'

// The following of the file brings all the pieces together 
// and injects the final product into index.html in the public folder.

ReactDOM.createRoot(document.getElementById('app')).render(
  <React.StrictMode>
    <Popup />
  </React.StrictMode>,
)
