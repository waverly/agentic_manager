import { useChat } from "../context/useChatContext";
import { Message } from "../types/chat";
import InsightCard from "./InsightCard";

export interface ChatMessageProps extends Message {
  isLoading?: boolean;
  setIsLoading: (loading: boolean) => void;
}

const ChatMessage = ({
  content,
  role,
  type,
  simpleMessage,
  setIsLoading,
}: ChatMessageProps) => {
  const { addMessage } = useChat();

  if (role === "user") {
    return <div className={`chat-message ${role}`}>{simpleMessage}</div>;
  } else if (type === "SimpleMessage") {
    console.log("simpleMessage", simpleMessage);
    return <div className={`chat-message ${role}`}>{simpleMessage}</div>;
  } else if (!content || type === "unknown") {
    console.log("there was no content or type was unknown", content, type);
    return <div className={`chat-message ${role}`}>{simpleMessage}</div>;
  }

  const { title, sections, insights, conclusion, action_items, summary } =
    content;

  const handleActionItemClick = (actionItem: string) => {
    addMessage({
      role: "user",
      type: "plain_text",
      simpleMessage: actionItem,
    });

    // Optional: Trigger the chat API call right away
    handleChatMessage(actionItem);
  };

  const handleChatMessage = async (message: string) => {
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message }),
      });

      const data = await response.json();
      addMessage({
        role: "assistant",
        simpleMessage: data?.simpleMessage,
        content: data || null,
        type: data.type,
      });
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`chat-message ${role} ${type}`}>
      {title && <h2 className="message-title">{title}</h2>}
      {summary && <p className="section-summary">{summary}</p>}
      {sections &&
        sections?.length > 0 &&
        sections?.map((section, index) => {
          const { heading, points } = section;

          return (
            <div key={index} className={`message-section`}>
              {heading && <h4 className="section-heading">{heading}</h4>}
              {points && (
                <ul className={`section-points-wrapper`}>
                  {points.map((point, pointIndex) => (
                    <li key={pointIndex}>
                      {point?.text}
                      {point?.citations && point.citations.length > 0 && (
                        <span className="citation-number">
                          {point.citations.length}
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          );
        })}
      {insights && (
        <div className="insights-wrapper">
          {insights.map((insight, index) => (
            <InsightCard
              handleActionItemClick={handleActionItemClick}
              key={index}
              insight={insight}
            />
          ))}{" "}
        </div>
      )}
      {action_items && (
        <div className="action-items-section">
          <h4 className="section-heading">Action Items</h4>
          <div className="action-items-button-wrapper">
            {action_items.map((item, index) => (
              <button
                onClick={() => handleActionItemClick(item)}
                key={index}
                className="action-item-button"
              >
                {item}
              </button>
            ))}
          </div>
        </div>
      )}
      {conclusion && (
        <div className="conclusion-section">
          {conclusion[0]?.heading && (
            <h4 className="section-heading">{conclusion[0].heading}</h4>
          )}
          {conclusion[0]?.points && (
            <ul>
              {conclusion[0].points.map((point, pointIndex) => (
                <li key={pointIndex}>
                  {point?.text}
                  {point?.citations && point.citations.length > 0 && (
                    <span className="citation-number">
                      {point.citations.length}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};

export default ChatMessage;
