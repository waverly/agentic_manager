import React, { useState } from "react";
import ChatMessage from "./ChatMessage";
import { useChat } from "../context/useChatContext";
import { Message } from "../types/chat";

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
  const { messages, addMessage } = useChat();
  const [inputText, setInputText] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    // Add user message
    const userMessage: Message = {
      role: "user",
      type: "text",
      content: {
        sections: [
          {
            points: [
              {
                text: inputText,
                citations: [],
              },
            ],
          },
        ],
      },
    };

    // Add user message
    addMessage(userMessage);
    setInputText("");

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: inputText }),
      });

      const data = await response.json();

      console.log("data", data);

      // Add assistant response
      addMessage({
        role: "assistant",
        type: "structured_response",
        content: data || {
          title: "Response",
          sections: [
            {
              points: [data.response || "No response content"],
            },
          ],
        },
      });
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return (
    <main className="main-content">
      <div className="inner-content">
        <div className="intro-text">
          <h1>Hi Bianca,</h1>
          <p className="subtitle">How can I help you today?</p>
        </div>

        <div className="prompts-wrapper">
          <div className="prompts-container">
            {messages.length > 1 ? (
              <div className="response-container">
                {messages.map((message, index) => (
                  <ChatMessage
                    key={index}
                    content={message.content}
                    role={message.role}
                    type={message.type}
                  />
                ))}
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
        </div>
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
