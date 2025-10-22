import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import Card from "../components/Card";
import Link from "next/link";

export default function Home() {
  return (
    <div>
      <Navbar />
      <main className="flex flex-col items-center justify-center min-h-[70vh] p-8">
        <Card className="max-w-xl text-center">
          <h1 className="text-3xl font-bold mb-4">Välkommen till BrainForce</h1>
          <p className="mb-4">
            En säker, modern AI-kontrollplattform byggd för OpenAI och lokal datahantering.
          </p>
          <div className="flex justify-center gap-4 mt-4">
            <Link href="/dashboard" className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 transition">
              Till Dashboard
            </Link>
          </div>
        </Card>
      </main>
      <Footer />
    </div>
  );
}
