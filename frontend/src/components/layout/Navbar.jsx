import { Link, NavLink } from "react-router-dom";
import { Code2, LockKeyhole, Menu, X } from "lucide-react";
import { useState } from "react";
export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="navbar">
      <Link className="brand" to="/">
        <span>
          <Code2 size={21} />
        </span>
        TCT <b>LAB</b>
      </Link>
      <button
        className="mobile-nav"
        type="button"
        aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
        aria-expanded={menuOpen}
        onClick={() => setMenuOpen((open) => !open)}
      >
        {menuOpen ? <X size={22} /> : <Menu size={22} />}
      </button>
      <nav className={`navbar__links${menuOpen ? " is-open" : ""}`}>
        <NavLink to="/" onClick={() => setMenuOpen(false)}>
          Home
        </NavLink>
        <a href="/#labs" onClick={() => setMenuOpen(false)}>
          Labs
        </a>
        <Link to="/about" onClick={() => setMenuOpen(false)}>
          About
        </Link>
        <Link className="admin-login" to="/admin/login">
          <LockKeyhole size={16} />
          Admin Login
        </Link>
      </nav>
    </header>
  );
}
