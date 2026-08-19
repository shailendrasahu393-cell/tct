import { Code2, Link2, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";
import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";

export default function About() {
  return (
    <>
      <Navbar />
      <main className="page-state about-page">
        <div className="about-page__icon">
          <Code2 size={32} />
        </div>
        <p className="eyebrow">About TCT Lab Portal</p>
        <h1>Technical Computer Training</h1>
        <p className="about-page__lead">
          TCT stands for Technical Computer Training. This portal gives students
          one clear place to find shared lab links, coding exercises, contests,
          and practice resources from their faculty.
        </p>
        <div className="about-page__grid">
          <section>
            <Link2 size={22} />
            <h2>Find shared lab links</h2>
            <p>
              The goal is simple: organize the links shared for each class so
              students can find the right resource without searching through
              scattered messages.
            </p>
          </section>
          <section>
            <ShieldCheck size={22} />
            <h2>Privacy first</h2>
            <p>
              This website is not a WhatsApp login system and does not need
              access to WhatsApp accounts, chats, or contacts. It is only a
              resource directory for approved lab links.
            </p>
          </section>
        </div>
        <Link className="button button--primary" to="/#labs">
          Explore labs
        </Link>
      </main>
      <Footer />
    </>
  );
}
