import { useState } from "react";
import API from "./api";
import "./App.css";

function App() {
  const [name, setName] = useState("");
  const [profile, setProfile] = useState(null);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const login = async () => {
    if (!name.trim()) {
      setMessage("Please enter your name.");
      return;
    }

    try {
      const response = await API.get(`/career-profile/${name}`);

      setProfile(response.data.profile);
      setMessage("");

    } catch (error) {
      console.log("Login error:", error);

      setMessage(
        error.response
          ? `Backend error: ${error.response.status}`
          : "Unable to connect to the backend."
      );
    }
  };

  const askAI = async () => {
    if (!question.trim() || loading) {
      return;
    }

    const userMessage = question.trim();

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: userMessage,
      },
    ]);

    setQuestion("");
    setLoading(true);

    try {
      const response = await API.post("/ask-ai", {
        name: name,
        question: userMessage,
      });

      setMessages((previous) => [
        ...previous,
        {
          role: "ai",
          content: response.data.answer,
        },
      ]);

    } catch (error) {
      console.log("AI error:", error);

      setMessages((previous) => [
        ...previous,
        {
          role: "ai",
          content: "Sorry, I couldn't connect to the AI right now.",
        },
      ]);

    } finally {
      setLoading(false);
    }
  };

  if (!profile) {
    return (
      <div className="login-page">

        <div className="login-card">

          <div className="logo">
            ✦
          </div>

          <h1>AI Career Companion</h1>

          <p>
            Your personal AI-powered career assistant.
          </p>

          <input
            type="text"
            placeholder="Enter your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                login();
              }
            }}
          />

          <button onClick={login}>
            Continue
          </button>

          {message && (
            <div className="error-message">
              {message}
            </div>
          )}

        </div>

      </div>
    );
  }

  return (
    <div className="chat-page">

      <header className="chat-header">

        <div className="brand">
          <div className="brand-icon">
            ✦
          </div>

          <div>
            <h2>AI Career Companion</h2>
            <span>Career Assistant</span>
          </div>
        </div>

        <div className="user-name">
          {profile.name}
        </div>

      </header>


      <main className="chat-area">

        {messages.length === 0 && (
          <div className="welcome">

            <div className="welcome-icon">
              ✦
            </div>

            <h1>
              Hey {profile.name} 👋
            </h1>

            <p>
              I'm your AI Career Companion.
              <br />
              Ask me anything about your career.
            </p>

          </div>
        )}


        <div className="messages">

          {messages.map((item, index) => (
            <div
              key={index}
              className={`message-row ${item.role}`}
            >

              <div className="message-bubble">
                {item.content}
              </div>

            </div>
          ))}


          {loading && (
            <div className="message-row ai">

              <div className="message-bubble typing">
                AI is thinking...
              </div>

            </div>
          )}

        </div>

      </main>


      <div className="chat-input-area">

        <div className="chat-input">

          <input
            type="text"
            placeholder="Ask anything about your career..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                askAI();
              }
            }}
          />

          <button onClick={askAI}>
            ➤
          </button>

        </div>

      </div>

    </div>
  );
}

export default App;