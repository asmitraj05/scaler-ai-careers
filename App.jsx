import { useState } from "react";

export default function App() {
  const [clicked, setClicked] = useState(false);

  const styles = {
    wrapper: {
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
      fontFamily: "'Segoe UI', system-ui, sans-serif",
    },
    card: {
      textAlign: "center",
      padding: "60px 80px",
      borderRadius: "20px",
      background: "rgba(255, 255, 255, 0.05)",
      backdropFilter: "blur(12px)",
      border: "1px solid rgba(255, 255, 255, 0.1)",
      boxShadow: "0 25px 50px rgba(0, 0, 0, 0.4)",
    },
    heading: {
      fontSize: "3.5rem",
      fontWeight: "800",
      margin: "0 0 12px",
      background: "linear-gradient(90deg, #e0c3fc, #8ec5fc)",
      WebkitBackgroundClip: "text",
      WebkitTextFillColor: "transparent",
      backgroundClip: "text",
      letterSpacing: "-1px",
    },
    subtitle: {
      fontSize: "1.15rem",
      color: "rgba(255, 255, 255, 0.6)",
      margin: "0 0 40px",
      fontWeight: "400",
    },
    button: {
      padding: "14px 36px",
      fontSize: "1rem",
      fontWeight: "600",
      border: "none",
      borderRadius: "50px",
      cursor: "pointer",
      background: clicked
        ? "linear-gradient(135deg, #43e97b, #38f9d7)"
        : "linear-gradient(135deg, #8ec5fc, #e0c3fc)",
      color: "#1a1a2e",
      boxShadow: "0 8px 24px rgba(142, 197, 252, 0.35)",
      transition: "transform 0.15s ease, box-shadow 0.15s ease",
    },
  };

  return (
    <div style={styles.wrapper}>
      <div style={styles.card}>
        <h1 style={styles.heading}>Hello, World!</h1>
        <p style={styles.subtitle}>
          {clicked ? "Thanks for clicking! You're awesome." : "Welcome to your first React page."}
        </p>
        <button
          style={styles.button}
          onClick={() => setClicked((prev) => !prev)}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = "scale(1.05)";
            e.currentTarget.style.boxShadow = "0 12px 32px rgba(142, 197, 252, 0.5)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "scale(1)";
            e.currentTarget.style.boxShadow = "0 8px 24px rgba(142, 197, 252, 0.35)";
          }}
        >
          {clicked ? "Reset" : "Click Me"}
        </button>
      </div>
    </div>
  );
}
