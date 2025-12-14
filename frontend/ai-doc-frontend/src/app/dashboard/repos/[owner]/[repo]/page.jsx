"use client";

import { useParams } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";

export default function GenerateDocsPage() {
  const { owner, repo } = useParams();

  const [theme, setTheme] = useState("beginner");
  const [model, setModel] = useState("llama3.2");
  const [format, setFormat] = useState("md");

  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState("");
  const [progress, setProgress] = useState(0);
  const [loading, setLoading] = useState(false);

  async function startGeneration() {
    const token = localStorage.getItem("access_token");
    if (!token) {
      alert("You are not logged in");
      return;
    }

    setLoading(true);
    setStatus("Starting job...");

    const resp = await fetch("http://localhost:8000/start-generation", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        repo_url: `https://github.com/${owner}/${repo}.git`,
        theme,
        model,
        format,
      }),
    });

    const data = await resp.json();
    setJobId(data.job_id);
    setLoading(false);
  }

  async function checkStatus() {
    if (!jobId) return;

    const resp = await fetch(
      `http://localhost:8000/status/${jobId}`
    );
    const data = await resp.json();

    setStatus(data.status);
    setProgress(data.progress);
  }

  return (
    <>
      <Navbar />

      <div className="max-w-3xl mx-auto mt-12 px-4">
        <h1 className="text-3xl font-bold">
          Generate Documentation
        </h1>

        <p className="text-gray-500 mt-1">
          Repository: <b>{owner}/{repo}</b>
        </p>

        {/* THEME */}
        <div className="mt-6">
          <label className="font-medium">Documentation Theme</label>
          <select
            className="w-full border p-2 rounded mt-1"
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
          >
            <option value="beginner">Beginner Friendly</option>
            <option value="technical">Technical</option>
            <option value="business">Business Overview</option>
          </select>
        </div>

        {/* MODEL */}
        <div className="mt-4">
          <label className="font-medium">Model</label>
          <select
            className="w-full border p-2 rounded mt-1"
            value={model}
            onChange={(e) => setModel(e.target.value)}
          >
            <option value="llama3.2">LLaMA 3.2</option>
            <option value="mistral">Mistral</option>
          </select>
        </div>

        {/* FORMAT */}
        <div className="mt-4">
          <label className="font-medium">Output Format</label>
          <select
            className="w-full border p-2 rounded mt-1"
            value={format}
            onChange={(e) => setFormat(e.target.value)}
          >
            <option value="md">Markdown</option>
            <option value="pdf">PDF</option>
          </select>
        </div>

        <Button
          className="mt-6 w-full"
          onClick={startGeneration}
          disabled={loading}
        >
          {loading ? "Starting..." : "Generate Documentation"}
        </Button>

        {/* JOB STATUS */}
        {jobId && (
          <div className="mt-6 border rounded p-4">
            <p className="font-medium">Job Status</p>
            <p className="text-sm mt-1">{status}</p>

            <div className="w-full bg-gray-200 rounded h-2 mt-2">
              <div
                className="bg-black h-2 rounded"
                style={{ width: `${progress}%` }}
              />
            </div>

            <Button
              size="sm"
              className="mt-3"
              onClick={checkStatus}
            >
              Refresh Status
            </Button>

            {progress === 100 && (
              <a
                href={`http://localhost:8000/download/${jobId}`}
                className="block text-center mt-3 text-blue-600"
              >
                Download Documentation →
              </a>
            )}
          </div>
        )}
      </div>
    </>
  );
}
