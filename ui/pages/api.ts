import axios from "axios";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function openaiProxy(prompt: string, model = "gpt-3.5-turbo") {
  const res = await axios.post(`${API_URL}/openai/`, {
    prompt, model
  });
  return res.data.response;
}

export async function saveMemory(role: string, message: string) {
  await axios.post(`${API_URL}/memory/save/`, { role, message });
}

export async function getAllMemory() {
  const res = await axios.get(`${API_URL}/memory/all/`);
  return res.data;
}
