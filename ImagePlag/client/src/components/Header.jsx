import React from "react";
import "./Header.css";

export default function Header() {
  return (
    <header className="header">
      <div className="header__mark">
        <span className="header__glyph">◈</span>
        <span className="header__word">Evidentia</span>
      </div>
      <span className="header__tag mono">originality register</span>
    </header>
  );
}
