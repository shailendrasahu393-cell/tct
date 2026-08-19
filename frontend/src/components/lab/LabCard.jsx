import { ArrowUpRight, GraduationCap } from "lucide-react";
import { Link } from "react-router-dom";
export default function LabCard({ lab }) {
  return (
    <article className={`lab-card lab-card--${lab.color}`}>
      <div className="lab-card__icon">
        <GraduationCap />
      </div>
      <div>
        <p className="eyebrow">TCT Lab</p>
        <h3>{lab.name}</h3>
        <p>{lab.description}</p>
      </div>
      <div className="lab-card__bottom">
        <span>
          Class: <b>{lab.className}</b>
        </span>
        <Link to={`/lab/${lab.id}`}>
          Enter lab <ArrowUpRight size={16} />
        </Link>
      </div>
    </article>
  );
}
