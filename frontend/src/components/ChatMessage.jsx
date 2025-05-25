import { MdPerson, MdSmartToy } from 'react-icons/md';
import './ChatMessage.css';

function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  const timestamp = new Date(message.timestamp).toLocaleTimeString([], { 
    hour: '2-digit', 
    minute: '2-digit' 
  });

  return (
    <div className={`message ${isUser ? 'user-message' : 'assistant-message'}`}>
      <div className="message-avatar">
        {isUser ? <MdPerson /> : <MdSmartToy />}
      </div>
      <div className="message-content">
        <div className="message-header">
          <span className="message-sender">
            {isUser ? 'You' : 'Finn'}
          </span>
          <span className="message-timestamp">{timestamp}</span>
        </div>
        <div className="message-text">
          {message.content}
        </div>
      </div>
    </div>
  );
}

export default ChatMessage; 