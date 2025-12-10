"use client";
import { Button } from "@/components/ui/button";
import { api } from "../lib/api";
import { getToken } from "../lib/auth";
import Navbar from "@/components/Navbar";

export default function Dashboard() {
  // async function connectGithub() {
  //   const token = localStorage.getItem("access_token");
  //   console.log("token from frontend",token)
  //   const resp = await fetch("http://localhost:8000/github/connect", {
  //     method: "GET",
  //     headers: {
  //       Authorization: `Bearer ${token}`
  //     }
  //   });
  
  //   if (!resp.ok) {
  //     console.error("Backend Error:", await resp.json());
  //     alert("Not authenticated");
  //     return;
  //   }
  
  //   const data = await resp.json();
  //   console.log("data on github connect:",data)
  //   window.location.href = `http://localhost:8000/github/connect?token=${token}`; // redirect to GitHub
  // }
  function connectGithub() {
    const token = localStorage.getItem("access_token");
    if (!token) {
      alert("You are not logged in.");
      return;
    }
    window.location.href = `http://localhost:8000/github/connect?token=${token}`;
  }
   
  return (
    <>
      <Navbar />
      <div className="max-w-4xl mx-auto mt-16 text-center">
        <h1 className="text-4xl font-bold">Dashboard</h1>

        <p className="mt-4 text-gray-500">
          Connect your GitHub to start generating documentation.
        </p>

        <Button className="mt-6 bg-gray-900 hover:bg-black" onClick={connectGithub}>
          Connect GitHub
        </Button>
      </div>
    </>
  );
}
