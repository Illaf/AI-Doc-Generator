"use client";
import { Button } from "@/components/ui/button";
import { api } from "../lib/api";
import { getToken } from "../lib/auth";
import Navbar from "@/components/Navbar";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function Dashboard() {
  const [githubLinked, setGithubLinked] = useState(false);
  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  // Detect redirect success
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("github") === "linked") {
      setGithubLinked(true);
    }
  }, []);

  const docButtonClicked = () =>{
    console.log("button clicked")
  }
  function connectGithub() {
    const token = localStorage.getItem("access_token");
    if (!token) {
      alert("You are not logged in.");
      return;
    }
    window.location.href = `http://localhost:8000/github/connect?token=${token}`;
  }

  async function fetchRepos() {
    const token = localStorage.getItem("access_token");
    if (!token) {
      alert("You are not logged in.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const resp = await fetch("http://localhost:8000/github/repos", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!resp.ok) {
        const data = await resp.json();
        throw new Error(data.detail || "Failed to load repositories");
      }

      const data = await resp.json();
      setRepos(data.repos);
    } catch (err:any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Navbar />
      <div className="max-w-5xl mx-auto mt-16 px-4">
        <h1 className="text-4xl font-bold text-center">Dashboard</h1>

        {!githubLinked && (
          <div className="text-center mt-6">
            <p className="mt-4 text-gray-500">
              Connect your GitHub to start generating documentation.
            </p>

            <Button
              className="mt-6 bg-gray-900 hover:bg-black"
              onClick={connectGithub}
            >
              Connect GitHub
            </Button>
          </div>
        )}

        {githubLinked && (
          <div className="mt-8 text-center">
            <p className="text-green-600 font-medium">
              ✅ GitHub connected successfully
            </p>

            <Button
              className="mt-4 bg-gray-900 hover:bg-black"
              onClick={fetchRepos}
            >
              {loading ? "Loading..." : "Show Repositories"}
            </Button>
          </div>
        )}

        {error && (
          <p className="text-red-500 text-center mt-4">{error}</p>
        )}

        {repos.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-10">
            {repos.map((repo:any) => (
              <div
                key={repo.id}
                className="border rounded-lg p-4 bg-white shadow-sm"
              >
                <div className="flex justify-between items-center">
                  <h3 className="font-semibold">{repo.name}</h3>
                  <span
                    className={`text-xs px-2 py-1 rounded ${
                      repo.private
                        ? "bg-red-100 text-red-600"
                        : "bg-green-100 text-green-600"
                    }`}
                  >
                    {repo.private ? "Private" : "Public"}
                  </span>
                </div>

                <p className="text-sm text-gray-500 mt-1">
                  {repo.full_name}
                </p>

                <a
                  href={repo.html_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm text-blue-600 mt-2 inline-block"
                >
                  View on GitHub →
                </a>
                <Button
  size="sm"
  className="mt-3 cursor-pointer"
  onClick={() =>
    router.push(
      `/dashboard/generate?repo=${encodeURIComponent(repo.full_name)}`
    )
  }
>
  Generate Docs →
</Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
