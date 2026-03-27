import { BrowserRouter, Routes, Route } from "react-router-dom";

import MainLayout from "../layout/MainLayout";
import Dashboard from "../pages/Dashboard";
import History from "../pages/History";



export default function AppRouter() {
  return (
   <BrowserRouter>
<Routes>

        <Route path="/" element={<MainLayout />}>

          <Route index element={<Dashboard />} />
          <Route path="history" element={<History />} />

        </Route>

      </Routes>
    </BrowserRouter>
  );
}