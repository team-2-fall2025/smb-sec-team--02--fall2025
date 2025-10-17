import { Sidebar } from "./Sidebar";
import { Navbar } from "./Navbar";
import { ReactNode } from "react";


interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="d-flex flex-column" style={{ minHeight: "100vh" }}>
      {/* Top Navbar */}
      <Navbar />

      {/* Content Area: Sidebar + Main */}
      <div className="d-flex flex-grow-1">
        <Sidebar />
        <main className="flex-grow-1 p-4 bg-white">{children}</main>
      </div>
    </div>
  );
}
