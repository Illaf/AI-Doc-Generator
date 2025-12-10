"use client";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Navbar() {
  return (
    <nav className="border-b bg-white/70 backdrop-blur sticky top-0 z-10">
      <div className="max-w-6xl mx-auto flex justify-between items-center p-4">
        <Link href="/" className="text-xl font-bold text-indigo-600">
          AI DocGen
        </Link>

        <div className="space-x-4 hidden md:block">
          <Link href="/" className="hover:text-indigo-600">Home</Link>
          <Link href="/about" className="hover:text-indigo-600">How it works</Link>
          <Link href="/auth/login">
            <Button variant="outline">Login</Button>
          </Link>
        </div>
      </div>
    </nav>
  );
}
