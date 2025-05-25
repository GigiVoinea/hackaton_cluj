import { useState } from 'react';
import { MdSend, MdClear } from 'react-icons/md';
import './WorkflowForm.css';

function WorkflowForm({ onSubmit, isLoading }) {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSubmit(message.trim());
    }
  };

  const handleClear = () => {
    setMessage('');
  };

  return (
    <div className="workflow-form-container">
      <h2>Ask Finn Anything</h2>
      <form onSubmit={handleSubmit} className="workflow-form">
        <div className="input-group">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask me about your finances, subscriptions, or any financial advice..."
            className="message-input"
            rows={4}
            disabled={isLoading}
          />
          <div className="button-group">
            <button
              type="button"
              onClick={handleClear}
              className="clear-button"
              disabled={isLoading || !message.trim()}
            >
              <MdClear className="button-icon" />
              Clear
            </button>
            <button
              type="submit"
              className="submit-button"
              disabled={isLoading || !message.trim()}
            >
              <MdSend className="button-icon" />
              {isLoading ? 'Processing...' : 'Send'}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}

export default WorkflowForm; 