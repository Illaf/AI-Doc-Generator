"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";

export default function GenerateDocsPage() {
  const params = useSearchParams();
  const repo = params.get("repo");

  const [theme, setTheme] = useState("default");
  const [model, setModel] = useState("llama3.2");
  const [format, setFormat] = useState("md");
  const [loading, setLoading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [progress, setProgress] = useState(0);
  const [downloadReady, setDownloadReady] = useState(false);
  async function startGeneration() {
    if (!repo) return;
  
    setLoading(true);
  
    const resp = await fetch("http://localhost:8000/start-generation", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        repo_url: `https://github.com/${repo}.git`,
        branch: "main",
        theme,
        model,
        format,
      }),
    });
  
    const data = await resp.json();
    setJobId(data.job_id);
    setStatus("Started");
    setLoading(false);
  }
  useEffect(() => {
    if (!jobId) return;
  
    const interval = setInterval(async () => {
      const resp = await fetch(
        `http://localhost:8000/status/${jobId}`
      );
      const data = await resp.json();
  
      setStatus(data.status);
      setProgress(data.progress || 0);
  
      if (data.status === "Completed") {
        setDownloadReady(true);
        clearInterval(interval);
      }
  
      if (data.status === "Failed") {
        alert(data.error || "Generation failed");
        clearInterval(interval);
      }
    }, 2000);
  
    return () => clearInterval(interval);
  }, [jobId]);
  
  return (
    <>
      <Navbar />

      <div className="max-w-3xl mx-auto mt-12 px-4">
        <h1 className="text-3xl font-bold">Generate Documentation</h1>

        <p className="text-gray-500 mt-2">
          Repository: <span className="font-medium">{repo}</span>
        </p>

        {/* Theme */}
        <div className="mt-6">
          <label className="block text-sm font-medium mb-1">
            Documentation Theme
          </label>
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
            className="w-full border rounded p-2"
          >
            <option value="default">Default (Simple)</option>
            <option value="technical">Technical</option>
            <option value="beginner">Beginner Friendly</option>
            <option value="api">API Reference</option>
          </select>
        </div>

        {/* Model */}
        <div className="mt-4">
          <label className="block text-sm font-medium mb-1">
            Model
          </label>
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full border rounded p-2"
          >
            <option value="llama3.2">LLaMA 3.2</option>
            <option value="llama3">LLaMA 3</option>
            <option value="mistral">Mistral</option>
          </select>
        </div>

        {/* Format */}
        <div className="mt-4">
          <label className="block text-sm font-medium mb-1">
            Output Format
          </label>
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value)}
            className="w-full border rounded p-2"
          >
            <option value="md">Markdown</option>
            <option value="pdf">PDF</option>
            <option value="docx">Word</option>
          </select>
        </div>

        {/* Generate */}
        <Button
          className="mt-8 bg-gray-900 hover:bg-black"
          onClick={startGeneration}
          disabled={loading}
        >
          {loading ? "Starting..." : "Start Generation"}
        </Button>
        {jobId && (
  <div className="mt-8">
    <p className="font-medium">{status}</p>

    <div className="w-full bg-gray-200 rounded h-3 mt-2">
      <div
        className="bg-green-600 h-3 rounded transition-all"
        style={{ width: `${progress}%` }}
      />
    </div>

    <p className="text-sm text-gray-500 mt-1">
      {progress}%
    </p>
  </div>
)}
{downloadReady && (
  <a
    href={`http://localhost:8000/download/${jobId}`}
    className="inline-block mt-6"
  >
    <Button className="bg-green-600 hover:bg-green-700">
      Download Documentation
    </Button>
  </a>
)}

      </div>
      
    </>
  );
}
