import { Message } from "../types/chat";
import InsightCard from "./InsightCard";

const ChatMessage = ({ content, role, type }: Message) => {
  console.log("content", content);
  console.log(content);
  const { title, sections, insights } = content;

  return (
    <div className={`chat-message ${role}`}>
      {title && <h2 className="message-title">{title}</h2>}
      {sections &&
        sections?.length > 0 &&
        sections?.map((section, index) => {
          const { heading, points } = section;

          return (
            <div key={index} className="message-section">
              {heading && <h4 className="section-heading">{heading}</h4>}
              {points && (
                <ul>
                  {points.map((point, pointIndex) => (
                    <li key={pointIndex}>{point?.text}</li>
                  ))}
                </ul>
              )}
            </div>
          );
        })}
      {insights && (
        <div className="insights-wrapper">
          {insights.map((insight, index) => (
            <InsightCard key={index} insight={insight} />
          ))}{" "}
        </div>
      )}
    </div>
  );
};

export default ChatMessage;
