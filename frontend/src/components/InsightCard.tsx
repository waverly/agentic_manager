import React from "react";
import { Insight } from "../types/chat";

const InsightCard: React.FC<{
  insight: Insight;
  handleActionItemClick: (action: string) => void;
}> = ({ insight, handleActionItemClick }) => {
  return (
    <div className="insight-card">
      <div className="insight-content">
        <strong>{insight.title}</strong>
        <p>{insight.description}</p>
      </div>
      <div className="insight-actions">
        {insight.actions?.map((action, index) => (
          <button
            onClick={() => handleActionItemClick(action)}
            key={index}
            className="action-item-button"
          >
            {action}
          </button>
        ))}
      </div>
    </div>
  );
};

export default InsightCard;
