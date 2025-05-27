# AI Photo Assistant Frontend

A React-based chat interface for interacting with your AI photo assistant.

## Features

- 💬 Clean, modern chat interface
- 🤖 Real-time messaging with AI assistant
- 📱 Responsive design for mobile and desktop
- ⚡ Fast and intuitive user experience
- 🎨 Beautiful gradient design with smooth animations

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The application will open in your browser at `http://localhost:3000`.

### Backend Connection

The frontend is configured to connect to the backend API at `http://localhost:8000`. Make sure your backend server is running before using the chat interface.

## Usage

1. Type your message in the input field at the bottom
2. Press Enter or click the send button (📤) to send your message
3. Wait for the AI assistant to respond
4. Continue the conversation!

### Example Questions

- "When did I go to the forest?"
- "Show me photos of dogs"
- "What photos do I have from last summer?"
- "Find pictures of my family"

## Available Scripts

- `npm start` - Runs the app in development mode
- `npm test` - Launches the test runner
- `npm run build` - Builds the app for production
- `npm run eject` - Ejects from Create React App (one-way operation)

## Technologies Used

- React 18
- Axios for HTTP requests
- CSS3 with modern features
- Create React App for build tooling

## API Integration

The frontend communicates with the backend using the `/chat` endpoint:

**Request Format:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "input_text", "text": "Your message here"}
      ]
    }
  ]
}
```

**Response Format:**
```json
{
  "success": true,
  "response": {
    "role": "assistant",
    "content": [
      {"type": "input_text", "text": "AI response here"}
    ]
  }
}
```
