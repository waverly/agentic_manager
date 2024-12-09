import React from "react";

const Sidebar = () => {
  return (
    <aside className="right-sidebar">
      <div className="date">Wednesday, November 18</div>

      <div className="highlights-card">
        <div className="section-label">HIGHLIGHTS</div>
        <div className="card-content">
          <div className="recent-work">
            <h2>Recent work</h2>
            <p>
              The team started working on{" "}
              <a href="#" className="mention">
                @Project Galileo
              </a>
              , they've closed out 4{" "}
              <a href="#" className="mention">
                @JIRA
              </a>{" "}
              epics and are preparing to start dogfooding.
            </p>
          </div>

          <div className="sentiment">
            <h2>Sentiment</h2>
            <div className="sentiment-graph">
              <svg width="100%" height="40" viewBox="0 0 280 40" fill="none">
                <path
                  d="M0 35L20 32L40 30L60 28L80 25L100 28L120 25L140 20L160 15L180 18L200 15L220 10L240 8L260 5L280 2"
                  stroke="url(#gradient)"
                  strokeWidth="2"
                  fill="none"
                />
                <defs>
                  <linearGradient id="gradient" x1="0" y1="0" x2="280" y2="0">
                    <stop offset="0%" stopColor="#818CF8" />
                    <stop offset="100%" stopColor="#6366F1" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <ul>
              <li>Your team's sentiment is trending lower</li>
              <li>
                Fewer folks feel they can bring up tough issues on the team
              </li>
              <li>Jenny and Luna each spent more than 15 hours in Meetings</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="highlights-card">
        <div className="section-label">TASKS</div>
        <div className="task-card">
          <div className="task-icon">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path
                d="M2 4C2 2.89543 2.89543 2 4 2H16C17.1046 2 18 2.89543 18 4V16C18 17.1046 17.1046 18 16 18H4C2.89543 18 2 17.1046 2 16V4Z"
                fill="#F3F4F6"
              />
              <path
                d="M6 10L9 13L14 7"
                stroke="#6366F1"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <span>Q2 360 Review cycle</span>
          <svg
            className="arrow"
            width="20"
            height="20"
            viewBox="0 0 20 20"
            fill="none"
          >
            <path
              d="M8 4L14 10L8 16"
              stroke="#9CA3AF"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
