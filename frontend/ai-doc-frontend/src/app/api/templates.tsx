import { useEffect, useState } from "react";
//import { fetchTemplates } from "@/api/templates";

type Template = {
  id: string;
  name: string;
  description: string;
};

export default function TemplateSelector({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
// api/templates.ts
async function fetchTemplates() {
    const res = await fetch("http://localhost:8000/templates");
    if (!res.ok) throw new Error("Failed to fetch templates");
    return res.json();
  }
  
  useEffect(() => {
    fetchTemplates()
      .then((data) => setTemplates(data.templates))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="mt-6">
      <label className="block text-sm font-medium text-gray-300 mb-2">
        Choose Documentation Template
      </label>

      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg bg-slate-900 border border-slate-700 px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
      >
        {loading && <option>Loading templates...</option>}
        {!loading &&
          templates.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name} — {t.description}
            </option>
          ))}
      </select>
    </div>
  );
}
