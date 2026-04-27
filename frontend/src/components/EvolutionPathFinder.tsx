import { useState, useMemo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { GitBranch, Search, Loader2, ArrowDown, Lightbulb, TrendingUp, Zap, Cpu, Route, X } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

const stageIcons: Record<string, typeof Lightbulb> = {
  philosophy: Lightbulb,
  scientific_validation: TrendingUp,
  engineering_application: Zap,
  modern_technology: Cpu,
};

const stageColors: Record<string, string> = {
  philosophy: "bg-purple-500",
  scientific_validation: "bg-blue-500",
  engineering_application: "bg-orange-500",
  modern_technology: "bg-green-500",
};

const stageBg: Record<string, string> = {
  philosophy: "bg-purple-50 border-purple-200",
  scientific_validation: "bg-blue-50 border-blue-200",
  engineering_application: "bg-orange-50 border-orange-200",
  modern_technology: "bg-green-50 border-green-200",
};

const stageText: Record<string, string> = {
  philosophy: "text-purple-700",
  scientific_validation: "text-blue-700",
  engineering_application: "text-orange-700",
  modern_technology: "text-green-700",
};

interface Idea {
  id: string;
  title: string;
  stage: string;
  start_year: number;
  end_year?: number;
  category: string;
  description: string;
  keywords: string[];
  laureates: string[];
  influence_score: number;
}

interface Props {
  ideas: Idea[];
}

export default function EvolutionPathFinder({ ideas }: Props) {
  const [fromQuery, setFromQuery] = useState("");
  const [toQuery, setToQuery] = useState("");
  const [fromSelected, setFromSelected] = useState<Idea | null>(null);
  const [toSelected, setToSelected] = useState<Idea | null>(null);
  const [showFrom, setShowFrom] = useState(false);
  const [showTo, setShowTo] = useState(false);
  const [path, setPath] = useState<Idea[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "not_found" | "found">("idle");

  const filter = useCallback((q: string) => {
    if (!q.trim()) return [];
    const lq = q.toLowerCase();
    return ideas.filter(i =>
      i.title.toLowerCase().includes(lq) ||
      (i.description || "").toLowerCase().includes(lq) ||
      (i.keywords || []).some(k => k.toLowerCase().includes(lq))
    ).slice(0, 8);
  }, [ideas]);

  const fromResults = useMemo(() => filter(fromQuery), [fromQuery, filter]);
  const toResults = useMemo(() => filter(toQuery), [toQuery, filter]);

  const findPath = async () => {
    if (!fromSelected || !toSelected) return;
    setStatus("loading");
    setPath([]);
    try {
      const res = await fetch(`http://localhost:5000/api/graph/path?from=${fromSelected.id}&to=${toSelected.id}`);
      const data = await res.json();
      const pathIds: string[] = data?.data?.path || [];
      if (!pathIds.length) { setStatus("not_found"); return; }
      const details = await Promise.all(
        pathIds.map(id =>
          fetch(`http://localhost:5000/api/ideas/${id}`).then(r => r.json()).then(d => d?.data).catch(() => null)
        )
      );
      setPath(details.filter(Boolean));
      setStatus("found");
    } catch {
      setStatus("not_found");
    }
  };

  const canFind = fromSelected && toSelected && fromSelected.id !== toSelected.id;

  const DropdownItem = ({ idea, onSelect }: { idea: Idea; onSelect: (i: Idea) => void }) => (
    <button
      onMouseDown={() => onSelect(idea)}
      className="w-full text-left px-3 py-2.5 hover:bg-slate-50 flex items-center gap-3 border-b last:border-0 transition-colors"
    >
      <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${stageColors[idea.stage] || "bg-gray-400"}`} />
      <div className="flex-1 min-w-0">
        <div className="font-medium text-sm truncate">{idea.title}</div>
        <div className="text-xs text-muted-foreground">{idea.category} · {idea.start_year}</div>
      </div>
      <Badge variant="outline" className={`text-[10px] shrink-0 ${stageText[idea.stage] || ""}`}>
        {(idea.stage || "").replace(/_/g, " ")}
      </Badge>
    </button>
  );

  const SelectedBadge = ({ idea, onClear }: { idea: Idea; onClear: () => void }) => (
    <div className={`rounded-lg px-3 py-2.5 border flex items-center justify-between ${stageBg[idea.stage] || "bg-gray-50 border-gray-200"}`}>
      <div>
        <div className={`font-semibold text-sm ${stageText[idea.stage] || "text-gray-700"}`}>{idea.title}</div>
        <div className="text-xs text-muted-foreground">{idea.start_year} · {idea.category}</div>
      </div>
      <button onClick={onClear} className="p-1 rounded-full hover:bg-black/10 transition-colors ml-2">
        <X className="h-3.5 w-3.5 text-muted-foreground" />
      </button>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-500 to-blue-500 shadow-lg mb-2">
          <Route className="h-7 w-7 text-white" />
        </div>
        <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
          Evolution Path Finder
        </h2>
        <p className="text-muted-foreground max-w-lg mx-auto text-sm">
          Select two ideas and discover the shortest evolutionary path connecting them through the knowledge graph.
        </p>
      </div>

      {/* Selector Card */}
      <Card className="bg-white/90 backdrop-blur-sm shadow-md">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <GitBranch className="h-4 w-4 text-purple-500" />
            Select Ideas
          </CardTitle>
          <CardDescription>Search and select a starting idea and a destination idea</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

            {/* FROM */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-purple-700 flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-purple-500" /> Origin Idea
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Search starting idea..."
                  value={fromQuery}
                  onChange={e => { setFromQuery(e.target.value); setFromSelected(null); setShowFrom(true); }}
                  onFocus={() => setShowFrom(true)}
                  onBlur={() => setTimeout(() => setShowFrom(false), 150)}
                />
                {showFrom && fromResults.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-1 bg-white border rounded-xl shadow-xl z-20 overflow-hidden">
                    {fromResults.map(r => <DropdownItem key={r.id} idea={r} onSelect={i => { setFromSelected(i); setFromQuery(i.title); setShowFrom(false); }} />)}
                  </div>
                )}
              </div>
              {fromSelected && <SelectedBadge idea={fromSelected} onClear={() => { setFromSelected(null); setFromQuery(""); }} />}
            </div>

            {/* TO */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-green-700 flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-green-500" /> Destination Idea
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Search destination idea..."
                  value={toQuery}
                  onChange={e => { setToQuery(e.target.value); setToSelected(null); setShowTo(true); }}
                  onFocus={() => setShowTo(true)}
                  onBlur={() => setTimeout(() => setShowTo(false), 150)}
                />
                {showTo && toResults.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-1 bg-white border rounded-xl shadow-xl z-20 overflow-hidden">
                    {toResults.map(r => <DropdownItem key={r.id} idea={r} onSelect={i => { setToSelected(i); setToQuery(i.title); setShowTo(false); }} />)}
                  </div>
                )}
              </div>
              {toSelected && <SelectedBadge idea={toSelected} onClear={() => { setToSelected(null); setToQuery(""); }} />}
            </div>
          </div>

          {fromSelected && toSelected && fromSelected.id === toSelected.id && (
            <p className="text-center text-sm text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2">
              Please select two different ideas.
            </p>
          )}

          <button
            onClick={findPath}
            disabled={!canFind || status === "loading"}
            className="w-full py-3 rounded-xl font-semibold text-sm bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:opacity-90 disabled:opacity-40 flex items-center justify-center gap-2 transition-all shadow-md hover:shadow-lg"
          >
            {status === "loading"
              ? <><Loader2 className="h-4 w-4 animate-spin" /> Finding path...</>
              : <><Route className="h-4 w-4" /> Find Evolution Path</>}
          </button>
        </CardContent>
      </Card>

      {/* Results */}
      <AnimatePresence mode="wait">
        {status === "not_found" && (
          <motion.div key="nf" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <Card className="bg-amber-50 border-amber-200">
              <CardContent className="py-8 text-center space-y-2">
                <div className="text-3xl">🔍</div>
                <p className="font-semibold text-amber-800">No path found</p>
                <p className="text-sm text-amber-700">These two ideas are not connected in the lineage graph. Try a different pair.</p>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {status === "found" && path.length > 0 && (
          <motion.div key="found" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-4">
            {/* Summary bar */}
            <div className="flex items-center justify-between px-1">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                  <Route className="h-4 w-4 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-sm">Path found</p>
                  <p className="text-xs text-muted-foreground">{path.length} step{path.length !== 1 ? "s" : ""} in the evolution chain</p>
                </div>
              </div>
              <Badge variant="outline" className="text-sm px-3 py-1">
                {(path[path.length - 1]?.start_year || 0) - (path[0]?.start_year || 0)} years
              </Badge>
            </div>

            {/* Path nodes */}
            <div className="relative">
              {/* Vertical connector line */}
              <div className="absolute left-[27px] top-10 bottom-10 w-0.5 bg-gradient-to-b from-purple-300 via-blue-300 to-green-300 z-0" />

              <div className="space-y-2 relative z-10">
                {path.map((idea, i) => {
                  const Icon = stageIcons[idea.stage] || Lightbulb;
                  const isFirst = i === 0;
                  const isLast = i === path.length - 1;
                  return (
                    <div key={idea.id}>
                      <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.08 }}
                        className={`flex items-start gap-4 p-4 rounded-xl border bg-white shadow-sm hover:shadow-md transition-shadow ${isFirst ? "ring-2 ring-purple-200" : ""} ${isLast ? "ring-2 ring-green-200" : ""}`}
                      >
                        {/* Step icon */}
                        <div className={`w-9 h-9 rounded-full ${stageColors[idea.stage] || "bg-gray-400"} flex items-center justify-center shrink-0 shadow-sm`}>
                          <Icon className="h-4 w-4 text-white" />
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap mb-1">
                            <span className="font-semibold text-sm">{idea.title}</span>
                            {isFirst && <Badge className="text-[10px] bg-purple-100 text-purple-700 border-purple-200">Origin</Badge>}
                            {isLast && <Badge className="text-[10px] bg-green-100 text-green-700 border-green-200">Destination</Badge>}
                            <Badge variant="outline" className={`text-[10px] ${stageText[idea.stage] || ""}`}>
                              {(idea.stage || "").replace(/_/g, " ")}
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground line-clamp-2 mb-2">{idea.description}</p>
                          <div className="flex items-center gap-3 text-xs text-muted-foreground">
                            <span>{idea.start_year}{idea.end_year ? ` – ${idea.end_year}` : ""}</span>
                            <span>·</span>
                            <span>{idea.category}</span>
                            {idea.laureates?.length > 0 && (
                              <>
                                <span>·</span>
                                <span className="truncate max-w-[200px]">{idea.laureates.slice(0, 2).join(", ")}</span>
                              </>
                            )}
                          </div>
                        </div>

                        {/* Step number */}
                        <div className="text-xs font-bold text-muted-foreground shrink-0 w-6 text-right">
                          {i + 1}
                        </div>
                      </motion.div>

                      {/* Arrow between steps */}
                      {i < path.length - 1 && (
                        <div className="flex justify-start pl-[27px] my-1">
                          <ArrowDown className="h-4 w-4 text-muted-foreground" />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </motion.div>
        )}

        {/* Idle empty state */}
        {status === "idle" && (
          <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Card className="bg-white/60 border-dashed">
              <CardContent className="py-12 text-center space-y-3">
                <div className="text-5xl">🧬</div>
                <p className="font-semibold text-slate-600">Ready to trace evolution</p>
                <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                  Select an origin and destination idea above, then click "Find Evolution Path" to see how knowledge evolved between them.
                </p>
                <div className="flex justify-center gap-4 pt-2 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-purple-500" /> Philosophy</div>
                  <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-blue-500" /> Scientific</div>
                  <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-orange-500" /> Engineering</div>
                  <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-green-500" /> Modern</div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
