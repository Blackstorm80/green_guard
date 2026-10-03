import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import App from "./App";
import { initialiserTheme } from "./lib/theme";
import "./index.css";
import "./assets/styles/print.css";

// Avant le premier rendu : évite un flash de thème (pas de script inline possible avec la CSP)
initialiserTheme();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
