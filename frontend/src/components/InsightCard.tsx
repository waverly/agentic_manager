import React from "react";
import { Insight } from "../types/chat";

const InsightCard: React.FC<{ insight: Insight }> = ({ insight }) => {
  return (
    <div className="insight-card">
      <div className="insight-content">
        <strong>{insight.title}</strong>
        <p>{insight.description}</p>
      </div>
      <div className="insight-actions">
        {insight.actions?.map((action, index) => (
          <button key={index} className="action-button">
            <span className="diamond">◆</span>
            {action}
          </button>
        ))}
      </div>
    </div>
  );
};

export default InsightCard;
