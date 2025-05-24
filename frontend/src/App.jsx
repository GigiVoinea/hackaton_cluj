import { MdEmail, MdSubscriptions } from 'react-icons/md'
import './App.css'

function App() {
  return (
    <>
      <div>
        <h1>Finn - your financial buddy</h1>
      </div>
      
      <div className="menu-container">
        <div className="menu-grid">
          <button className="menu-item">
            <MdEmail className="menu-icon" />
            <span>Financial Impact Scan</span>
          </button>
          
          <button className="menu-item">
            <MdSubscriptions className="menu-icon" />
            <span>Optimize Subscriptions</span>
          </button>
        </div>
      </div>
      
      <p className="read-the-docs">
        Your personal financial companion
      </p>
    </>
  )
}

export default App
