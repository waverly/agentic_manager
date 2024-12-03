import React, { useState } from "react";

const AssistantPrompt = ({
  title,
  description,
}: {
  title: string;
  description: string;
}) => (
  <div className="assistant-prompt">
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
    >
      <path d="M8 2L10 6L14 7L11 10L12 14L8 12L4 14L5 10L2 7L6 6L8 2Z" />
    </svg>
    <div>
      <div className="prompt-title">{title}</div>
      <p className="prompt-description">{description}</p>
    </div>
  </div>
);

const MainContent = () => {
  const [inputText, setInputText] = useState("");
  const [response, setResponse] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: inputText }),
      });

      const data = await res.json();
      setResponse(data.response);
      setInputText("");
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return (
    <main className="main-content">
      <h1>Hi Bianca,</h1>
      <p className="subtitle">How can I help you today?</p>

      <div className="prompts-container">
        {response ? (
          <div className="response-container">
            <p>{response}</p>
          </div>
        ) : (
          <>
            <AssistantPrompt
              title="Ask Assistant a question..."
              description="Ask about company programs, career growth, or Lattice best practices."
            />
            <AssistantPrompt
              title="Ask Assistant to summarize..."
              description="Feedback, notes, goal progress, team sentiment..."
            />
            <AssistantPrompt
              title="Ask Assistant for recommendations..."
              description="On your growth areas or goals, how to coach your team..."
            />
            <AssistantPrompt
              title="Ask Assistant for help writing..."
              description="Draft feedback, reviews, updates, growth areas..."
            />
          </>
        )}
      </div>

      <form onSubmit={handleSubmit} className="input-container">
        <div className="input-icons">
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            stroke="#94a3b8"
          >
            <path d="M8 2L10 6L14 7L11 10L12 14L8 12L4 14L5 10L2 7L6 6L8 2Z" />
          </svg>
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            stroke="#94a3b8"
          >
            <path d="M6.5 7.5C6.5 6.12 7.62 5 9 5L11.5 5C12.88 5 14 6.12 14 7.5C14 8.88 12.88 10 11.5 10L10 10M9.5 8.5C9.5 9.88 8.38 11 7 11L4.5 11C3.12 11 2 9.88 2 8.5C2 7.12 3.12 6 4.5 6L6 6" />
          </svg>
          <span className="at-symbol">@</span>
        </div>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Ask a question..."
          className="question-input"
        />
        <button
          type="submit"
          className={`send-button ${inputText ? "active" : ""}`}
        >
          →
        </button>
      </form>
    </main>
  );
};

export default MainContent;
