import { useState } from "react";
import API from "./api";
import "./App.css";

function App() {
  const [name, setName] = useState("");
  const [message, setMessage] = useState("");

  return (
    <div className="app">
      <div className="container">
        <h1>AI Career Companion</h1>

        <p className="subtitle">
          Your personal AI-powered career assistant
        </p>

        <div className="card">
          <h2>Welcome 👋</h2>

          <p>
            Enter your name to access your personalized career dashboard.
          </p>

          <input
            type="text"
            placeholder="Enter your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />

         <button
           onClick={async () => {
             try {
               const response = await API.get(`/career-profile/${name}`);
               setMessage(response.data.message);
              } catch (error) {
                console.log("Backend error:", error);
                setMessage(
                  error.response
                  ? `Backend error: ${error.response.status}`
                  : "Unable to connect to the backend."
                );
              }
            }}
          >
            Continue
          </button>
          {message && <p className="message">{message}</p>}
        </div>
      </div>
    </div>
  );
}

export default App;
