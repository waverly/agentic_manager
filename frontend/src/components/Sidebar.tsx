import React from "react";
import MyTeamIcon from "../images/icon-team.svg";
import TasksIcon from "../images/icon-tasks.svg";
import OneOnOneIcon from "../images/icon-11s.svg";
import FeedbackIcon from "../images/icon-feedback.svg";
import UpdatesIcon from "../images/icon-updates.svg";
import TimeOffIcon from "../images/icon-timeoff.svg";
import GoalsIcon from "../images/icon-goals.svg";
import GrowIcon from "../images/icon-grow.svg";
import CompensationIcon from "../images/icon-comp.svg";
import EngagementIcon from "../images/icon-engagement.svg";
import ReviewsIcon from "../images/icon-reviews.svg";
import OrgChartIcon from "../images/icon-orgchart.svg";
import DepartmentsIcon from "../images/icon-department.svg";
// import HelpIcon from "../images/icon-help.svg";

const menuItems = [
  { icon: MyTeamIcon, text: "My team" },
  { icon: TasksIcon, text: "Tasks" },
  { icon: OneOnOneIcon, text: "1:1s" },
  { icon: FeedbackIcon, text: "Feedback" },
  { icon: UpdatesIcon, text: "Updates" },
  { icon: TimeOffIcon, text: "Time off" },
  { icon: GoalsIcon, text: "Goals" },
  { icon: GrowIcon, text: "Grow" },
  { icon: CompensationIcon, text: "Compensation" },
  { icon: EngagementIcon, text: "Engagement" },
  { icon: ReviewsIcon, text: "Reviews" },
  { icon: MyTeamIcon, text: "Directory" },
  { icon: OrgChartIcon, text: "Org chart" },
  { icon: DepartmentsIcon, text: "Departments" },
];

const Sidebar = () => (
  <div className="sidebar">
    <div className="profile-section">
      <div className="profile-card">
        <img src="src/images/BiancaBerg.png" alt="Profile" className="avatar" />
        <span>Bianca B</span>
      </div>
    </div>
    <nav>
      {menuItems.map((item, index) => (
        <div key={index} className="menu-item">
          <img src={item.icon} alt={item.text} className="icon" />
          <span>{item.text}</span>
        </div>
      ))}
    </nav>
    {/* <div className="help-section">
      <div className="menu-item">
        <img src={HelpIcon} alt="Help" className="icon" />
        <span>Help</span>
      </div>
      <button className="switch-admin">Switch to admin</button>
    </div> */}
  </div>
);

export default Sidebar;
