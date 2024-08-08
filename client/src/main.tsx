import React from 'react'
import ReactDOM from 'react-dom/client'
import Routing from './Routing'
import './index.css'
import './i18n';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Routing />
  </React.StrictMode>,
)
