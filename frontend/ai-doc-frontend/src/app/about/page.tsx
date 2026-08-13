export default function HowItWorks() {
    const steps = [
      {
        title: "Enter Repository Details",
        description:
          "Paste the GitHub repository URL, select the branch, and optionally choose a subdirectory to generate documentation for a specific part of the repo.",
      },
      {
        title: "Choose Model & Settings",
        description:
          `Select an AI model (llama3.2, llama3, or mistral), choose output format, UI template, theme, and enable or disable cached documentation.You need to have Ollama running locally`,
      },
      {
        title: "Repository Processing",
        description:
          "The repository is securely cloned, files are filtered, and relevant source files are grouped for efficient AI processing.",
      },
      {
        title: "AI Documentation Generation",
        description:
          "The selected AI model analyzes each file and generates clear, structured, and human-readable documentation.",
      },
      {
        title: "Apply UI Templates",
        description:
          "Your documentation is rendered using the selected template such as Minimal, Dark, Notion,Gradient,etc.",
      },
      {
        title: "Download or Reuse",
        description:
          "Download the generated documentation instantly. If caching is enabled, previously generated docs are reused for faster results.",
      },
    ];
  
    return (
      <div className="max-w-6xl mx-auto px-6 py-14">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            How It Works
          </h1>
          <p className="text-lg text-gray-600 max-w-3xl">
            Generate clean, well-structured documentation from any GitHub
            repository using local AI models — fast, private, and customizable.
          </p>
        </div>
  
        {/* Steps */}
        <div className="grid gap-6">
            <p className="text-green-500">Note:Ollama should be running locally</p>
          {steps.map((step, index) => (
            <div
              key={index}
              className="flex gap-5 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-600 text-white font-semibold">
                {index + 1}
              </div>
  
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-1">
                  {step.title}
                </h2>
                <p className="text-gray-600 leading-relaxed">
                  {step.description}
                </p>
              </div>
            </div>
          ))}
        </div>
  
        {/* Footer note */}
        <div className="mt-14 rounded-2xl bg-gradient-to-r from-blue-600 to-purple-600 p-8 text-white">
          <h3 className="text-2xl font-semibold mb-2">
            Built for Developers
          </h3>
          <p className="text-blue-100 max-w-3xl">
            Runs locally using Ollama — no cloud APIs, no data leakage. Designed
            for real-world repositories with flexible templates and caching for
            maximum efficiency.
          </p>
        </div>
      </div>
    );
  }
  