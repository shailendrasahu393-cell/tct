import { Link, NavLink } from 'react-router-dom';
import { Code2, LockKeyhole } from 'lucide-react';
export default function Navbar() { return <header className="navbar"><Link className="brand" to="/"><span><Code2 size={21} /></span>TCT <b>LAB</b></Link><nav className="navbar__links"><NavLink to="/">Home</NavLink><a href="/#labs">Labs</a><Link to="/about">About</Link><Link className="admin-login" to="/admin/login"><LockKeyhole size={16} />Admin Login</Link></nav></header>; }
