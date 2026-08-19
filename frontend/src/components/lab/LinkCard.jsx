import { ArrowUpRight, CalendarDays } from "lucide-react";
export default function LinkCard({ link }) {
  return (
    <article className="link-card">
      <div>
        <span className="link-card__date">
          <CalendarDays size={14} />
          {new Date(`${link.date}T00:00:00`).toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
          })}
        </span>
        <h3>{link.title}</h3>
        <p>{link.description}</p>
      </div>
      <a href={link.url} target="_blank" rel="noopener noreferrer">
        Open problem <ArrowUpRight size={16} />
      </a>
    </article>
  );
}
