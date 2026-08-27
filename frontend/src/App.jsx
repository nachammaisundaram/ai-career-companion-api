import { useState } from "react";
import API from "./api";
import "./App.css";

function App() {
  const [name, setName] = useState("");
  const [message, setMessage] = useState("");
  const [profile, setProfile] = useState(null);
  const [recommendations, setRecommendations] = useState(null);

  const getRecommendations = async () => {
    try {
      const response = await API.post(`/recommend-roles/${name}`);
      setRecommendations(response.data.roles);
    } catch (error) {
      console.log("Recommendation error:", error);
    }
  };

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
               setProfile(response.data.profile);
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

          {profile && (
            <div className="profile-card">
              <h2>Career Dashboard</h2>
              <p><strong>Name:</strong> {profile.name}</p>
              <p>
                <strong>Target Role:</strong>{" "}
                {profile.target_role || "Not specified"}
                </p>
                <p>
                  <strong>Education:</strong>{" "}
                  {profile.education}
                  </p>
                <p>
                  <strong>Skills:</strong>{" "}
                  {profile.skills}
                </p>
                <p>
                  <strong>Experience:</strong>{" "}
                  {profile.experience}
                </p>
                <p>
                  <strong>Interests:</strong>{" "}
                  {profile.interests}
                  </p>
            </div>
          )}
          <button onClick={getRecommendations}>
            Get Career Recommendations
          </button>

          {recommendations && (
            <div className="recommendations">
              <h2>Recommended Career Roles</h2>

              {recommendations.map((item, index) => (
                <div className="role-card" key={index}>
                  <h3>{item.role}</h3>
                  <p>{item.why}</p>
                  <strong>Skills to strengthen:</strong>

                  <ul>
                    {item.skills_to_strengthen.map((skill, skillIndex) => (
                      <li key={skillIndex}>{skill}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        
        </div>
      </div>
    </div>
  );
}

export default App;

