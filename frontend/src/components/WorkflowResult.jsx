import { MdCheckCircle, MdError, MdChat } from 'react-icons/md';
import './WorkflowResult.css';

function WorkflowResult({ result, error }) {
  if (error) {
    return (
      <div className="workflow-result-container error">
        <div className="result-header">
          <MdError className="result-icon error-icon" />
          <h3>Error</h3>
        </div>
        <div className="result-content">
          <p className="error-message">{error}</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return null;
  }

  return (
    <div className="workflow-result-container success">
      <div className="result-header">
        <MdCheckCircle className="result-icon success-icon" />
        <h3>Finn's Response</h3>
      </div>
      
      {result.output && (
        <div className="result-content">
          <div className="output-section">
            <h4>
              <MdChat className="section-icon" />
              Response
            </h4>
            <div className="output-text">
              {result.output}
            </div>
          </div>
        </div>
      )}
      
      {result.messages && result.messages.length > 0 && (
        <div className="messages-section">
          <h4>Conversation History</h4>
          <div className="messages-list">
            {result.messages.map((message, index) => (
              <div key={index} className={`message ${message.type || 'unknown'}`}>
                <div className="message-type">
                  {message.type === 'human' ? 'You' : 'Finn'}
                </div>
                <div className="message-content">
                  {typeof message.content === 'string' ? message.content : JSON.stringify(message.content)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default WorkflowResult; 