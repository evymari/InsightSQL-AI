import { Link } from "react-router-dom";

export default function Sidebar() {
  return (
    <aside className="w-64 bg-white shadow p-4">
      <h2 className="text-xl font-bold mb-6">Analytics Agent</h2>
      <nav className="flex flex-col gap-2">
        <Link to="/" className="text-left px-2 py-1 hover:bg-blue-600 rounded "><span>🏠 </span>Dashboard</Link>
        <Link to="/history" className="text-left px-2 py-1 hover:bg-blue-600 rounded"><span>🕘 </span>History</Link>
        <Link to="/settings" className="text-left px-2 py-1 hover:bg-blue-600 rounded"><span>⚙️ </span>Settings</Link>
        
         
        
      </nav>
    </aside>
  );
}