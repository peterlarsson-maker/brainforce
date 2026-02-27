import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import Footer from "../components/Footer";
import Card from "../components/Card";

export default function Dashboard() {
  return (
    <div>
      <Navbar />
      <div className="flex min-h-[70vh]">
        <Sidebar />
        <main className="flex-1 p-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <h2 className="text-xl font-bold mb-2">Status</h2>
            <ul className="text-sm text-gray-600">
              <li>OpenAI-API: <span className="text-green-700">Online</span></li>
              <li>Mock-läge: <span className="text-yellow-700">Tillgängligt</span></li>
              <li>Minne: <span className="text-green-700">Aktivt</span></li>
              <li>Licens: <span className="text-indigo-700">Pro</span></li>
            </ul>
          </Card>
          <Card>
            <h2 className="text-xl font-bold mb-2">Snabbkommandon</h2>
            <div className="flex flex-col gap-2">
              <button className="rounded bg-indigo-600 text-white px-4 py-2 hover:bg-indigo-700 transition">Ny chatt</button>
              <button className="rounded bg-gray-200 text-gray-900 px-4 py-2 hover:bg-gray-300 transition">Ladda konversation</button>
            </div>
          </Card>
        </main>
      </div>
      <Footer />
    </div>
  );
}
