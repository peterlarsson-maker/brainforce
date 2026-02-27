import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip";
import { Loader2, RefreshCw, Send, Cpu, HardDrive, Terminal, Bot, Settings, PlugZap, Boxes, GitBranch, Sparkles, Monitor, ShieldCheck, GripVertical } from "lucide-react";

// Minimal types for Ollama API
interface OllamaModelTag { name: string; model?: string; modified?: string; size?: number; digest?: string }
interface OllamaPsItem { name: string; size?: number; digest?: string; started_at?: string }

// Helper: format bytes
const fmtBytes = (n?: number) => {
  if (!n && n !== 0) return "-";
  const units = ["B","KB","MB","GB","TB"]; let i=0; let x=n;
  while (x >= 1024 && i < units.length-1) { x/=1024; i++; }
  return `${x.toFixed(x<10?2:1)} ${units[i]}`;
};

// Draggable resizable sidebar
function useResizable(initialWidth = 280) {
  const [width, setWidth] = useState(initialWidth);
  const draggingRef = useRef(false);
  const onMouseDown = useCallback(() => { draggingRef.current = true; }, []);
  const onMouseMove = useCallback((e: MouseEvent) => {
    if (!draggingRef.current) return;
    const w = Math.min(Math.max(e.clientX, 200), 520); // clamp 200-520px
    setWidth(w);
  }, []);
  const onMouseUp = useCallback(() => { draggingRef.current = false; }, []);
  useEffect(() => {
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => { window.removeEventListener("mousemove", onMouseMove); window.removeEventListener("mouseup", onMouseUp); };
  }, [onMouseMove, onMouseUp]);
  return { width, onMouseDown };
}

export default function CommandPanel() {
  const { width, onMouseDown } = useResizable();
  const [activeTab, setActiveTab] = useState<string>("panel");
  const [baseUrl, setBaseUrl] = useState<string>("http://localhost:11434");
  const [loadingTags, setLoadingTags] = useState(false);
  const [loadingPs, setLoadingPs] = useState(false);
  const [models, setModels] = useState<OllamaModelTag[]>([]);
  const [procs, setProcs] = useState<OllamaPsItem[]>([]);
  const [prompt, setPrompt] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [reply, setReply] = useState<string>("");
  const [running, setRunning] = useState(false);
  const [apiOk, setApiOk] = useState<boolean | null>(null);

  const tabs = useMemo(() => ([
    { key: "panel", icon: <Bot className="w-4 h-4"/>, label: "Panel" },
    { key: "hub", icon: <PlugZap className="w-4 h-4"/>, label: "Hub" },
    { key: "avatars", icon: <Boxes className="w-4 h-4"/>, label: "Avatars" },
    { key: "dev", icon: <GitBranch className="w-4 h-4"/>, label: "GitHub/VS" },
    { key: "vr", icon: <Monitor className="w-4 h-4"/>, label: "VR" },
    { key: "licenses", icon: <ShieldCheck className="w-4 h-4"/>, label: "Licenser" },
    { key: "settings", icon: <Settings className="w-4 h-4"/>, label: "Inställningar" },
  ]), []);

  const checkApi = useCallback(async () => {
    try {
      const res = await fetch(`${baseUrl}/api/tags`, { method: "GET" });
      setApiOk(res.ok);
    } catch {
      setApiOk(false);
    }
  }, [baseUrl]);

  const loadTags = useCallback(async () => {
    setLoadingTags(true);
    try {
      const res = await fetch(`${baseUrl}/api/tags`);
      if (!res.ok) throw new Error("tags failed");
      const data = await res.json();
      const list: OllamaModelTag[] = data?.models ?? data?.data ?? [];
      setModels(list);
      if (!selectedModel && list.length) setSelectedModel(list[0].name);
    } catch (e) {
      console.error(e);
    } finally { setLoadingTags(false); }
  }, [baseUrl, selectedModel]);

  const loadPs = useCallback(async () => {
    setLoadingPs(true);
    try {
      const res = await fetch(`${baseUrl}/api/ps`);
      if (!res.ok) throw new Error("ps failed");
      const data = await res.json();
      const list: OllamaPsItem[] = data?.models ?? data?.data ?? [];
      setProcs(list);
    } catch (e) { console.error(e); }
    finally { setLoadingPs(false); }
  }, [baseUrl]);

  useEffect(() => { checkApi(); }, [checkApi]);
  useEffect(() => { loadTags(); loadPs(); }, [loadTags, loadPs]);

  const handleGenerate = useCallback(async () => {
    if (!selectedModel || !prompt.trim()) return;
    setRunning(true); setReply("");
    try {
      const res = await fetch(`${baseUrl}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: selectedModel, prompt }),
      });
      if (!res.ok || !res.body) {
        const t = await res.text();
        throw new Error(t || "No response body");
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let full = "";
      while (true) {
        const {value, done} = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        // Ollama streams NDJSON
        for (const line of chunk.split("\n")) {
          if (!line.trim()) continue;
          try {
            const j = JSON.parse(line);
            if (typeof j.response === "string") { full += j.response; setReply(prev => prev + j.response); }
          } catch { /* ignore partial */ }
        }
      }
      setReply(full);
    } catch (e: any) {
      setReply(`⚠️ Fel vid generering: ${e?.message ?? e}`);
    } finally { setRunning(false); }
  }, [baseUrl, selectedModel, prompt]);

  const StatusPill = ({ ok }: { ok: boolean | null }) => (
    <div className={`px-2 py-1 text-xs rounded-full border ${ok===null?"border-muted-foreground/30 text-muted-foreground":""} ${ok?"bg-emerald-500/10 text-emerald-600 border-emerald-500/30":"bg-rose-500/10 text-rose-600 border-rose-500/30"}`}>
      API {ok===null?"?": ok?"OK":"NED"}
    </div>
  );

  return (
    <TooltipProvider>
      <div className="w-screen h-screen min-h-screen bg-background text-foreground overflow-hidden">
        <div className="flex h-full">
          {/* Sidebar */}
          <aside style={{ width }} className="relative border-r bg-card/50 backdrop-blur-sm">
            <div className="flex items-center gap-2 p-3 border-b">
              <Sparkles className="w-5 h-5"/>
              <span className="font-semibold">Kommandopanel</span>
              <div className="ml-auto"><StatusPill ok={apiOk} /></div>
            </div>
            <div className="p-3 space-y-2">
              <label className="text-xs text-muted-foreground">Ollama‑bas-URL</label>
              <Input value={baseUrl} onChange={e=>setBaseUrl(e.target.value)} placeholder="http://localhost:11434" />
              <div className="flex gap-2">
                <Button variant="secondary" onClick={()=>{checkApi(); loadTags(); loadPs();}}>
                  <RefreshCw className="mr-2 h-4 w-4"/>Uppdatera
                </Button>
              </div>
            </div>
            <nav className="px-2 pt-2 space-y-1 select-none">
              {tabs.map(t => (
                <button key={t.key} onClick={()=>setActiveTab(t.key)}
                  className={`w-full flex items-center gap-2 px-3 py-2 rounded-xl text-left hover:bg-accent transition ${activeTab===t.key?"bg-accent" : ""}`}>
                  {t.icon}
                  <span>{t.label}</span>
                </button>
              ))}
            </nav>
            {/* Drag handle */}
            <div onMouseDown={onMouseDown} className="absolute top-0 right-0 h-full w-2 cursor-col-resize flex items-center justify-center text-muted-foreground/40">
              <GripVertical className="w-3 h-3"/>
            </div>
          </aside>

          {/* Main content */}
          <main className="flex-1 min-w-0 p-4 md:p-6 overflow-auto">
            {activeTab === "panel" && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
                <Card className="shadow-sm">
                  <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle className="flex items-center gap-2"><Cpu className="w-5 h-5"/> Modeller</CardTitle>
                    <Button size="sm" variant="outline" onClick={loadTags} disabled={loadingTags}>
                      {loadingTags? <Loader2 className="w-4 h-4 animate-spin"/> : <RefreshCw className="w-4 h-4"/>}
                    </Button>
                  </CardHeader>
                  <CardContent>
                    <div className="border rounded-xl overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-muted/40">
                          <tr className="text-left">
                            <th className="px-3 py-2">Namn</th>
                            <th className="px-3 py-2">Storlek</th>
                            <th className="px-3 py-2">Ändrad</th>
                          </tr>
                        </thead>
                        <tbody>
                          {models.map((m) => (
                            <tr key={m.name} className="border-t hover:bg-accent/30">
                              <td className="px-3 py-2 font-medium">{m.name}</td>
                              <td className="px-3 py-2">{fmtBytes(m.size)}</td>
                              <td className="px-3 py-2">{m.modified ? new Date(m.modified).toLocaleString() : "–"}</td>
                            </tr>
                          ))}
                          {!models.length && (
                            <tr><td className="px-3 py-6 text-muted-foreground" colSpan={3}>Inga modeller hittades – kontrollera API:et och tryck Uppdatera.</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>

                <Card className="shadow-sm">
                  <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle className="flex items-center gap-2"><HardDrive className="w-5 h-5"/> Processer</CardTitle>
                    <Button size="sm" variant="outline" onClick={loadPs} disabled={loadingPs}>
                      {loadingPs? <Loader2 className="w-4 h-4 animate-spin"/> : <RefreshCw className="w-4 h-4"/>}
                    </Button>
                  </CardHeader>
                  <CardContent>
                    <div className="border rounded-xl overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-muted/40">
                          <tr className="text-left">
                            <th className="px-3 py-2">Namn</th>
                            <th className="px-3 py-2">Storlek</th>
                            <th className="px-3 py-2">Startad</th>
                          </tr>
                        </thead>
                        <tbody>
                          {procs.map((p, i) => (
                            <tr key={`${p.name}-${i}`} className="border-t hover:bg-accent/30">
                              <td className="px-3 py-2">{p.name}</td>
                              <td className="px-3 py-2">{fmtBytes(p.size)}</td>
                              <td className="px-3 py-2">{p.started_at ? new Date(p.started_at).toLocaleString() : "–"}</td>
                            </tr>
                          ))}
                          {!procs.length && (
                            <tr><td className="px-3 py-6 text-muted-foreground" colSpan={3}>Inga aktiva processer.</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>

                <Card className="lg:col-span-2 shadow-sm">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2"><Terminal className="w-5 h-5"/> Snabbkörning</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <div className="md:col-span-2">
                        <Textarea value={prompt} onChange={e=>setPrompt(e.target.value)} placeholder="Skriv en prompt…" className="min-h-[96px]"/>
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs text-muted-foreground">Modell</label>
                        <Select value={selectedModel} onValueChange={setSelectedModel}>
                          <SelectTrigger className="w-full">
                            <SelectValue placeholder="Välj modell" />
                          </SelectTrigger>
                          <SelectContent>
                            {models.map(m => (
                              <SelectItem key={m.name} value={m.name}>{m.name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <Button className="w-full" onClick={handleGenerate} disabled={running || !prompt.trim() || !selectedModel}>
                          {running ? <Loader2 className="mr-2 h-4 w-4 animate-spin"/> : <Send className="mr-2 h-4 w-4"/>}
                          Kör
                        </Button>
                      </div>
                    </div>
                    <div className="border rounded-xl p-3 bg-muted/30 min-h-[140px] whitespace-pre-wrap text-sm">
                      {reply || <span className="text-muted-foreground">Svar visas här…</span>}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab !== "panel" && (
              <div className="h-full grid place-items-center text-center text-muted-foreground">
                <div>
                  <div className="flex items-center justify-center gap-2 mb-2">
                    {tabs.find(t=>t.key===activeTab)?.icon}
                    <h2 className="text-xl font-semibold">{tabs.find(t=>t.key===activeTab)?.label}</h2>
                  </div>
                  <p>Denna modul är platsad här och kan aktiveras via licens. Basen är klar i vänstermenyn.</p>
                </div>
              </div>
            )}
          </main>
        </div>
      </div>
    </TooltipProvider>
  );
}
																																																																																																																																																																																																																																																																																																																																																																		