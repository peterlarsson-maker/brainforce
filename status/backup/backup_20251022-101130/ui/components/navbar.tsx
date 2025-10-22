import Link from "next/link";

export default function Navbar() {
  return (
    <nav className="bg-white shadow-kirki px-6 py-2 flex items-center justify-between rounded-b-card mb-4">
      <div className="flex items-center gap-2">
        <img src="/logo.svg" alt="BrainForce" className="w-8 h-8" />
        <span className="font-bold text-xl text-indigo-700">BrainForce</span>
      </div>
      <div>
        <Link href="/dashboard" className="mx-2 text-base font-medium hover:text-indigo-700">Dashboard</Link>
        <Link href="/knowledge" className="mx-2 text-base font-medium hover:text-indigo-700">Knowledge</Link>
        <Link href="/roles" className="mx-2 text-base font-medium hover:text-indigo-700">Roles</Link>
        <Link href="/settings" className="mx-2 text-base font-medium hover:text-indigo-700">Settings</Link>
        <Link href="/licenses" className="mx-2 text-base font-medium hover:text-indigo-700">Licenses</Link>
      </div>
    </nav>
  );
}
