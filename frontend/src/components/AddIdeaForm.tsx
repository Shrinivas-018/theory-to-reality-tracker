import { useState } from "react";
import { motion } from "framer-motion";
import { PlusCircle, Loader2, CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

const STAGES = [
  { value: "philosophy", label: "Philosophy", color: "bg-purple-500" },
  { value: "scientific_validation", label: "Scientific Validation", color: "bg-blue-500" },
  { value: "engineering_application", label: "Engineering Application", color: "bg-orange-500" },
  { value: "modern_technology", label: "Modern Technology", color: "bg-green-500" },
];

const CATEGORIES = [
  "Physics", "Chemistry", "Biology", "Mathematics", "Computer science",
  "Medicine", "Economics", "Psychology", "Neuroscience", "Astronomy",
  "Engineering", "Genetics", "Artificial intelligence", "General Science"
];

interface FormState {
  title: string;
  description: string;
  stage: string;
  category: string;
  start_year: string;
  end_year: string;
  laureates: string;
  keywords: string;
}

const EMPTY: FormState = {
  title: "", description: "", stage: "philosophy",
  category: "Physics", start_year: "", end_year: "",
  laureates: "", keywords: "",
};

export default function AddIdeaForm({ onAdded }: { onAdded?: () => void }) {
  const [form, setForm] = useState<FormState>(EMPTY);
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  const set = (k: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("loading");
    setErrorMsg("");

    // Build a safe ID from title
    const id = form.title.toLowerCase().replace(/[^a-z0-9]+/g, "_").slice(0, 60)
      + "_" + form.start_year;

    const payload = {
      id,
      title: form.title,
      description: form.description || `Concept of ${form.title}`,
      stage: form.stage,
      category: form.category,
      start_year: parseInt(form.start_year),
      end_year: form.end_year ? parseInt(form.end_year) : null,
      laureates: form.laureates ? form.laureates.split(",").map(s => s.trim()).filter(Boolean) : ["Unknown"],
      motivation: form.description || `Scholarly concept: ${form.title}`,
      keywords: form.keywords ? form.keywords.split(",").map(s => s.trim().toLowerCase()).filter(Boolean) : [form.title.toLowerCase()],
      influence_score: 0.5,
    };

    try {
      const res = await fetch("http://localhost:5000/api/ideas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        setErrorMsg(data.message || "Failed to add idea");
        setStatus("error");
        return;
      }
      setStatus("success");
      setForm(EMPTY);
      onAdded?.();
      setTimeout(() => setStatus("idle"), 3000);
    } catch (err) {
      setErrorMsg("Could not connect to backend");
      setStatus("error");
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
      <Card className="bg-white/80 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PlusCircle className="h-5 w-5 text-purple-500" />
            Add Your Own Idea
          </CardTitle>
          <CardDescription>
            Submit a new idea to the evolution tracker. It will appear in search results immediately.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-5">

            {/* Title */}
            <div className="space-y-1">
              <label className="text-sm font-medium">Title *</label>
              <Input placeholder="e.g. Quantum Entanglement" value={form.title} onChange={set("title")} required />
            </div>

            {/* Description */}
            <div className="space-y-1">
              <label className="text-sm font-medium">Description</label>
              <textarea
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                rows={3}
                placeholder="Describe the idea, its significance and impact..."
                value={form.description}
                onChange={set("description")}
              />
            </div>

            {/* Stage */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Evolution Stage *</label>
              <div className="flex flex-wrap gap-2">
                {STAGES.map(s => (
                  <button
                    key={s.value}
                    type="button"
                    onClick={() => setForm(f => ({ ...f, stage: s.value }))}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium border-2 transition-all ${
                      form.stage === s.value
                        ? `${s.color} text-white border-transparent`
                        : "bg-white text-gray-600 border-gray-200 hover:border-gray-400"
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Category + Years */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-1">
                <label className="text-sm font-medium">Category *</label>
                <select
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  value={form.category}
                  onChange={set("category")}
                >
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium">Start Year *</label>
                <Input type="number" placeholder="e.g. 1925" min={1800} max={2200} value={form.start_year} onChange={set("start_year")} required />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium">End Year</label>
                <Input type="number" placeholder="e.g. 1950" min={1800} max={2200} value={form.end_year} onChange={set("end_year")} />
              </div>
            </div>

            {/* Authors + Keywords */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-sm font-medium">Key Contributors</label>
                <Input placeholder="e.g. Einstein, Bohr (comma separated)" value={form.laureates} onChange={set("laureates")} />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium">Keywords</label>
                <Input placeholder="e.g. quantum, physics (comma separated)" value={form.keywords} onChange={set("keywords")} />
              </div>
            </div>

            {/* Error */}
            {status === "error" && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {errorMsg}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={status === "loading" || status === "success"}
              className={`w-full py-2.5 rounded-lg font-medium text-sm flex items-center justify-center gap-2 transition-all ${
                status === "success"
                  ? "bg-green-500 text-white"
                  : "bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:opacity-90"
              }`}
            >
              {status === "loading" && <Loader2 className="h-4 w-4 animate-spin" />}
              {status === "success" && <CheckCircle2 className="h-4 w-4" />}
              {status === "success" ? "Idea Added Successfully!" : status === "loading" ? "Adding..." : "Add Idea to Tracker"}
            </button>
          </form>
        </CardContent>
      </Card>
    </motion.div>
  );
}
