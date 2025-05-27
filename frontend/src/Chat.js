import React, { useState } from 'react';
import axios from 'axios';
import './Chat.css';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      role: 'user',
      content: [{ type: 'input_text', text: inputMessage }]
    };

    // Add user message to chat
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Send to backend
      const response = await axios.post('http://localhost:8000/chat', {
        messages: [...messages, userMessage]
      });

      if (response.data.success) {
        // Add AI response to chat
        setMessages(prev => [...prev, response.data.response]);
      } else {
        // Handle error
        const errorMessage = {
          role: 'assistant',
          content: [{ type: 'input_text', text: 'Sorry, I encountered an error. Please try again.' }]
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        role: 'assistant',
        content: [{ type: 'input_text', text: 'Sorry, I could not connect to the server. Please try again.' }]
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getMessageText = (message) => {
    const textContent = message.content.find(item => item.type === 'input_text');
    return textContent ? textContent.text : '';
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>AI Photo Assistant</h1>
        <p>Ask me about your photos and memories!</p>
      </div>
      
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>👋 Hello! I'm your AI photo assistant. Ask me anything about your photos!</p>
            <p>Try asking: "When did I go to the forest?" or "Show me photos of dogs"</p>
          </div>
        )}
        
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            <div className="message-content">
              {getMessageText(message)}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="message assistant">
            <div className="message-content loading">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
              Thinking...
            </div>
          </div>
        )}
      </div>
      
      <div className="chat-input">
        <div className="input-container">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me about your photos..."
            disabled={isLoading}
            rows="1"
          />
          <button 
            onClick={sendMessage} 
            disabled={isLoading || !inputMessage.trim()}
            className="send-button"
          >
            {isLoading ? '⏳' : '📤'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chat; 