export async function sendPrompt(prompt: string) {
  const res = await fetch("http://localhost:11434/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: "llama3.1:8b", prompt })
  });
  const data = await res.json();
  return data.response || "Ingen respons";
}
