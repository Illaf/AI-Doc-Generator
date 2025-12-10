"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "../../lib/api";
import Link from "next/link";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const registerUser = async () => {
    try {
      await api.post("/auth/register", { email, password });
      alert("Account Created! You can login now.");
      window.location.href = "/auth/login";
    } catch (err) {
      alert("Error registering user");
    }
  };

  return (
    <div className="h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white shadow-xl rounded-xl p-8 w-[400px]">
        <h2 className="text-3xl font-bold text-center mb-6">Create Account</        h2>

        <div className="space-y-4">
          <Input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <Input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />

          <Button className="w-full bg-indigo-600 hover:bg-indigo-700" onClick={registerUser}>
            Register
          </Button>
        </div>

        <p className="text-center text-sm mt-3 text-gray-500">
          Already have an account? <Link href="/auth/login" className="text-indigo-600">Login</Link>
        </p>
      </div>
    </div>
  );
}
