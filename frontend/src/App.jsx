import { useState } from 'react';
import { MdEmail, MdSubscriptions, MdChat } from 'react-icons/md';
import WorkflowForm from './components/WorkflowForm';
import WorkflowResult from './components/WorkflowResult';
import Chat from './components/Chat';
import apiClient from './services/api';
import './App.css';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [showWorkflow, setShowWorkflow] = useState(false);
  const [showChat, setShowChat] = useState(false);

  const handleWorkflowSubmit = async (message) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await apiClient.runWorkflow(message);
      setResult(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMenuClick = (action) => {
    if (action === 'chat') {
      setShowChat(true);
      setShowWorkflow(false);
    } else {
      setShowWorkflow(true);
      setShowChat(false);
    }
    setResult(null);
    setError(null);
    
    // Pre-fill with suggested prompts based on the action
    const prompts = {
      'financial-scan': 'Help me analyze my financial situation and identify areas for improvement.',
      'optimize-subscriptions': 'Help me review and optimize my subscription services to save money.'
    };
    
    // You could auto-submit these or just show the form
    // For now, just show the workflow form
  };

  const handleBackToMenu = () => {
    setShowWorkflow(false);
    setShowChat(false);
    setResult(null);
    setError(null);
  };

  return (
    <>
      <div>
        <h1>Finn - your financial buddy</h1>
      </div>
      
      {!showWorkflow && !showChat ? (
        <div className="menu-container">
          <div className="menu-grid">
            <button 
              className="menu-item"
              onClick={() => handleMenuClick('financial-scan')}
            >
              <MdEmail className="menu-icon" />
              <span>Financial Impact Scan</span>
            </button>
            
            <button 
              className="menu-item"
              onClick={() => handleMenuClick('optimize-subscriptions')}
            >
              <MdSubscriptions className="menu-icon" />
              <span>Optimize Subscriptions</span>
            </button>
          </div>
          
          <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button 
              className="menu-item"
              onClick={() => handleMenuClick('chat')}
              style={{ maxWidth: '300px' }}
            >
              <MdChat className="menu-icon" />
              <span>Chat with Finn</span>
            </button>
            
            <button 
              className="menu-item"
              onClick={() => setShowWorkflow(true)}
              style={{ maxWidth: '300px' }}
            >
              <span>Ask Finn Anything</span>
            </button>
          </div>
        </div>
      ) : showChat ? (
        <Chat onBack={handleBackToMenu} />
      ) : (
        <div className="workflow-container">
          <WorkflowForm 
            onSubmit={handleWorkflowSubmit}
            isLoading={isLoading}
          />
          
          <WorkflowResult 
            result={result}
            error={error}
          />
          
          <div style={{ textAlign: 'center', marginTop: '2rem' }}>
            <button 
              className="menu-item"
              onClick={handleBackToMenu}
              style={{ maxWidth: '200px', padding: '0.75rem 1.5rem' }}
            >
              Back to Menu
            </button>
          </div>
        </div>
      )}
      
      <p className="read-the-docs">
        Your personal financial companion
      </p>
    </>
  );
}

export default App;
