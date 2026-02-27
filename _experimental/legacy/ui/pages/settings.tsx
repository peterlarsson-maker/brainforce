import { useState } from "react";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import Footer from "../components/Footer";
import Card from "../components/Card";
import axios from "axios";

export default function Settings() {
  const [mock, setMock] = useState(false);

  const handleMockChange = async (val: boolean) => {
    setMock(val);
    await axios.post("/api/logs/event/", { event: "mock_mode_changed", value: val });
  };

  return (
    <div>
      <Navbar />
      <div className="flex min-h-[70vh]">
        <Sidebar />
        <main className="flex-1 p-8">
          <Card>
            <h2 className="text-xl font-bold mb-4">Inställningar</h2>
            <div className="mb-2 flex items-center gap-2">
              <input type="checkbox" checked={mock} onChange={e => handleMockChange(e.target.checked)} />
              <span>Mock-läge (testa utan API-nyckel)</span>
            </div>
            <p className="text-xs text-gray-500">Vid mock-läge skickas fejkdata istället för riktiga OpenAI-svar.</p>
          </Card>
        </main>
      </div>
      <Footer />
    </div>
  );
}
