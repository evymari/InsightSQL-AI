import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar";

export default function MainLayout() {
  return (
    <div className="flex h-screen bg-gray-100">

      {/* Sidebar fijo */}
      

      {/* Contenido dinámico */}
      <main className="flex-1 p-6 overflow-auto">
        <Outlet />
      </main>

    </div>
  );
}