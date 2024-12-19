import React from "react";
import "./App.css";
import Sidebar from "./components/Sidebar";
import MainContent from "./components/MainContent";
import RightPanel from "./components/RightPanel";
import { ChatProvider } from "./context/ChatContext";

function App() {
  return (
    <div className="app">
      <Sidebar />
      <ChatProvider>
        <MainContent />
      </ChatProvider>
      {/* <RightPanel /> */}
    </div>
  );
}

export default App;
