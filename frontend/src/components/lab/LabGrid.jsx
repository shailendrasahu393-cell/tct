import LabCard from "./LabCard";
export default function LabGrid({ labs }) {
  return (
    <div className="lab-grid">
      {labs.map((lab) => (
        <LabCard key={lab.id} lab={lab} />
      ))}
    </div>
  );
}
