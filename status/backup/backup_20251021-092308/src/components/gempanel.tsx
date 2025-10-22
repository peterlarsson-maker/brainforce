import { useState } from "react";
import { sendPrompt } from "../lib/ollama";

export default function GemPanel() {
  const [input, setInput] = useState("");
  const [log, setLog] = useState<string[]>([]);

  async function handleSend() {
    const reply = await sendPrompt(input);
    setLog(prev => [...prev, "🧍: " + input, "🤖: " + reply]);
    setInput("");
  }

  return (
    <div className="flex h-screen bg-slate-900 text-silver">
      <div className="w-64 p-4 border-r border-slate-700">
        <h2 className="text-xl font-bold mb-4">Gem Panel</h2>
        <button className="w-full bg-blue-600 rounded p-2 mb-2">Chat</button>
        <button className="w-full bg-slate-700 rounded p-2">Filer</button>
      </div>
      <div className="flex-1 p-4">
        <div className="overflow-y-auto h-[90%] bg-slate-800 rounded p-2 mb-2">
          {log.map((l, i) => <div key={i}>{l}</div>)}
        </div>
        <div className="flex">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            className="flex-1 bg-slate-700 p-2 rounded-l outline-none"
            placeholder="Skriv till Gem…"
          />
          <button onClick={handleSend} className="bg-blue-600 px-4 rounded-r">
            Skicka
          </button>
        </div>
      </div>
    </div>
  );
}
