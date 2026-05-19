import React, { createContext, useContext, useEffect, useState } from "react";

interface ThemeContextType {
  isDarkMode: boolean;
  toggleTheme: () => void;
  setTheme: (isDark: boolean) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize theme from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("sentinelops-theme");
    let initialDarkMode = true;

    if (saved !== null) {
      initialDarkMode = saved === "dark";
    } else if (typeof window !== "undefined") {
      initialDarkMode = window.matchMedia("(prefers-color-scheme: dark)").matches;
    }

    setIsDarkMode(initialDarkMode);
    setIsInitialized(true);
  }, []);

  // Apply theme to DOM when it changes
  useEffect(() => {
    if (!isInitialized) return;

    const html = document.documentElement;

    if (isDarkMode) {
      html.classList.remove("light");
      html.classList.add("dark");
      html.style.colorScheme = "dark";
    } else {
      html.classList.remove("dark");
      html.classList.add("light");
      html.style.colorScheme = "light";
    }

    // Persist to localStorage
    localStorage.setItem("sentinelops-theme", isDarkMode ? "dark" : "light");
    console.log("Theme changed to:", isDarkMode ? "dark" : "light");
  }, [isDarkMode, isInitialized]);

  const toggleTheme = () => setIsDarkMode(!isDarkMode);
  const setTheme = (isDark: boolean) => setIsDarkMode(isDark);

  return (
    <ThemeContext.Provider value={{ isDarkMode, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
};
