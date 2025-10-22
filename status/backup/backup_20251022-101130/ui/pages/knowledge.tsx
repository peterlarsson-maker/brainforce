import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import Footer from "../components/Footer";
import Card from "../components/Card";
import axios from "axios";

interface MemoryEntry {
  id: number;
  role: string;
  message: string;
  timestamp: string;
}

export default function Knowledge() {
  const [memory, setMemory] = useState<MemoryEntry[]>([]);
  const [newMsg, setNewMsg] = useState("");
  const [newRole, setNewRole] = useState("user");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchMemory();
  }, []);

  const fetchMemory = async () => {
    setLoading(true);
    const res = await axios.get("/api/memory/all/");
    setMemory(res.data);
    setLoading(false);
  };

  const saveMemory = async () => {
    await axios.post("/api/memory/save/", {
      role: newRole,
      message: newMsg
    });
    setNewMsg("");
    fetchMemory();
  };

  return (
    <div>
      <Navbar />
      <div className="flex min-h-[70vh]">
        <Sidebar />
        <main className="flex-1 p-8">
          <Card>
            <h2 className="text-xl font-bold mb-4">Lagrade konversationer</h2>
            <div className="mb-4">
              <input
                className="border rounded px-3 py-1 mr-2"
                placeholder="Roll"
                value={newRole}
                onChange={e => setNewRole(e.target.value)}
              />
              <input
                className="border rounded px-3 py-1 mr-2 w-64"
                placeholder="Meddelande"
                value={newMsg}
                onChange={e => setNewMsg(e.target.value)}
              />
              <button className="bg-indigo-600 text-white px-3 py-1 rounded" onClick={saveMemory}>Spara</button>
            </div>
            {loading ? (
              <p>Laddar...</p>
            ) : (
              <ul className="max-h-96 overflow-auto">
                {memory.map(mem => (
                  <li key={mem.id} className="mb-2">
                    <span className="text-xs text-gray-500">{mem.timestamp} </span>
                    <span className="font-semibold">{mem.role}: </span>
                    <span>{mem.message}</span>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </main>
      </div>
      <Footer />
    </div>
  );
}
