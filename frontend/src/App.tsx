import React from "react";
import "./App.css";
import Sidebar from "./components/Sidebar";
import MainContent from "./components/MainContent";
import RightPanel from "./components/RightPanel";

function App() {
  return (
    <div className="app">
      <Sidebar />
      <MainContent />
      <RightPanel />
    </div>
  );
}

export default App;
