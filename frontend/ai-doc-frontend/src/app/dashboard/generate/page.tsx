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
  const [useCache, setUseCache] = useState(true);
  const [loading, setLoading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [progress, setProgress] = useState(0);
  const [downloadReady, setDownloadReady] = useState(false);
  const [branchList,setBranchList] = useState<string[]>([])
  const [selectedBranch, setSelectedBranch] = useState<string>("");
  const [loadingBranches, setLoadingBranches] = useState(false);
  const [wasCached, setWasCached] = useState<boolean | null>(null);
  const [template, setTemplate] = useState("minimal");

  const templateOptions = [
    { value: "minimal", label: "Minimal Clean", description: "Clean and simple design with plenty of whitespace" },
    { value: "dark", label: "Dark Mode Developer", description: "Dark theme with neon accents for developers" },
    { value: "notion", label: "Notion-Inspired", description: "Warm, friendly design inspired by Notion" },
    { value: "gradient", label: "Modern Gradient", description: "Contemporary design with vibrant gradients" },
    { value: "terminal", label: "Terminal Style", description: "Retro terminal aesthetic with green text" },
    { value: "gitbook", label: "GitBook Style", description: "Professional documentation site layout" }
  ];
  const selectedTemplateInfo = templateOptions.find(t => t.value === template);
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
        branch: selectedBranch,
        theme,
        model,
        format,
        template,
        use_cache: useCache,
      }),
    });
  
    const data = await resp.json();
    setJobId(data.job_id);
    setStatus("Started");
    setLoading(false);
  }
  useEffect(() => {
    if (!repo) return;
  
    async function fetchBranches() {
      setLoadingBranches(true);
  
      try {
        const resp = await fetch("http://localhost:8000/list-branches", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            repo_url: `https://github.com/${repo}.git`,
          }),
        });
  
        const data = await resp.json();
  
        setBranchList(data.branches || []);
        setSelectedBranch(data.default || "");
      } catch (err) {
        console.error("Failed to fetch branches", err);
      } finally {
        setLoadingBranches(false);
      }
    }
  
    fetchBranches();
  }, [repo]);
  
  useEffect(() => {
    if (!jobId) return;
  
    const interval = setInterval(async () => {
      const resp = await fetch(
        `http://localhost:8000/status/${jobId}`
      );
      const data = await resp.json();
  
      setStatus(data.status);
      setProgress(data.progress || 0);
  
      if (data.progress === 100 && data.output_file) {
        setDownloadReady(true);
        clearInterval(interval);
      }
  
      if (data.status === "Failed") {
        console.log(data.error)
        alert(data.error || "Generation failed");
        clearInterval(interval);
      }
    }, 2000);
  
    return () => clearInterval(interval);
  }, [jobId]);
  
  return (
    <>
      <Navbar />
  
      {/* Page background */}
      <div className="min-h-screen bg-gray-50 py-12 px-4">
        <div className="max-w-4xl mx-auto">
  
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900">
              Generate Documentation
            </h1>
            <p className="text-gray-600 mt-2">
              Repository:{" "}
              <span className="font-medium text-gray-900">{repo}</span>
            </p>
          </div>
  
          {/* Main Card */}
          <div className="bg-white rounded-2xl shadow-lg p-8 space-y-6">
  
            {/* Branch */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Branch
              </label>
  
              {loadingBranches ? (
                <p className="text-sm text-gray-500">Loading branches...</p>
              ) : (
                <select
                  value={selectedBranch}
                  onChange={(e) => setSelectedBranch(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2
                             focus:outline-none focus:ring-2 focus:ring-gray-900"
                >
                  {branchList.map((branch) => (
                    <option key={branch} value={branch}>
                      {branch}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Cache Control */}
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <div className="flex items-start space-x-3">
                <input
                  type="checkbox"
                  id="useCache"
                  checked={useCache}
                  onChange={(e) => setUseCache(e.target.checked)}
                  className="mt-1 h-4 w-4 text-gray-900 rounded border-gray-300
                             focus:ring-2 focus:ring-gray-900"
                />
                <div className="flex-1">
                  <label 
                    htmlFor="useCache" 
                    className="block text-sm font-medium text-gray-700 cursor-pointer"
                  >
                    Use cached documentation
                  </label>
                  <p className="text-xs text-gray-500 mt-1">
                    {useCache 
                      ? "Will use existing documentation if available for this commit. Faster generation." 
                      : "Will generate fresh documentation, ignoring cache. Takes longer but ensures latest analysis."}
                  </p>
                </div>
              </div>
            </div>
  
            {/* Theme */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Documentation Theme
              </label>
              <select
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2
                           focus:outline-none focus:ring-2 focus:ring-gray-900"
              >
                <option value="default">Default (Simple)</option>
                <option value="technical">Technical</option>
                <option value="beginner">Beginner Friendly</option>
                <option value="api">API Reference</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
              Affects the writing style and detail level
            </p>
            </div>
            <div className="border-t-2 border-gray-100 pt-6">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              UI Template
            </label>
            <select
              value={template}
              onChange={(e) => setTemplate(e.target.value)}
              className="w-full rounded-lg border-2 border-gray-200 px-4 py-2.5
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                         transition-all mb-3"
            >
              {templateOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            
            {/* Template Preview Card */}
            <div className="bg-linear-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  {template === "minimal" && <span className="text-2xl">📄</span>}
                  {template === "dark" && <span className="text-2xl">🌙</span>}
                  {template === "notion" && <span className="text-2xl">📝</span>}
                  {template === "gradient" && <span className="text-2xl">🎨</span>}
                  {template === "terminal" && <span className="text-2xl">💻</span>}
                  {template === "gitbook" && <span className="text-2xl">📚</span>}
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900">{selectedTemplateInfo?.label}</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    {selectedTemplateInfo?.description}
                  </p>
                </div>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Template only applies to HTML and PDF formats
            </p>
          </div>
            {/* Model + Format (2-column layout) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
  
              {/* Model */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Model
                </label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2
                             focus:outline-none focus:ring-2 focus:ring-gray-900"
                >
                  <option value="llama3.2">LLaMA 3.2</option>
                  <option value="llama3">LLaMA 3</option>
                  <option value="mistral">Mistral</option>
                </select>
              </div>
  
              {/* Format */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Output Format
                </label>
                <select
                  value={format}
                  onChange={(e) => setFormat(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2
                             focus:outline-none focus:ring-2 focus:ring-gray-900"
                >
                  <option value="md">Markdown</option>
                  {/* <option value="pdf">PDF</option> */}
                  <option value="html">HTML</option>
                  <option value="docx">Word</option>
                </select>
              </div>
            </div>
  
            {/* Generate Button */}
            <div className="pt-4">
              <Button
                onClick={startGeneration}
                disabled={loading}
                className="w-full bg-gray-900 hover:bg-black text-white py-3
                           rounded-xl text-lg transition"
              >
                {loading ? "Starting..." : "Start Generation"}
              </Button>
            </div>
  
            {/* Progress */}
            {jobId && (
              <div className="pt-4">
                <p className="font-medium text-gray-800">{status}</p>
  
                <div className="w-full bg-gray-200 rounded-full h-3 mt-2 overflow-hidden">
                  <div
                    className="bg-green-600 h-3 transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
  
                <p className="text-sm text-gray-500 mt-1">
                  {progress}%
                </p>
              </div>
            )}
  
            {/* Download */}
            {downloadReady && (
              <a
                href={`http://localhost:8000/download/${jobId}`}
                className="block"
              >
                <Button className="w-full bg-green-600 hover:bg-green-700
                                   text-white py-3 rounded-xl text-lg transition">
                  Download Documentation
                </Button>
              </a>
            )}
          </div>
        </div>
      </div>
    </>
  );
  
}