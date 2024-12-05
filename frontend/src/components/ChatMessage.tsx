import { Message } from "../types/chat";
import InsightCard from "./InsightCard";

const ChatMessage = ({ content, role, type, simpleMessage }: Message) => {
  if (role === "user") {
    return <div className={`chat-message ${role}`}>{simpleMessage}</div>;
  } else if (type === "SimpleMessage") {
    console.log("simpleMessage", simpleMessage);
    return <div className={`chat-message ${role}`}>{simpleMessage}</div>;
  } else if (!content || type === "unknown") {
    console.log("there was no content or type was unknown", content, type);
    return <div className={`chat-message ${role}`}>{simpleMessage}</div>;
  }

  const { title, sections, insights, conclusion } = content;

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
            <InsightCard key={index} insight={insight} />
          ))}{" "}
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
