// frontend/src/components/MainContent.jsx

import React, { useEffect, useState } from "react";
import { Message } from "../types/chat";

const MainContent = () => {
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]); // Store grouped messages

  const addMessage = (message: Message) => {
    setMessages((prevMessages) => [...prevMessages, message]);
  };

  // Reset messages array when component mounts
  const resetMessages = () => {
    setMessages([]);
  };

  const accumulatedStreamContent = (messageData: Message) => {
    console.log("Accumulating message:", messageData);

    setMessages((prevMessages) => {
      // For action items, always add as new message
      if (messageData.type === "action_item") {
        console.log("Adding action item:", messageData);
        return [...prevMessages, { ...messageData }];
      }

      if (prevMessages.length === 0) {
        return [{ ...messageData }];
      }

      const lastMessage = prevMessages[prevMessages.length - 1];

      // Only combine consecutive messages of the same type and role, and only for heading and body
      if (
        (messageData.type === "heading" || messageData.type === "body") &&
        lastMessage.role === messageData.role &&
        lastMessage.type === messageData.type
      ) {
        const updatedMessages = [...prevMessages];
        updatedMessages[updatedMessages.length - 1] = {
          ...lastMessage,
          content: lastMessage.content + " " + messageData.content,
        };
        return updatedMessages;
      }

      return [...prevMessages, { ...messageData }];
    });
  };

  const streamMessage = async (messageStream: Response) => {
    const reader = messageStream.body?.getReader();
    if (!reader) {
      console.log("Failed to get response body reader");
      throw new Error("Failed to get response body reader");
    }
    const decoder = new TextDecoder("utf-8");

    let accumulated = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        console.log("Stream is done!");
        break;
      }

      // Decode the chunk and accumulate
      accumulated += decoder.decode(value, { stream: true });
      console.log("accumulated", accumulated);

      // Split accumulated text into complete lines (NDJSON format)
      const lines = accumulated.split("\n");
      accumulated = lines.pop() || ""; // Save the incomplete line for next iteration

      lines.forEach((line) => {
        if (line.trim()) {
          try {
            const data = JSON.parse(line);
            console.log("Parsed NDJSON line:", data); // Debug log
            console.log("Message type:", data.type); // Debug log
            accumulatedStreamContent(data);
          } catch (err) {
            console.error("Failed to parse NDJSON chunk:", err);
            console.error("Problem line:", line); // Debug log
            setMessages((prevMessages) => [
              ...prevMessages,
              {
                role: "system",
                type: "error",
                content: "An error occurred while processing the response.",
              },
            ]);
          }
        }
      });
    }
  };

  // Render different message types
  const renderElement = (element: Message, index: number) => {
    console.log("Rendering element:", element); // Debug log
    switch (element.type) {
      case "message":
        console.log("element", element);
        return (
          <p
            className={`chat-message ${
              element.role === "assistant" ? "assistant" : "user"
            }`}
            key={index}
          >
            {element.content}
          </p>
        );

      case "title":
        return (
          <h1 className="chat-title" key={index}>
            {element.content}
          </h1>
        );

      case "heading":
        return (
          <h2 className="chat-heading" key={index}>
            {element.content}
          </h2>
        );

      case "body":
        return (
          <p
            className={`chat-message ${
              element.role === "assistant" ? "assistant" : "user"
            }`}
            key={index}
          >
            {element.content}
          </p>
        );

      case "highlight":
        return (
          <p className="chat-highlight" key={index}>
            {element.content}
          </p>
        );

      case "flag":
        return (
          <p className="chat-flag" key={index}>
            ⚠️ {element.content}
          </p>
        );

      case "action_item":
        console.log("Rendering action item:", element); // Debug log
        return (
          <button
            onClick={() => handleActionItemClick(element.content)}
            key={index}
            className="action-item-button"
          >
            {element.content}
          </button>
        );

      case "error":
        return (
          <p className="chat-error" key={index}>
            {element.content}
          </p>
        );

      default:
        return (
          <p
            className={`chat-message ${
              element.role === "assistant" ? "assistant" : "user"
            }`}
            key={index}
          >
            {element.content}
          </p>
        );
    }
  };

  // ON MOUNT
  useEffect(() => {
    resetMessages();
    setIsLoading(true);

    const handleFirstMessageStream = async () => {
      try {
        const firstMessageStream = await fetch(
          "http://localhost:8000/first_message_stream"
        );
        streamMessage(firstMessageStream);
      } catch (error) {
        console.error("Error streaming NDJSON:", error);
      } finally {
        setIsLoading(false);
      }
    };

    handleFirstMessageStream();
  }, []);

  // on submit or action item click
  const handleChatResponse = async (messageText: string) => {
    try {
      const assistantResponseData = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: messageText,
          last_system_message: messages[messages.length - 1]?.content || "",
        }),
      });
      console.log("assistantResponseData", assistantResponseData);
      streamMessage(assistantResponseData);
    } catch (error) {
      console.error("Error:", error);
      // Optionally add a system error message
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          role: "system",
          type: "error",
          content: "An error occurred while sending your message.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    setIsLoading(true);

    // Add user message
    const userMessage: Message = {
      role: "user",
      type: "message",
      content: inputText,
    };

    // Add user message to messages array
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInputText("");

    await handleChatResponse(inputText);
  };

  const handleActionItemClick = async (actionItem: string) => {
    setIsLoading(true);
    
    // Add user message showing the action being taken
    addMessage({
      role: "user",
      type: "body",
      content: actionItem,
    });

    try {
      const response = await fetch("http://localhost:8000/execute_action", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          action: actionItem,
        }),
      });

      // Stream the response
      streamMessage(response);
    } catch (error) {
      console.error("Error executing action:", error);
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          role: "system",
          type: "error",
          content: "Failed to execute action. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  console.log("messages", messages);

  useEffect(() => {
    console.log("Messages state updated:", messages);
  }, [messages]);

  return (
    <main className={`main-content`}>
      <div className={`inner-content ${isLoading ? "loading" : ""}`}>
        {!messages.length && (
          <div className="intro-text">
            <h1>Hey Bianca, Coach Lattice here!</h1>
            <p className="subtitle">
              Thought I'd stop by, since I noticed some new activity on your
              team. Please give me a moment while I gather some insights to
              share...
            </p>
          </div>
        )}

        <div className="prompts-wrapper">
          <div className="prompts-container">
            {messages.map((msg, index) => renderElement(msg, index))}
          </div>
        </div>
        {isLoading && <div className="loading-indicator">🤸</div>}
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
