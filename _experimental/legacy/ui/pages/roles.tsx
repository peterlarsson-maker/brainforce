import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import Footer from "../components/Footer";
import Card from "../components/Card";
import axios from "axios";

interface Role {
  id: string;
  name: string;
  permissions: string[];
}

export default function Roles() {
  const [roles, setRoles] = useState<Role[]>([]);

  useEffect(() => {
    fetch("/manifests/roles.json")
      .then(res => res.json())
      .then(setRoles);
  }, []);

  return (
    <div>
      <Navbar />
      <div className="flex min-h-[70vh]">
        <Sidebar />
        <main className="flex-1 p-8">
          <Card>
            <h2 className="text-xl font-bold mb-4">Roller</h2>
            <ul>
              {roles.map(role => (
                <li key={role.id} className="mb-2">
                  <span className="font-bold">{role.name}</span>
                  <span className="ml-2 text-xs text-gray-500">({role.id})</span>
                  <ul className="ml-6 text-xs text-gray-700 list-disc">
                    {role.permissions.map(p => <li key={p}>{p}</li>)}
                  </ul>
                </li>
              ))}
            </ul>
          </Card>
        </main>
      </div>
      <Footer />
    </div>
  );
}
