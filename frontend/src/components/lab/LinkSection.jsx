import { Flame, MonitorCog, Target } from "lucide-react";
import LinkCard from "./LinkCard";
const iconMap = {
  Contest: Flame,
  "Daily Lab": MonitorCog,
  "Single Problem": Target,
};
export default function LinkSection({ title, links }) {
  if (!links.length) return null;
  const Icon = iconMap[title] || Target;
  return (
    <section className="link-section">
      <div className="section-title">
        <span>
          <Icon size={19} />
        </span>
        <div>
          <p className="eyebrow">
            {links.length} {links.length === 1 ? "resource" : "resources"}
          </p>
          <h2>{title}</h2>
        </div>
      </div>
      <div className="link-grid">
        {links.map((link) => (
          <LinkCard key={link.id} link={link} />
        ))}
      </div>
    </section>
  );
}
