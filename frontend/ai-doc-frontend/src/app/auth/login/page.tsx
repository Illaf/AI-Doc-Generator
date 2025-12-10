"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "../../lib/api";
import { saveToken } from "../../lib/auth";
import { Github } from "lucide-react";
import Link from "next/link";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const loginUser = async () => {
    try {
      const form= new FormData()
      form.append("username",email)
      form.append("password",password)
      const { data } = await api.post("/auth/login", form,{
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      console.log("data:",data)
      saveToken(data.access_token);
      window.location.href = "/dashboard";
    } catch (err) {
      console.log(err)
      alert("Invalid credentials");
    }
  };

  return (
    <div className="h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white shadow-xl rounded-xl p-8 w-[400px]">
        <h2 className="text-3xl font-bold text-center mb-6">Welcome Back</h2>

        <div className="space-y-4">
          <Input 
            placeholder="Email" 
            type="email" 
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <Input 
            placeholder="Password" 
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <Button className="w-full bg-indigo-600 hover:bg-indigo-700" onClick={loginUser}>
            Login
          </Button>
        </div>

        <p className="text-center text-sm mt-3 text-gray-500">
          New user? <Link href="/auth/register" className="text-indigo-600">Register</Link>
        </p>

        <div className="text-center my-4 text-gray-400">— or —</div>

        <Button 
          variant="outline" 
          className="w-full flex gap-2"
          onClick={() => window.location.href = "http://localhost:8000/auth/github/login"}
        >
          <Github className="w-5 h-5" />
          Login with GitHub
        </Button>
      </div>
    </div>
  );
}
