import React, { useState, useMemo, useEffect, useRef, useCallback } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { forceCollide } from "d3-force";
import { motion, AnimatePresence } from "framer-motion";
import {
  Lightbulb, TrendingUp, Zap, Cpu,
  Search, Calendar, Network, BarChart3,
  ChevronDown, ArrowRight, Atom, Brain,
  Flame, Sparkles, AlertTriangle, Eye, Wand2, Loader2, Check
} from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card, CardContent, CardDescription,
  CardHeader, CardTitle
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select, SelectContent, SelectItem,
  SelectTrigger, SelectValue
} from "@/components/ui/select";

/* ——————— Demo Data: 3 Evolution Chains ——————— */

interface Idea {
  id: string;
  title: string;
  description: string;
  stage: string;
  start_year: number;
  end_year?: number;
  category: string;
  laureates: string[];
  keywords: string[];
  influence_score: number;
  chain: string;
}

interface InfluenceEdge {
  source: string;
  target: string;
  type: string;
  weight: number;
}

export const useEvolutionData = () => {
  const [ideas, setIdeas] = React.useState<Idea[]>([]);
  const [edges, setEdges] = React.useState<InfluenceEdge[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const load = async () => {
      try {
        const [iRes, eRes] = await Promise.all([
          fetch("http://localhost:5000/api/ideas?limit=400"),
          fetch("http://localhost:5000/api/graph/lineage")
        ]);
        const iData = await iRes.json();
        const eData = await eRes.json();
        
        if (iData?.data?.ideas) {
          setIdeas(iData.data.ideas.map((i: any) => ({
            ...i,
            chain: i.category || "General"
          })));
        }
        const graphEdges = eData?.data?.edges || eData?.data?.links || [];
        if (graphEdges.length > 0) {
          setEdges(graphEdges.map((l: any) => ({
            source: l.source,
            target: l.target,
            type: l.influence_type || "inspired_by",
            weight: l.influence_weight || 0.5
          })));
        }
      } catch (e) {
        console.error(e);
      } finally {
         setLoading(false);
      }
    };
    load();
  }, []);

  return { ideas, setIdeas, edges, loading };
};

/* ——————— Config ——————— */

const stageConfig: Record<string, {
  label: string; icon: typeof Lightbulb; color: string;
  textColor: string; bgColor: string; description: string;
  gradient: string;
}> = {
  philosophy: {
    label: "Philosophy", icon: Lightbulb,
    color: "bg-purple-500", textColor: "text-purple-700",
    bgColor: "bg-purple-50", description: "Initial philosophical concepts and theories",
    gradient: "from-purple-500 to-purple-700",
  },
  scientific_validation: {
    label: "Scientific Validation", icon: TrendingUp,
    color: "bg-blue-500", textColor: "text-blue-700",
    bgColor: "bg-blue-50", description: "Experimental validation and scientific proof",
    gradient: "from-blue-500 to-blue-700",
  },
  engineering_application: {
    label: "Engineering Application", icon: Zap,
    color: "bg-orange-500", textColor: "text-orange-700",
    bgColor: "bg-orange-50", description: "Practical engineering implementations",
    gradient: "from-orange-500 to-orange-700",
  },
  modern_technology: {
    label: "Modern Technology", icon: Cpu,
    color: "bg-green-500", textColor: "text-green-700",
    bgColor: "bg-green-50", description: "Current technological applications",
    gradient: "from-green-500 to-green-700",
  },
};

// Chain config built dynamically from data — see EvolutionTracker component
const chainConfig: Record<string, { label: string; icon: typeof Atom; color: string }> = {
  Physics: { label: "Physics", icon: Atom, color: "bg-blue-500" },
  Chemistry: { label: "Chemistry", icon: Brain, color: "bg-green-500" },
  Medicine: { label: "Medicine", icon: Zap, color: "bg-red-500" },
  Literature: { label: "Literature", icon: Lightbulb, color: "bg-yellow-500" },
  Peace: { label: "Peace", icon: Sparkles, color: "bg-purple-500" },
  Economics: { label: "Economics", icon: TrendingUp, color: "bg-orange-500" },
  General: { label: "General", icon: Cpu, color: "bg-gray-500" },
};

/* ——————— Lineage Graph Component ——————— */

const LineageGraphView = ({ ideas, edges }: { ideas: Idea[], edges: InfluenceEdge[] }) => {
  const fgRef = useRef<any>();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.offsetWidth,
        height: 600
      });
    }
  }, []);

  useEffect(() => {
    // Add collision force to prevent node overlap
    if (fgRef.current) {
      fgRef.current.d3Force("collide", forceCollide(30));
      fgRef.current.d3Force("charge").strength(-400);
    }
  }, []);

  const graphData = useMemo(() => {
    const nodes = ideas.map(idea => ({
      id: idea.id,
      name: idea.title,
      val: 20 + (idea.influence_score || 0) * 30, // Node size based on influence
      color: stageConfig[idea.stage]?.color.replace('text-', '').replace('bg-', '') || '#999', // Rough color extraction, handled below
      stage: idea.stage,
      chain: idea.chain,
      start_year: idea.start_year
    }));

    const stageColors: Record<string, string> = {
      philosophy: "#8b5cf6",
      scientific_validation: "#3b82f6",
      engineering_application: "#f97316",
      modern_technology: "#22c55e",
    };

    nodes.forEach(n => { n.color = stageColors[n.stage] || '#999'; });

    const ideaMap = Object.fromEntries(ideas.map(i => [i.id, i]));
    const links = edges.map(edge => ({
      source: edge.source,
      target: edge.target,
      isCross: ideaMap[edge.source]?.chain !== ideaMap[edge.target]?.chain
    }));

    return { nodes, links };
  }, [ideas, edges]);

  return (
    <Card className="bg-white/80 backdrop-blur-sm overflow-hidden">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Network className="h-5 w-5" />
          Interactive Lineage Graph
        </CardTitle>
        <CardDescription>
          Force-directed graph showing how ideas influence and evolve into each other. Scroll to zoom, drag to pan.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div ref={containerRef} className="w-full bg-slate-50/50 rounded-xl border overflow-hidden flex justify-center">
          <ForceGraph2D
            ref={fgRef}
            width={dimensions.width}
            height={dimensions.height}
            graphData={graphData}
            nodeLabel="name"
            nodeColor="color"
            nodeRelSize={1}
            linkColor={(link: any) => link.isCross ? "#a78bfa" : "#94a3b8"}
            linkWidth={(link: any) => link.isCross ? 1.5 : 2}
            linkLineDash={(link: any) => link.isCross ? [6, 3] : undefined}
            linkDirectionalArrowLength={6}
            linkDirectionalArrowRelPos={1}
            cooldownTicks={100}
            nodeCanvasObject={(node: any, ctx, globalScale) => {
              const label = node.name.length > 20 ? node.name.substring(0, 18) + "..." : node.name;
              const fontSize = 12 / globalScale;
              ctx.font = `${fontSize}px Sans-Serif`;
              
              // Draw circle
              ctx.beginPath();
              ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI, false);
              ctx.fillStyle = node.color;
              ctx.fill();
              
              // Draw light halo
              ctx.beginPath();
              ctx.arc(node.x, node.y, Math.sqrt(node.val) * 2, 0, 2 * Math.PI, false);
              ctx.fillStyle = node.color + "33"; // 20% opacity
              ctx.fill();
              
              const textWidth = ctx.measureText(label).width;
              ctx.fillStyle = "#334155";
              
              // Only draw text if zoomed in enough or if node is large
              if (globalScale > 1.2 || node.val > 40) {
                 ctx.fillText(label, node.x - textWidth / 2, node.y + 16);
                 
                 ctx.font = `${fontSize * 0.8}px Sans-Serif`;
                 ctx.fillStyle = "#64748b";
                 ctx.fillText(node.start_year.toString(), node.x - ctx.measureText(node.start_year.toString()).width / 2, node.y + 16 + fontSize);
              }
            }}
          />
        </div>

        {/* Legend */}
        <div className="flex flex-wrap justify-center gap-4 mt-4 text-xs text-muted-foreground">
          {Object.entries(stageConfig).map(([key, cfg]) => {
            const stageColors: Record<string, string> = {
              philosophy: "#8b5cf6",
              scientific_validation: "#3b82f6",
              engineering_application: "#f97316",
              modern_technology: "#22c55e",
            };
            return (
              <div key={key} className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: stageColors[key] }} />
                {cfg.label}
              </div>
            );
          })}
          <div className="flex items-center gap-1.5">
            <div className="w-6 border-t-2 border-dashed border-purple-400" />
            Cross-chain
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

/* ——————— Main Component ——————— */

const EvolutionTracker = () => {
  const { ideas, setIdeas, edges, loading } = useEvolutionData();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStage, setSelectedStage] = useState<string | null>(null);
  const [selectedChain, setSelectedChain] = useState("all");
  const [startYear, setStartYear] = useState("");
  const [endYear, setEndYear] = useState("");
  const [summarizingIds, setSummarizingIds] = useState<Set<string>>(new Set());
  const [summarizedIds, setSummarizedIds] = useState<Set<string>>(new Set());
  const [llmConfigured, setLlmConfigured] = useState<boolean | null>(null);

  // Check if LLM is configured on mount
  useEffect(() => {
    fetch("http://localhost:5000/api/llm/status")
      .then(r => r.json())
      .then(d => setLlmConfigured(d?.data?.configured ?? false))
      .catch(() => setLlmConfigured(false));
  }, []);

  const handleSummarize = useCallback(async (ideaId: string) => {
    setSummarizingIds(prev => new Set(prev).add(ideaId));
    try {
      const res = await fetch(`http://localhost:5000/api/llm/summarize/${ideaId}`, {
        method: "POST",
      });
      const data = await res.json();
      if (data?.data?.description) {
        // Update the idea in the local state via setState to trigger re-render
        setIdeas(prev => prev.map(i => 
          i.id === ideaId ? { ...i, description: data.data.description } : i
        ));
        setSummarizedIds(prev => new Set(prev).add(ideaId));
        // Clear the checkmark after 3 seconds
        setTimeout(() => setSummarizedIds(prev => {
          const next = new Set(prev);
          next.delete(ideaId);
          return next;
        }), 3000);
      }
    } catch (err) {
      console.error("LLM summarize failed:", err);
    } finally {
      setSummarizingIds(prev => {
        const next = new Set(prev);
        next.delete(ideaId);
        return next;
      });
    }
  }, [ideas]);

    const filteredIdeas = useMemo(() => {
    return ideas.filter((idea) => {
      const s = searchTerm.toLowerCase();
      const matchesSearch =
        !s ||
        (idea.title || "").toLowerCase().includes(s) ||
        (idea.description || "").toLowerCase().includes(s) ||
        (idea.keywords || []).some((k) => (k || "").toLowerCase().includes(s));
      const matchesStage = !selectedStage || idea.stage === selectedStage;
      const matchesChain = selectedChain === "all" || idea.chain === selectedChain;
      const matchesYear =
        (!startYear || idea.start_year >= parseInt(startYear)) &&
        (!endYear || idea.start_year <= parseInt(endYear));
      return matchesSearch && matchesStage && matchesChain && matchesYear;
    });
  }, [ideas, searchTerm, selectedStage, selectedChain, startYear, endYear]);

  const stats = useMemo(() => {
    const years = ideas.map((i) => i.start_year);
    const uniqueChains = new Set(ideas.map(i => i.chain)).size;
    return {
      totalIdeas: ideas.length,
      chains: uniqueChains,
      timeSpan: years.length > 0 ? Math.max(...years) - Math.min(...years) : 0,
      avgInfluence: ideas.length > 0 ? (
        ideas.reduce((s, i) => s + i.influence_score, 0) / ideas.length
      ).toFixed(2) : "0.00",
    };
  }, [ideas]);

  // Build dynamic chain list from actual data
  const chainList = useMemo(() => {
    const cats = [...new Set(ideas.map(i => i.chain))].sort();
    return cats;
  }, [ideas]);

  // Top 3 categories for stat card display
  const topChains = useMemo(() => {
    const counts: Record<string, number> = {};
    ideas.forEach(i => { counts[i.chain] = (counts[i.chain] || 0) + 1; });
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([name]) => name);
  }, [ideas]);

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-xl font-bold text-gray-500">Loading Evolution Data...</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50">
      {/* Header */}
      <header className="border-b border-border bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container py-6">
          <motion.div
            initial={{ opacity: 0, y: -16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center shadow-lg">
                <Lightbulb className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                  Theory-to-Reality Evolution Tracker
                </h1>
                <p className="text-sm text-muted-foreground">
                  Track how ideas evolve from philosophy to modern technology
                </p>
              </div>
            </div>
            
            <div className="flex gap-2 justify-end mt-4 md:mt-0 md:absolute md:right-8 md:top-6">
               <button onClick={() => window.open('http://localhost:5000/api/export/dataset?format=csv', '_blank')} className="px-4 py-2 text-xs font-semibold bg-white border shadow-sm rounded-md hover:bg-slate-50 transition-colors">
                  Export CSV
               </button>
               <button onClick={() => window.open('http://localhost:5000/api/export/dataset?format=json', '_blank')} className="px-4 py-2 text-xs font-semibold bg-white border shadow-sm rounded-md hover:bg-slate-50 transition-colors">
                  Export JSON
               </button>
            </div>
          </motion.div>
        </div>
      </header>

      <main className="container py-8 space-y-8">
        {/* Stats Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4"
        >
          <Card className="border-purple-200 bg-white/80 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Ideas</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-600">{stats.totalIdeas}</div>
              <p className="text-xs text-muted-foreground mt-1">Across all stages</p>
            </CardContent>
          </Card>
          <Card className="border-blue-200 bg-white/80 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Evolution Chains</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">{stats.chains}</div>
              <p className="text-xs text-muted-foreground mt-1">{topChains.join(" · ")}</p>
            </CardContent>
          </Card>
          <Card className="border-orange-200 bg-white/80 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Time Span</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-orange-600">{stats.timeSpan}</div>
              <p className="text-xs text-muted-foreground mt-1">Years of evolution</p>
            </CardContent>
          </Card>
          <Card className="border-green-200 bg-white/80 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Avg Influence</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">{stats.avgInfluence}</div>
              <p className="text-xs text-muted-foreground mt-1">Impact score</p>
            </CardContent>
          </Card>
        </motion.div>

        {/* Tabs */}
        <Tabs defaultValue="timeline" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 bg-white/80 backdrop-blur-sm">
            <TabsTrigger value="timeline" className="flex items-center gap-2">
              <Calendar className="h-4 w-4" /> Timeline
            </TabsTrigger>
            <TabsTrigger value="graph" className="flex items-center gap-2">
              <Network className="h-4 w-4" /> Lineage Graph
            </TabsTrigger>
            <TabsTrigger value="analysis" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" /> Analysis
            </TabsTrigger>
            <TabsTrigger value="predictions" className="flex items-center gap-2">
              <Sparkles className="h-4 w-4" /> Predictions
            </TabsTrigger>
          </TabsList>

          {/* ─── TIMELINE TAB ─── */}
          <TabsContent value="timeline" className="space-y-6">
            {/* Search & Filters */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
              <Card className="bg-white/80 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Search className="h-5 w-5" /> Search & Filter
                  </CardTitle>
                  <CardDescription>Find ideas by name, stage, chain, or time period</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-col md:flex-row gap-4">
                    <div className="flex-1">
                      <Input
                        placeholder="Search ideas, keywords..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                      />
                    </div>
                    <Select value={selectedChain} onValueChange={setSelectedChain}>
                      <SelectTrigger className="w-52">
                        <SelectValue placeholder="All Chains" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Chains</SelectItem>
                        {chainList.map((cat) => (
                          <SelectItem key={cat} value={cat}>
                            {cat}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <div className="flex gap-2">
                      <Input type="number" placeholder="Start Year" value={startYear}
                        onChange={(e) => setStartYear(e.target.value)} className="w-32" />
                      <Input type="number" placeholder="End Year" value={endYear}
                        onChange={(e) => setEndYear(e.target.value)} className="w-32" />
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant={selectedStage === null ? "default" : "outline"}
                      className="cursor-pointer" onClick={() => setSelectedStage(null)}>
                      All Stages
                    </Badge>
                    {Object.entries(stageConfig).map(([key, config]) => (
                      <Badge key={key}
                        variant={selectedStage === key ? "default" : "outline"}
                        className="cursor-pointer"
                        onClick={() => setSelectedStage(key)}>
                        {config.label}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Timeline */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
              <Card className="bg-white/80 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calendar className="h-5 w-5" /> Evolution Timeline
                  </CardTitle>
                  <CardDescription>
                    Showing {filteredIdeas.length} of {ideas.length} ideas
                    {selectedChain !== "all" && ` · ${chainConfig[selectedChain].label}`}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="relative">
                    <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-purple-500 via-blue-500 via-orange-500 to-green-500" />
                    <div className="space-y-8">
                      <AnimatePresence mode="popLayout">
                        {filteredIdeas.map((idea, index) => {
                          const config = stageConfig[idea.stage];
                          const Icon = config.icon;
                          return (
                            <motion.div
                              key={idea.id}
                              layout
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              exit={{ opacity: 0, x: 20 }}
                              transition={{ delay: index * 0.05 }}
                              className="relative pl-20"
                            >
                              <div className={`absolute left-4 w-8 h-8 rounded-full ${config.color} flex items-center justify-center shadow-lg`}>
                                <Icon className="h-4 w-4 text-white" />
                              </div>
                              <Card className={`${config.bgColor} border-2 hover:shadow-lg transition-all duration-300`}>
                                <CardHeader>
                                  <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                      <div className="flex items-center gap-2">
                                        <CardTitle className="text-lg">{idea.title}</CardTitle>
                                        <Badge variant="secondary" className="text-[10px]">
                                          {chainConfig[idea.chain]?.label}
                                        </Badge>
                                      </div>
                                      <CardDescription className="mt-1">{idea.description}</CardDescription>
                                    </div>
                                    <Badge className={config.color}>
                                      {idea.start_year}
                                      {idea.end_year && ` – ${idea.end_year}`}
                                    </Badge>
                                  </div>
                                </CardHeader>
                                <CardContent>
                                  <div className="space-y-2">
                                    <div className="flex items-center gap-2 text-sm">
                                      <span className="font-medium">Stage:</span>
                                      <Badge variant="outline" className={config.textColor}>{config.label}</Badge>
                                    </div>
                                    <div className="flex items-center gap-2 text-sm">
                                      <span className="font-medium">Category:</span>
                                      <span className="text-muted-foreground">{idea.category}</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-sm">
                                      <span className="font-medium">Laureates:</span>
                                      <span className="text-muted-foreground">{idea.laureates.join(", ")}</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-sm">
                                      <span className="font-medium">Influence:</span>
                                      <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-xs">
                                        <motion.div
                                          className={`${config.color} h-2 rounded-full`}
                                          initial={{ width: 0 }}
                                          animate={{ width: `${idea.influence_score * 100}%` }}
                                          transition={{ delay: 0.5 + index * 0.05, duration: 0.6 }}
                                        />
                                      </div>
                                      <span className="text-muted-foreground">{(idea.influence_score * 100).toFixed(0)}%</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1 mt-2">
                                      {idea.keywords.map((kw) => (
                                        <Badge key={kw} variant="secondary" className="text-xs">{kw}</Badge>
                                      ))}
                                    </div>
                                    {/* AI Summarize Button */}
                                    {llmConfigured && (
                                      <div className="mt-3 pt-3 border-t border-gray-200/60">
                                        <button
                                          onClick={() => handleSummarize(idea.id)}
                                          disabled={summarizingIds.has(idea.id)}
                                          className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-300 ${
                                            summarizedIds.has(idea.id)
                                              ? "bg-green-100 text-green-700 border border-green-300"
                                              : summarizingIds.has(idea.id)
                                              ? "bg-violet-50 text-violet-400 border border-violet-200 cursor-wait"
                                              : "bg-gradient-to-r from-violet-50 to-purple-50 text-violet-700 border border-violet-200 hover:from-violet-100 hover:to-purple-100 hover:shadow-sm cursor-pointer"
                                          }`}
                                        >
                                          {summarizedIds.has(idea.id) ? (
                                            <><Check className="h-3.5 w-3.5" /> Generated</>
                                          ) : summarizingIds.has(idea.id) ? (
                                            <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Generating...</>
                                          ) : (
                                            <><Wand2 className="h-3.5 w-3.5" /> AI Summarize</>
                                          )}
                                        </button>
                                      </div>
                                    )}
                                  </div>
                                </CardContent>
                              </Card>
                            </motion.div>
                          );
                        })}
                      </AnimatePresence>
                    </div>
                  </div>
                  {filteredIdeas.length === 0 && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-12">
                      <p className="text-muted-foreground">No ideas found matching your criteria</p>
                    </motion.div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </TabsContent>

          {/* ─── LINEAGE GRAPH TAB ─── */}
          <TabsContent value="graph">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
              <LineageGraphView ideas={ideas} edges={edges} />
            </motion.div>
          </TabsContent>

          {/* ─── ANALYSIS TAB ─── */}
          <TabsContent value="analysis" className="space-y-6">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Stage Distribution */}
              <Card className="bg-white/80 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-base">Ideas by Evolution Stage</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {Object.entries(stageConfig).map(([key, cfg]) => {
                    const count = ideas.filter(i => i.stage === key).length;
                    const pct = (count / ideas.length) * 100;
                    return (
                      <div key={key} className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span className={cfg.textColor + " font-medium"}>{cfg.label}</span>
                          <span className="text-muted-foreground">{count} ideas</span>
                        </div>
                        <div className="bg-gray-100 rounded-full h-2">
                          <motion.div
                            className={`${cfg.color} h-2 rounded-full`}
                            initial={{ width: 0 }}
                            animate={{ width: `${pct}%` }}
                            transition={{ duration: 0.8 }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>

              {/* Chain Summary */}
              <Card className="bg-white/80 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-base">Evolution Chains</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {Array.from(new Set(ideas.map(i => i.chain))).map((chain) => {
                    const chainIdeas = ideas.filter(i => i.chain === chain);
                    const cfg = chainConfig[chain];
                    const yearStart = Math.min(...chainIdeas.map(i => i.start_year));
                    const yearEnd = Math.max(...chainIdeas.map(i => i.end_year || i.start_year));
                    return (
                      <div key={chain} className="p-3 rounded-lg bg-gray-50 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className={`font-semibold ${cfg?.accent || 'text-gray-600'}`}>{cfg?.label || chain}</span>
                          <Badge variant="outline">{yearEnd - yearStart} years</Badge>
                        </div>
                        <div className="flex items-center gap-1 text-xs text-muted-foreground flex-wrap">
                          {chainIdeas.slice(0, 5).map((idea, i) => (
                            <span key={idea.id} className="flex items-center gap-1">
                              <span className={stageConfig[idea.stage]?.textColor}>
                                {idea.title}
                              </span>
                              {i < chainIdeas.slice(0, 5).length - 1 && <ArrowRight className="h-3 w-3 text-gray-400" />}
                            </span>
                          ))}
                          {chainIdeas.length > 5 && <span>... ({chainIdeas.length} total)</span>}
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>

              {/* Top Influential Ideas */}
              <Card className="bg-white/80 backdrop-blur-sm md:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base">Most Influential Ideas</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                    {[...ideas]
                      .sort((a, b) => b.influence_score - a.influence_score)
                      .slice(0, 6)
                      .map((idea, i) => {
                        const cfg = stageConfig[idea.stage];
                        return (
                          <motion.div
                            key={idea.id}
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: i * 0.08 }}
                            className={`p-3 rounded-lg ${cfg.bgColor} border`}
                          >
                            <div className="flex items-start justify-between">
                              <div className="font-medium text-sm">{idea.title}</div>
                              <span className={`text-lg font-bold ${cfg.textColor}`}>
                                {(idea.influence_score * 100).toFixed(0)}%
                              </span>
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                              {idea.start_year} · {idea.category}
                            </div>
                          </motion.div>
                        );
                      })}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </TabsContent>

          {/* ─── PREDICTIONS TAB ─── */}
          <TabsContent value="predictions" className="space-y-6">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
              {/* ── Dormant Ideas ── */}
              <Card className="bg-white/80 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-amber-500" />
                    Dormant Ideas — Sleeping Potential
                  </CardTitle>
                  <CardDescription>
                    Ideas scoring high on age, low connectivity, and distance from modern technology
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {(() => {
                    const CURRENT_YEAR = new Date().getFullYear();
                    const scored = ideas.map((idea) => {
                      const age = CURRENT_YEAR - idea.start_year;
                      const ageScore = Math.min(age / 200, 1);
                      const stageOrder: Record<string, number> = { philosophy: 0, scientific_validation: 1, engineering_application: 2, modern_technology: 3 };
                      const stallScore = 1 - (stageOrder[idea.stage] || 0) / 3;
                      const edgeCount = edges.filter(e => e.source === idea.id || e.target === idea.id).length;
                      const connectScore = 1 - Math.min(edgeCount / 4, 1);
                      const dormancy = 0.3 * ageScore + 0.35 * stallScore + 0.35 * connectScore;
                      return { ...idea, dormancy: Math.round(dormancy * 100) / 100 };
                    }).sort((a, b) => b.dormancy - a.dormancy);

                    return scored.filter(s => s.dormancy > 0.4).map((idea, i) => {
                      const cfg = stageConfig[idea.stage];
                      return (
                        <motion.div key={idea.id}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.08 }}
                          className={`p-4 rounded-xl border-2 border-amber-200 ${cfg.bgColor}`}
                        >
                          <div className="flex items-start justify-between">
                            <div>
                              <div className="font-semibold">{idea.title}</div>
                              <div className="text-xs text-muted-foreground mt-1">
                                {idea.start_year} · {cfg.label}
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-lg font-bold text-amber-600">{(idea.dormancy * 100).toFixed(0)}%</div>
                              <div className="text-[10px] text-muted-foreground">Dormancy</div>
                            </div>
                          </div>
                          <div className="mt-2 bg-amber-100 rounded-full h-2">
                            <motion.div className="bg-amber-500 h-2 rounded-full"
                              initial={{ width: 0 }} animate={{ width: `${idea.dormancy * 100}%` }}
                              transition={{ duration: 0.8, delay: i * 0.1 }}
                            />
                          </div>
                          <div className="text-xs text-amber-700 mt-2">
                            {idea.dormancy > 0.6 ? "High dormancy — old concept, low connectivity" :
                             idea.dormancy > 0.4 ? "Moderate dormancy — may have revival potential" : ""}
                          </div>
                        </motion.div>
                      );
                    });
                  })()}
                </CardContent>
              </Card>

              {/* ── Forecast Dashboard ── */}
              <Card className="bg-white/80 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-violet-500" />
                    Evolution Forecast
                  </CardTitle>
                  <CardDescription>
                    Predicted next stage for each idea with confidence score
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {ideas.map((idea, i) => {
                      const stages = ["philosophy", "scientific_validation", "engineering_application", "modern_technology"];
                      const idx = stages.indexOf(idea.stage);
                      const nextIdx = Math.min(idx + 1, 3);
                      const nextStage = stages[nextIdx];
                      const nextCfg = stageConfig[nextStage];
                      const cfg = stageConfig[idea.stage];
                      const confidence = idx === 3 ? 0.95 : Math.min(0.4 + idea.influence_score * 0.4 + (idx / 3) * 0.2, 0.95);
                      const NextIcon = nextCfg.icon;

                      return (
                        <motion.div key={idea.id}
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: i * 0.06 }}
                          className={`p-4 rounded-xl ${cfg.bgColor} border space-y-3`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="font-semibold text-sm">{idea.title}</div>
                            <NextIcon className={`h-4 w-4 ${nextCfg.textColor}`} />
                          </div>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Badge variant="outline" className={cfg.textColor}>{cfg.label}</Badge>
                            <ArrowRight className="h-3 w-3" />
                            <Badge variant="outline" className={nextCfg.textColor}>{nextCfg.label}</Badge>
                          </div>
                          <div className="space-y-1">
                            <div className="flex justify-between text-xs">
                              <span className="font-medium">Confidence</span>
                              <span className={`font-bold ${confidence > 0.7 ? 'text-green-600' : confidence > 0.5 ? 'text-amber-600' : 'text-red-500'}`}>
                                {(confidence * 100).toFixed(0)}%
                              </span>
                            </div>
                            <div className="bg-gray-200 rounded-full h-2">
                              <motion.div
                                className={`h-2 rounded-full ${confidence > 0.7 ? 'bg-green-500' : confidence > 0.5 ? 'bg-amber-500' : 'bg-red-400'}`}
                                initial={{ width: 0 }}
                                animate={{ width: `${confidence * 100}%` }}
                                transition={{ duration: 0.6, delay: 0.3 + i * 0.05 }}
                              />
                            </div>
                          </div>
                          <div className="text-[10px] text-muted-foreground italic">
                            {idx === 3 ? "Already at Modern Technology" :
                             confidence > 0.7 ? "Strong trajectory — high influence + connectivity" :
                             "Moderate potential — may need more validation"}
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>

              {/* ── Similarity Map ── */}
              <Card className="bg-white/80 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Eye className="h-5 w-5 text-blue-500" />
                    Keyword Similarity Map
                  </CardTitle>
                  <CardDescription>
                    Ideas sharing common keywords — potential undiscovered connections
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {ideas.slice(0, 6).map((idea, idx) => {
                      const others = ideas.filter(o => o.id !== idea.id);
                      const withOverlap = others.map(o => ({
                        ...o,
                        common: idea.keywords.filter(k => o.keywords.includes(k)),
                      })).filter(o => o.common.length > 0).sort((a, b) => b.common.length - a.common.length).slice(0, 2);

                      if (withOverlap.length === 0) return null;
                      const cfg = stageConfig[idea.stage];
                      return (
                        <motion.div key={idea.id}
                          initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                          transition={{ delay: idx * 0.06 }}
                          className={`p-3 rounded-lg ${cfg.bgColor} border`}
                        >
                          <div className="flex items-center gap-2 mb-2">
                            <span className={`font-medium text-sm ${cfg.textColor}`}>{idea.title}</span>
                            <Badge variant="secondary" className="text-[10px]">{idea.start_year}</Badge>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {withOverlap.map(sim => (
                              <div key={sim.id} className="flex items-center gap-1 bg-white/60 rounded-lg px-2 py-1 text-xs">
                                <span className="font-medium">{sim.title}</span>
                                <span className="text-muted-foreground">·</span>
                                {sim.common.map(k => (
                                  <Badge key={k} variant="outline" className="text-[9px] px-1">{k}</Badge>
                                ))}
                              </div>
                            ))}
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default EvolutionTracker;
