import Link from "next/link";
import Link from "next/link";
import { useRouter } from "next/router";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/knowledge", label: "Knowledge" },
  { href: "/roles", label: "Roles" },
  { href: "/settings", label: "Settings" },
  { href: "/licenses", label: "Licenses" },
];

export default function Sidebar() {
  const router = useRouter();
  return (
    <aside className="w-56 bg-white shadow-kirki h-full rounded-r-card py-6 px-2 flex flex-col gap-2">
      {links.map(link => (
        <Link
          key={link.href}
          href={link.href}
          className={`block px-4 py-2 rounded-lg font-medium transition ${router.pathname === link.href ? 'bg-indigo-50 text-indigo-700' : 'hover:bg-indigo-50'}`}
        >
          {link.label}
        </Link>
      ))}
    </aside>
  );
}
