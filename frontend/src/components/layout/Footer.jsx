import { Code2, ExternalLink } from "lucide-react";
export default function Footer() {
  return (
    <footer>
      <div className="footer-brand">
        <Code2 /> TCT LAB PORTAL
      </div>
      <div
        className="footer-contributors"
        style={{ display: "grid", gap: "3px" }}
      >
        <b>Contributions</b>
        <span>Idea Founder &amp; Frontend Developer</span>
        <span>Backend Developer &amp; Security Tester</span>
      </div>
      <div className="footer-socials" style={{ display: "grid", gap: "5px" }}>
        <a
          href="https://www.linkedin.com/in/shailendrasahu-/"
          target="_blank"
          rel="noopener noreferrer"
        >
          <ExternalLink size={14} /> Shailendra Sahu
        </a>
        <a
          href="https://www.linkedin.com/in/anadisharma15/"
          target="_blank"
          rel="noopener noreferrer"
        >
          <ExternalLink size={14} /> Anadi Sharma
        </a>
      </div>
      <span>© 2026 TCT Lab Portal</span>
    </footer>
  );
}
