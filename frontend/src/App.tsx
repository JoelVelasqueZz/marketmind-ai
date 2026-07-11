import { Route, Routes } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import Briefing from "./pages/Briefing";
import Dashboard from "./pages/Dashboard";
import Radar from "./pages/Radar";
import Signals from "./pages/Signals";
import Watchlist from "./pages/Watchlist";

export default function App() {
  return (
    <div className="min-h-screen selection:bg-primary-container selection:text-on-primary-container">
      <Sidebar />
      <main className="ml-[280px] min-h-screen flex flex-col">
        <Topbar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/radar" element={<Radar />} />
          <Route path="/analysis" element={<Signals />} />
          <Route path="/briefings" element={<Briefing />} />
          <Route path="/watchlist" element={<Watchlist />} />
        </Routes>
      </main>
    </div>
  );
}
