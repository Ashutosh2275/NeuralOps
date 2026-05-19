import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider } from "./contexts/ThemeContext";
import { PlatformProvider } from "./contexts/PlatformContext";
import { SettingsProvider } from "./contexts/SettingsContext";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider>
      <SettingsProvider>
        <PlatformProvider>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </PlatformProvider>
      </SettingsProvider>
    </ThemeProvider>
  </React.StrictMode>
);
