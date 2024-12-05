import React from "react";

const menuItems = [
  { icon: "👥", text: "My team" },
  { icon: "✓", text: "Tasks" },
  { icon: "1:1", text: "1:1s" },
  { icon: "💭", text: "Feedback" },
  { icon: "🔄", text: "Updates" },
  { icon: "📅", text: "Time off" },
  { icon: "🎯", text: "Goals" },
  { icon: "📈", text: "Grow" },
  { icon: "💰", text: "Compensation" },
  { icon: "❤️", text: "Engagement" },
  { icon: "📋", text: "Reviews" },
  { icon: "👥", text: "Directory" },
  { icon: "📊", text: "Org chart" },
  { icon: "🏢", text: "Departments" },
];

const Sidebar = () => (
  <div className="sidebar">
    <div className="profile-section">
      <div className="profile-card">
        <img
          src="src/images/BiancaBerg.png"
          alt="Profile"
          className="avatar"
        />
        <span>Bianca B</span>
      </div>
    </div>
    <nav>
      {menuItems.map((item, index) => (
        <div key={index} className="menu-item">
          <span className="icon">{item.icon}</span>
          <span>{item.text}</span>
        </div>
      ))}
    </nav>
    <div className="help-section">
      <div className="menu-item">
        <span className="icon">❓</span>
        <span>Help</span>
      </div>
      <button className="switch-admin">Switch to admin</button>
    </div>
  </div>
);

export default Sidebar;
