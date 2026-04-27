import React, { useState, useMemo, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Lightbulb, TrendingUp, Zap, Cpu,
  Search, Calendar, Network, BarChart3,
  ChevronDown, ArrowRight, Atom, Brain,
  Flame, Sparkles, AlertTriangle, Eye, Wand2, Loader2, Check,
  Route
} from "lucide-react";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, AreaChart, Area } from "recharts";
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
import IdeaDetailPanel from "@/components/IdeaDetailPanel";
import NodeSelector from "@/components/NodeSelector";
import EvolutionPathFinder from "@/components/EvolutionPathFinder";

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

const STAGE_ORDER = ["philosophy", "scientific_validation", "engineering_application", "modern_technology"] as const;
const STAGE_LABELS: Record<string, string> = {
  philosophy: "Philosophy",
  scientific_validation: "Scientific Validation",
  engineering_application: "Engineering Application",
  modern_technology: "Modern Technology",
};
const STAGE_COLORS: Record<string, string> = {
  philosophy: "#8b5cf6",
  scientific_validation: "#3b82f6",
  engineering_application: "#f97316",
  modern_technology: "#22c55e",
};

const LineageGraphView = ({ ideas, edges, onNodeClick }: { ideas: Idea[], edges: InfluenceEdge[], onNodeClick?: (id: string) => void }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [graphIdeas, setGraphIdeas] = useState<Idea[]>(ideas);
  const [graphEdges, setGraphEdges] = useState<InfluenceEdge[]>(edges);
  const [graphLoading, setGraphLoading] = useState(false);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  // Load full graph data independently when tab is shown
  useEffect(() => {
    const load = async () => {
      setGraphLoading(true);
      try {
        const [iRes, eRes] = await Promise.all([
          fetch("http://localhost:5000/api/ideas?limit=200"),
          fetch("http://localhost:5000/api/graph/lineage")
        ]);
        const iData = await iRes.json();
        const eData = await eRes.json();
        if (iData?.data?.ideas) {
          setGraphIdeas(iData.data.ideas.map((i: any) => ({ ...i, chain: i.category || "General" })));
        }
        const rawEdges = eData?.data?.edges || [];
        setGraphEdges(rawEdges.map((l: any) => ({
          source: l.source, target: l.target,
          type: l.influence_type || "inspired_by", weight: l.influence_weight || 0.5
        })));
      } catch (e) { console.error(e); }
      finally { setGraphLoading(false); }
    };
    load();
  }, []);

  // Compute hierarchical tree layout
  const layout = useMemo(() => {
    const activeIdeas = graphIdeas.length > 0 ? graphIdeas : ideas;
    const activeEdges = graphEdges.length > 0 ? graphEdges : edges;

    // Build adjacency lists
    const children: Record<string, string[]> = {};
    const parents: Record<string, string[]> = {};
    activeIdeas.forEach(idea => {
      children[idea.id] = [];
      parents[idea.id] = [];
    });
    activeEdges.forEach(edge => {
      if (children[edge.source] && parents[edge.target]) {
        children[edge.source].push(edge.target);
        parents[edge.target].push(edge.source);
      }
    });

    // Find root nodes (no parents)
    const roots = activeIdeas.filter(idea => parents[idea.id].length === 0);

    // Layout constants - compact tree style
    const NODE_W = 180;
    const NODE_H = 90;
    const LEVEL_GAP_Y = 120;
    const SIBLING_GAP_X = 30;
    const TREE_GAP_X = 100;
    const PADDING_X = 40;
    const PADDING_TOP = 40;

    const nodePositions: Record<string, { x: number; y: number; w: number; h: number; stage: string; color: string; idea: Idea; level: number }> = {};
    const validEdges = activeEdges.filter(e => 
      activeIdeas.some(i => i.id === e.source) && activeIdeas.some(i => i.id === e.target)
    );

    // Calculate subtree width for each node
    const getSubtreeWidth = (nodeId: string, visited: Set<string> = new Set()): number => {
      if (visited.has(nodeId)) return NODE_W;
      visited.add(nodeId);
      
      const childIds = children[nodeId] || [];
      if (childIds.length === 0) return NODE_W;
      
      const childrenWidth = childIds.reduce((sum, childId) => 
        sum + getSubtreeWidth(childId, visited), 0
      );
      const gapsWidth = Math.max(0, childIds.length - 1) * SIBLING_GAP_X;
      return Math.max(NODE_W, childrenWidth + gapsWidth);
    };

    // Layout tree recursively
    const layoutTree = (
      nodeId: string,
      x: number,
      y: number,
      level: number,
      visited: Set<string> = new Set()
    ): number => {
      if (visited.has(nodeId)) return x;
      visited.add(nodeId);

      const idea = activeIdeas.find(i => i.id === nodeId);
      if (!idea) return x;

      const stage = idea.stage || "philosophy";
      const color = STAGE_COLORS[stage] || "#999";

      const childIds = children[nodeId] || [];
      const subtreeWidth = getSubtreeWidth(nodeId, new Set());

      // Position current node at center of its subtree
      const nodeX = x + subtreeWidth / 2 - NODE_W / 2;
      nodePositions[nodeId] = {
        x: nodeX,
        y,
        w: NODE_W,
        h: NODE_H,
        stage,
        color,
        idea,
        level
      };

      // Layout children
      if (childIds.length > 0) {
        let childX = x;
        childIds.forEach(childId => {
          const childWidth = getSubtreeWidth(childId, new Set());
          layoutTree(childId, childX, y + LEVEL_GAP_Y, level + 1, visited);
          childX += childWidth + SIBLING_GAP_X;
        });
      }

      return x + subtreeWidth;
    };

    // Layout each tree
    let currentX = PADDING_X;
    const visited = new Set<string>();
    
    roots.forEach(root => {
      if (!visited.has(root.id)) {
        const treeWidth = getSubtreeWidth(root.id, new Set());
        layoutTree(root.id, currentX, PADDING_TOP, 0, visited);
        currentX += treeWidth + TREE_GAP_X;
      }
    });

    // Layout orphaned nodes (nodes with parents but not yet positioned)
    const orphans = activeIdeas.filter(idea => !nodePositions[idea.id]);
    orphans.forEach((idea, idx) => {
      const stage = idea.stage || "philosophy";
      const color = STAGE_COLORS[stage] || "#999";
      nodePositions[idea.id] = {
        x: currentX + (idx % 5) * (NODE_W + SIBLING_GAP_X),
        y: PADDING_TOP + Math.floor(idx / 5) * LEVEL_GAP_Y,
        w: NODE_W,
        h: NODE_H,
        stage,
        color,
        idea,
        level: 0
      };
    });

    // Calculate total dimensions
    const allX = Object.values(nodePositions).map(p => p.x + p.w);
    const allY = Object.values(nodePositions).map(p => p.y + p.h);
    const totalWidth = Math.max(...allX, 800) + PADDING_X;
    const totalHeight = Math.max(...allY, 600) + PADDING_TOP;

    // Group by stage for legend
    const stageGroups: Record<string, Idea[]> = {};
    STAGE_ORDER.forEach(s => { stageGroups[s] = []; });
    activeIdeas.forEach(idea => {
      const stage = idea.stage || "philosophy";
      if (stageGroups[stage]) {
        stageGroups[stage].push(idea);
      }
    });

    return { nodePositions, validEdges, totalWidth, totalHeight, stageGroups };
  }, [graphIdeas, graphEdges, ideas, edges]);

  // Get highlighted edges (connected to hovered node)
  const highlightedEdges = useMemo(() => {
    if (!hoveredNode) return new Set<string>();
    const set = new Set<string>();
    layout.validEdges.forEach(e => {
      if (e.source === hoveredNode || e.target === hoveredNode) {
        set.add(`${e.source}-${e.target}`);
      }
    });
    return set;
  }, [hoveredNode, layout.validEdges]);

  const connectedNodes = useMemo(() => {
    if (!hoveredNode) return new Set<string>();
    const set = new Set<string>([hoveredNode]);
    layout.validEdges.forEach(e => {
      if (e.source === hoveredNode) set.add(e.target);
      if (e.target === hoveredNode) set.add(e.source);
    });
    return set;
  }, [hoveredNode, layout.validEdges]);

  return (
    <Card className="bg-white/80 backdrop-blur-sm overflow-hidden">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Network className="h-5 w-5" />
          Hierarchical Tree View
          {graphLoading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground ml-2" />}
        </CardTitle>
        <CardDescription>
          Tree structure showing idea evolution and relationships • {Object.keys(layout.nodePositions).length} nodes, {layout.validEdges.length} connections
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div
          ref={containerRef}
          className="w-full bg-gradient-to-br from-slate-50 via-white to-blue-50 rounded-xl border border-slate-200 shadow-inner overflow-auto relative"
          style={{ maxHeight: "75vh" }}
        >
          <svg
            width={layout.totalWidth}
            height={layout.totalHeight}
            className="block"
            style={{ minWidth: layout.totalWidth }}
          >
            {/* Defs for gradients and filters */}
            <defs>
              <filter id="cardShadow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur in="SourceAlpha" stdDeviation="2"/>
                <feOffset dx="0" dy="1" result="offsetblur"/>
                <feComponentTransfer>
                  <feFuncA type="linear" slope="0.15"/>
                </feComponentTransfer>
                <feMerge>
                  <feMergeNode/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
              
              <linearGradient id="purpleGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#a78bfa" />
                <stop offset="100%" stopColor="#8b5cf6" />
              </linearGradient>
              
              <linearGradient id="blueGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#60a5fa" />
                <stop offset="100%" stopColor="#3b82f6" />
              </linearGradient>
              
              <linearGradient id="orangeGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#fb923c" />
                <stop offset="100%" stopColor="#f97316" />
              </linearGradient>
              
              <linearGradient id="greenGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#4ade80" />
                <stop offset="100%" stopColor="#22c55e" />
              </linearGradient>
            </defs>

            {/* Connection lines - tree style */}
            {layout.validEdges.map((edge, idx) => {
              const src = layout.nodePositions[edge.source];
              const tgt = layout.nodePositions[edge.target];
              if (!src || !tgt) return null;

              const isHighlighted = hoveredNode === edge.source || hoveredNode === edge.target || 
                                   selectedNode === edge.source || selectedNode === edge.target;
              const isDimmed = (hoveredNode || selectedNode) && !isHighlighted;

              // Parent (source) bottom-center to child (target) top-center
              const x1 = src.x + src.w / 2;
              const y1 = src.y + src.h;
              const x2 = tgt.x + tgt.w / 2;
              const y2 = tgt.y;

              // Tree-style connection: vertical from parent, horizontal, then vertical to child
              const midY = y1 + (y2 - y1) / 2;

              const isCross = src.stage !== tgt.stage;
              const edgeColor = isCross ? "#a855f7" : "#6366f1";

              return (
                <g key={idx}>
                  {/* Vertical line from parent */}
                  <line
                    x1={x1}
                    y1={y1}
                    x2={x1}
                    y2={midY}
                    stroke={edgeColor}
                    strokeWidth={isHighlighted ? 2.5 : 1.5}
                    strokeOpacity={isDimmed ? 0.1 : isHighlighted ? 0.8 : 0.3}
                    strokeLinecap="round"
                  />
                  {/* Horizontal line */}
                  <line
                    x1={x1}
                    y1={midY}
                    x2={x2}
                    y2={midY}
                    stroke={edgeColor}
                    strokeWidth={isHighlighted ? 2.5 : 1.5}
                    strokeOpacity={isDimmed ? 0.1 : isHighlighted ? 0.8 : 0.3}
                    strokeLinecap="round"
                  />
                  {/* Vertical line to child */}
                  <line
                    x1={x2}
                    y1={midY}
                    x2={x2}
                    y2={y2}
                    stroke={edgeColor}
                    strokeWidth={isHighlighted ? 2.5 : 1.5}
                    strokeOpacity={isDimmed ? 0.1 : isHighlighted ? 0.8 : 0.3}
                    strokeLinecap="round"
                  />
                  {/* Junction dots */}
                  <circle
                    cx={x1}
                    cy={midY}
                    r={isHighlighted ? 4 : 3}
                    fill={edgeColor}
                    opacity={isDimmed ? 0.1 : isHighlighted ? 0.9 : 0.4}
                  />
                  <circle
                    cx={x2}
                    cy={midY}
                    r={isHighlighted ? 4 : 3}
                    fill={edgeColor}
                    opacity={isDimmed ? 0.1 : isHighlighted ? 0.9 : 0.4}
                  />
                </g>
              );
            })}

            {/* Node cards - compact tree style */}
            {Object.entries(layout.nodePositions).map(([id, pos]) => {
              const isHovered = hoveredNode === id;
              const isSelected = selectedNode === id;
              const isConnected = connectedNodes.has(id);
              const isDimmed = (hoveredNode || selectedNode) && !isConnected && hoveredNode !== id && selectedNode !== id;
              
              const truncTitle = pos.idea.title.length > 24 ? pos.idea.title.substring(0, 22) + "..." : pos.idea.title;
              
              // Get gradient based on stage
              const gradientId = pos.stage === "philosophy" ? "purpleGradient" :
                                pos.stage === "scientific_validation" ? "blueGradient" :
                                pos.stage === "engineering_application" ? "orangeGradient" : "greenGradient";

              return (
                <g
                  key={id}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  style={{ cursor: "pointer", transition: "all 0.2s ease" }}
                  opacity={isDimmed ? 0.25 : 1}
                  onMouseEnter={() => setHoveredNode(id)}
                  onMouseLeave={() => setHoveredNode(null)}
                  onClick={() => {
                    setSelectedNode(id === selectedNode ? null : id);
                    onNodeClick && onNodeClick(id);
                  }}
                >
                  {/* Card shadow */}
                  <rect
                    x={1}
                    y={1}
                    width={pos.w}
                    height={pos.h}
                    rx={10}
                    fill="rgba(0,0,0,0.08)"
                    filter="url(#cardShadow)"
                  />
                  
                  {/* Card background */}
                  <rect
                    x={0}
                    y={0}
                    width={pos.w}
                    height={pos.h}
                    rx={10}
                    fill="white"
                    stroke={isSelected ? pos.color : isHovered ? pos.color : "#e5e7eb"}
                    strokeWidth={isSelected ? 2.5 : isHovered ? 2 : 1}
                  />
                  
                  {/* Top colored header bar */}
                  <rect
                    x={0}
                    y={0}
                    width={pos.w}
                    height={6}
                    rx={10}
                    fill={`url(#${gradientId})`}
                  />
                  
                  {/* Small avatar circle */}
                  <circle
                    cx={pos.w / 2}
                    cy={26}
                    r={14}
                    fill={pos.color}
                    opacity={0.15}
                  />
                  <circle
                    cx={pos.w / 2}
                    cy={26}
                    r={12}
                    fill={pos.color}
                    opacity={0.25}
                  />
                  
                  {/* Icon in avatar */}
                  <text
                    x={pos.w / 2}
                    y={30}
                    fill={pos.color}
                    fontSize={12}
                    fontWeight="600"
                    textAnchor="middle"
                    fontFamily="Inter, system-ui, sans-serif"
                  >
                    💡
                  </text>
                  
                  {/* Title */}
                  <text
                    x={pos.w / 2}
                    y={52}
                    fill="#1e293b"
                    fontSize={11}
                    fontWeight="700"
                    textAnchor="middle"
                    fontFamily="Inter, system-ui, sans-serif"
                  >
                    {truncTitle}
                  </text>
                  
                  {/* Category */}
                  <text
                    x={pos.w / 2}
                    y={66}
                    fill={pos.color}
                    fontSize={9}
                    fontWeight="600"
                    textAnchor="middle"
                    fontFamily="Inter, system-ui, sans-serif"
                  >
                    {pos.idea.category.length > 20 ? pos.idea.category.substring(0, 18) + "..." : pos.idea.category}
                  </text>
                  
                  {/* Year */}
                  <text
                    x={pos.w / 2}
                    y={78}
                    fill="#94a3b8"
                    fontSize={8}
                    textAnchor="middle"
                    fontFamily="Inter, system-ui, sans-serif"
                  >
                    {pos.idea.start_year}
                  </text>
                  
                  {/* Influence indicator bar */}
                  <rect
                    x={15}
                    y={pos.h - 8}
                    width={pos.w - 30}
                    height={3}
                    rx={1.5}
                    fill="#e5e7eb"
                  />
                  <rect
                    x={15}
                    y={pos.h - 8}
                    width={(pos.w - 30) * pos.idea.influence_score}
                    height={3}
                    rx={1.5}
                    fill={pos.color}
                    opacity={0.8}
                  />
                  
                  {/* Hover/Select glow */}
                  {(isHovered || isSelected) && (
                    <rect
                      x={-2}
                      y={-2}
                      width={pos.w + 4}
                      height={pos.h + 4}
                      rx={12}
                      fill="none"
                      stroke={pos.color}
                      strokeWidth={2}
                      opacity={0.4}
                    />
                  )}
                </g>
              );
            })}
          </svg>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap justify-center gap-6 mt-4 text-xs">
          {STAGE_ORDER.map(key => (
            <div key={key} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full shadow-sm" style={{ backgroundColor: STAGE_COLORS[key] }} />
              <span className="font-medium text-slate-700">{STAGE_LABELS[key]}</span>
              <span className="text-slate-400">({layout.stageGroups[key]?.length || 0})</span>
            </div>
          ))}
        </div>
        
        <div className="text-center mt-3 text-xs text-slate-500">
          Click to select • Hover to highlight • Scroll to explore the tree
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
  const [selectedDetailIdeaId, setSelectedDetailIdeaId] = useState<string | null>(null);
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
          <TabsList className="grid w-full grid-cols-5 bg-white/80 backdrop-blur-sm">
            <TabsTrigger value="timeline" className="flex items-center gap-2">
              <Calendar className="h-4 w-4" /> Timeline
            </TabsTrigger>
            <TabsTrigger value="graph" className="flex items-center gap-2">
              <Network className="h-4 w-4" /> Lineage Graph
            </TabsTrigger>
            <TabsTrigger value="paths" className="flex items-center gap-2">
              <Route className="h-4 w-4" /> Paths
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
                              <Card 
                                onClick={() => setSelectedDetailIdeaId(idea.id)}
                                className={`${config.bgColor} border-2 hover:shadow-lg transition-all duration-300 cursor-pointer hover:border-violet-300`}
                              >
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
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleSummarize(idea.id);
                                          }}
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
              <LineageGraphView ideas={ideas} edges={edges} onNodeClick={(id) => setSelectedDetailIdeaId(id)} />
            </motion.div>
          </TabsContent>

          {/* ─── EVOLUTION PATHS TAB ─── */}
          <TabsContent value="paths" className="space-y-6">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
              <EvolutionPathFinder ideas={ideas} />
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
                            onClick={() => setSelectedDetailIdeaId(idea.id)}
                            className={`p-3 rounded-lg ${cfg.bgColor} border cursor-pointer hover:border-violet-300 hover:shadow-md transition-all`}
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
            <PredictionsDashboard ideas={ideas} edges={edges} llmConfigured={llmConfigured} />
          </TabsContent>
        </Tabs>
      </main>
      <IdeaDetailPanel
        ideaId={selectedDetailIdeaId}
        onClose={() => setSelectedDetailIdeaId(null)}
        allIdeas={ideas}
        onSelectSimilar={(id) => setSelectedDetailIdeaId(id)}
      />
    </div>
  );
};

/* ——————— Predictions Dashboard Component ——————— */

const PredictionsDashboard = ({ ideas, edges, llmConfigured }: { ideas: Idea[], edges: InfluenceEdge[], llmConfigured: boolean | null }) => {
  const [selectedIdeaId, setSelectedIdeaId] = useState<string | null>(null);
  const [prediction, setPrediction] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Future ideas prediction state
  const [futureIdeas, setFutureIdeas] = useState<any[]>([]);
  const [futureCategory, setFutureCategory] = useState<string>("Computer Science");
  const [futureLoading, setFutureLoading] = useState(false);
  const [futureError, setFutureError] = useState<string | null>(null);

  const selectedIdea = ideas.find(i => i.id === selectedIdeaId);

  // Calculate statistics
  const stats = useMemo(() => {
    if (!selectedIdea) return null;

    // 1. Stage distribution
    const stageDistribution = STAGE_ORDER.map(stage => ({
      stage: STAGE_LABELS[stage],
      count: ideas.filter(i => i.stage === stage).length,
      color: STAGE_COLORS[stage]
    }));

    // 2. Category distribution (top 6)
    const categoryCount: Record<string, number> = {};
    ideas.forEach(i => {
      categoryCount[i.category] = (categoryCount[i.category] || 0) + 1;
    });
    const categoryDistribution = Object.entries(categoryCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([category, count]) => ({ category, count }));

    // 3. Timeline distribution (by decade)
    const decades: Record<string, number> = {};
    ideas.forEach(i => {
      const decade = Math.floor(i.start_year / 10) * 10;
      decades[decade] = (decades[decade] || 0) + 1;
    });
    const timelineData = Object.entries(decades)
      .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
      .map(([decade, count]) => ({ decade: `${decade}s`, count }));

    // 4. Influence score distribution
    const influenceRanges = [
      { range: '0.0-0.2', min: 0, max: 0.2, count: 0 },
      { range: '0.2-0.4', min: 0.2, max: 0.4, count: 0 },
      { range: '0.4-0.6', min: 0.4, max: 0.6, count: 0 },
      { range: '0.6-0.8', min: 0.6, max: 0.8, count: 0 },
      { range: '0.8-1.0', min: 0.8, max: 1.0, count: 0 },
    ];
    ideas.forEach(i => {
      const range = influenceRanges.find(r => i.influence_score >= r.min && i.influence_score <= r.max);
      if (range) range.count++;
    });

    // 5. Connectivity analysis
    const connectivity = ideas.map(i => {
      const inDegree = edges.filter(e => e.target === i.id).length;
      const outDegree = edges.filter(e => e.source === i.id).length;
      return {
        id: i.id,
        title: i.title.substring(0, 20),
        inDegree,
        outDegree,
        total: inDegree + outDegree
      };
    }).sort((a, b) => b.total - a.total).slice(0, 10);

    // 6. Selected idea metrics
    const selectedInDegree = edges.filter(e => e.target === selectedIdea.id).length;
    const selectedOutDegree = edges.filter(e => e.source === selectedIdea.id).length;
    const selectedInfluenceRank = ideas
      .sort((a, b) => b.influence_score - a.influence_score)
      .findIndex(i => i.id === selectedIdea.id) + 1;

    return {
      stageDistribution,
      categoryDistribution,
      timelineData,
      influenceRanges,
      connectivity,
      selectedMetrics: {
        inDegree: selectedInDegree,
        outDegree: selectedOutDegree,
        totalConnections: selectedInDegree + selectedOutDegree,
        influenceRank: selectedInfluenceRank,
        totalIdeas: ideas.length
      }
    };
  }, [selectedIdea, ideas, edges]);

  const handlePredict = async () => {
    if (!selectedIdeaId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Get AI forecast from backend
      const response = await fetch(`http://localhost:5000/api/predictions/forecast/${selectedIdeaId}`);
      const data = await response.json();
      
      if (data.status === 'success') {
        setPrediction(data.data);
      } else {
        setError(data.message || 'Failed to get prediction');
      }
    } catch (err) {
      setError('Failed to connect to prediction service');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePredictFuture = async () => {
    setFutureLoading(true);
    setFutureError(null);
    
    try {
      const response = await fetch('http://localhost:5000/api/predictions/future-ideas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category: futureCategory, count: 5 })
      });
      const data = await response.json();
      
      if (data.status === 'success') {
        // Add source info to each prediction for display
        const predictionsWithSource = data.data.predictions.map((p: any) => ({
          ...p,
          source: data.data.source,
          model: data.data.model
        }));
        setFutureIdeas(predictionsWithSource);
        setFutureError(null);
      } else {
        // Check for specific error types
        const errorMsg = data.message || 'Failed to generate future predictions';
        
        if (errorMsg.includes('429') || errorMsg.includes('RESOURCE_EXHAUSTED') || errorMsg.includes('quota')) {
          setFutureError('⏳ API rate limit reached. Using high-quality rule-based predictions instead. (Resets in ~1 hour)');
        } else if (errorMsg.includes('503') || errorMsg.includes('high demand')) {
          setFutureError('⏳ Google Gemini API is experiencing high demand. Using rule-based predictions instead.');
        } else {
          setFutureError(errorMsg);
        }
      }
    } catch (err) {
      setFutureError('Failed to connect to prediction service. Make sure the backend is running.');
      console.error(err);
    } finally {
      setFutureLoading(false);
    }
  };

  // Get unique categories from ideas
  const categories = useMemo(() => {
    const cats = new Set(ideas.map(i => i.category));
    return Array.from(cats).sort();
  }, [ideas]);

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Future Ideas Prediction Section */}
      <Card className="bg-gradient-to-br from-cyan-50 to-blue-50 border-cyan-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-6 w-6 text-cyan-600" />
            Future Breakthrough Predictions
          </CardTitle>
          <CardDescription>
            AI-powered predictions for future breakthrough ideas in any field
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <Select value={futureCategory} onValueChange={setFutureCategory}>
                <SelectTrigger className="w-full bg-white">
                  <SelectValue placeholder="Select a category..." />
                </SelectTrigger>
                <SelectContent className="max-h-[300px]">
                  {categories.map(cat => (
                    <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <button
              onClick={handlePredictFuture}
              disabled={futureLoading || !llmConfigured}
              className="px-6 py-2 bg-cyan-600 text-white rounded-lg font-semibold hover:bg-cyan-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {futureLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Predict Future Ideas
                </>
              )}
            </button>
          </div>

          {!llmConfigured && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-700 text-sm">
              LLM service not configured. Set GEMINI_API_KEY to enable future predictions.
            </div>
          )}

          {futureError && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm flex items-start justify-between gap-3">
              <div className="flex-1">
                <div className="font-semibold mb-1">⚠️ Prediction Error</div>
                <div>{futureError}</div>
              </div>
              {futureError.includes('high demand') && (
                <button
                  onClick={handlePredictFuture}
                  className="px-3 py-1 bg-amber-600 text-white rounded text-xs font-semibold hover:bg-amber-700 transition-colors whitespace-nowrap"
                >
                  Try Again
                </button>
              )}
            </div>
          )}

          {futureIdeas.length > 0 && (
            <div className="space-y-3 mt-4">
              <div className="flex items-center justify-between">
                <div className="text-sm font-semibold text-cyan-900">
                  Predicted Future Breakthroughs in {futureCategory}:
                </div>
                {futureIdeas[0] && futureIdeas[0].source === 'fallback' && (
                  <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 text-xs">
                    <Brain className="h-3 w-3 mr-1" />
                    Rule-based predictions
                  </Badge>
                )}
              </div>
              <div className="grid gap-4">
                {futureIdeas.map((idea, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    className="p-4 bg-white rounded-xl shadow-sm border border-cyan-100 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Lightbulb className="h-5 w-5 text-cyan-600" />
                          <h3 className="font-bold text-lg text-cyan-900">{idea.title}</h3>
                        </div>
                        <p className="text-sm text-gray-700 mb-3">{idea.description}</p>
                        <div className="flex flex-wrap gap-2 mb-2">
                          <Badge variant="outline" className="bg-cyan-50 text-cyan-700 border-cyan-200">
                            <Calendar className="h-3 w-3 mr-1" />
                            {idea.timeframe}
                          </Badge>
                          {idea.confidence && (
                            <Badge variant="outline" className={`${
                              idea.confidence > 0.7 ? 'bg-green-50 text-green-700 border-green-200' :
                              idea.confidence > 0.5 ? 'bg-amber-50 text-amber-700 border-amber-200' :
                              'bg-gray-50 text-gray-700 border-gray-200'
                            }`}>
                              {(idea.confidence * 100).toFixed(0)}% confidence
                            </Badge>
                          )}
                        </div>
                        {idea.prerequisites && idea.prerequisites.length > 0 && (
                          <div className="mt-2">
                            <div className="text-xs text-gray-500 mb-1">Prerequisites:</div>
                            <div className="flex flex-wrap gap-1">
                              {idea.prerequisites.map((prereq: string, i: number) => (
                                <span key={i} className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded">
                                  {prereq}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Existing Idea Evolution Prediction Section */}
      <Card className="bg-gradient-to-br from-violet-50 to-blue-50 border-violet-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-6 w-6 text-violet-600" />
            Existing Idea Evolution Prediction
          </CardTitle>
          <CardDescription>
            Select an existing idea to predict its next evolution stage
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <Select value={selectedIdeaId || ""} onValueChange={setSelectedIdeaId}>
                <SelectTrigger className="w-full bg-white">
                  <SelectValue placeholder="Select an idea to analyze..." />
                </SelectTrigger>
                <SelectContent className="max-h-[300px]">
                  {ideas.map(idea => (
                    <SelectItem key={idea.id} value={idea.id}>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{idea.title}</span>
                        <span className="text-xs text-muted-foreground">({idea.start_year})</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <button
              onClick={handlePredict}
              disabled={!selectedIdeaId || loading}
              className="px-6 py-2 bg-violet-600 text-white rounded-lg font-semibold hover:bg-violet-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Wand2 className="h-4 w-4" />
                  Get AI Prediction
                </>
              )}
            </button>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {selectedIdea && (
        <>
          {/* Selected Idea Overview */}
          <Card className="bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="h-5 w-5 text-amber-500" />
                {selectedIdea.title}
              </CardTitle>
              <CardDescription>
                {selectedIdea.category} • {selectedIdea.start_year} • {STAGE_LABELS[selectedIdea.stage]}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">{selectedIdea.description}</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 bg-violet-50 rounded-lg">
                  <div className="text-xs text-muted-foreground">Influence Score</div>
                  <div className="text-2xl font-bold text-violet-600">{(selectedIdea.influence_score * 100).toFixed(0)}%</div>
                </div>
                {stats && (
                  <>
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <div className="text-xs text-muted-foreground">Connections</div>
                      <div className="text-2xl font-bold text-blue-600">{stats.selectedMetrics.totalConnections}</div>
                    </div>
                    <div className="p-3 bg-green-50 rounded-lg">
                      <div className="text-xs text-muted-foreground">Influence Rank</div>
                      <div className="text-2xl font-bold text-green-600">#{stats.selectedMetrics.influenceRank}</div>
                    </div>
                    <div className="p-3 bg-orange-50 rounded-lg">
                      <div className="text-xs text-muted-foreground">Descendants</div>
                      <div className="text-2xl font-bold text-orange-600">{stats.selectedMetrics.outDegree}</div>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          {/* AI Prediction Results */}
          {prediction && (
            <Card className="bg-gradient-to-br from-violet-50 via-purple-50 to-blue-50 border-violet-300">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5 text-violet-600" />
                  AI Prediction Results
                </CardTitle>
                <CardDescription>
                  Machine learning analysis of evolution trajectory
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="p-4 bg-white rounded-xl shadow-sm">
                    <div className="text-sm text-muted-foreground mb-1">Current Stage</div>
                    <div className="text-lg font-bold" style={{ color: STAGE_COLORS[prediction.current_stage] }}>
                      {STAGE_LABELS[prediction.current_stage]}
                    </div>
                  </div>
                  <div className="p-4 bg-white rounded-xl shadow-sm">
                    <div className="text-sm text-muted-foreground mb-1">Predicted Next Stage</div>
                    <div className="text-lg font-bold" style={{ color: STAGE_COLORS[prediction.predicted_next_stage] }}>
                      {STAGE_LABELS[prediction.predicted_next_stage]}
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-white rounded-xl shadow-sm">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium">Confidence Score</span>
                    <span className={`text-lg font-bold ${prediction.confidence > 0.7 ? 'text-green-600' : prediction.confidence > 0.5 ? 'text-amber-600' : 'text-red-500'}`}>
                      {(prediction.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="bg-gray-200 rounded-full h-3">
                    <motion.div
                      className={`h-3 rounded-full ${prediction.confidence > 0.7 ? 'bg-green-500' : prediction.confidence > 0.5 ? 'bg-amber-500' : 'bg-red-400'}`}
                      initial={{ width: 0 }}
                      animate={{ width: `${prediction.confidence * 100}%` }}
                      transition={{ duration: 1 }}
                    />
                  </div>
                </div>

                {prediction.explanation && (
                  <div className="p-4 bg-white rounded-xl shadow-sm space-y-3">
                    <div className="font-semibold text-sm">Analysis Factors:</div>
                    <div className="grid md:grid-cols-3 gap-3">
                      <div>
                        <div className="text-xs text-muted-foreground">Age</div>
                        <div className="text-sm font-medium">{prediction.explanation.age} years</div>
                      </div>
                      <div>
                        <div className="text-xs text-muted-foreground">Connectivity</div>
                        <div className="text-sm font-medium">{(prediction.explanation.connectivity * 100).toFixed(1)}%</div>
                      </div>
                      <div>
                        <div className="text-xs text-muted-foreground">Tech Similarity</div>
                        <div className="text-sm font-medium">{(prediction.explanation.similarity_score * 100).toFixed(1)}%</div>
                      </div>
                    </div>
                    <div className="pt-3 border-t">
                      <div className="text-xs text-muted-foreground mb-1">Reasoning:</div>
                      <div className="text-sm">{prediction.explanation.reason || prediction.reason}</div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Statistical Graphs */}
          {stats && (
            <div className="grid md:grid-cols-2 gap-6">
              {/* Evolution Stage Distribution - Donut with Breakdown */}
              <Card className="bg-white/80 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-base flex items-center justify-between">
                    Evolution Stage Distribution
                    <span className="text-xs text-muted-foreground font-normal">ⓘ</span>
                  </CardTitle>
                  <CardDescription>Ideas across different stages</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-6">
                    <div className="relative w-40 h-40 flex-shrink-0">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={stats.stageDistribution}
                            dataKey="count"
                            nameKey="stage"
                            cx="50%"
                            cy="50%"
                            innerRadius={50}
                            outerRadius={70}
                            paddingAngle={0}
                          >
                            {stats.stageDistribution.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                        <span className="text-3xl font-bold text-gray-900">{ideas.length}</span>
                        <small className="text-xs text-gray-500 mt-1">Total Ideas</small>
                      </div>
                    </div>
                    <div className="flex-1 space-y-3">
                      {stats.stageDistribution.map((stage, idx) => (
                        <div key={idx}>
                          <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: stage.color }}></div>
                            <span className="flex-1">{stage.stage}</span>
                            <span className="text-gray-900 font-semibold">{stage.count}</span>
                            <span className="text-gray-500 text-xs">({((stage.count / ideas.length) * 100).toFixed(0)}%)</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Category Distribution - Donut with Legend */}
              <Card className="bg-white/80 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-base flex items-center justify-between">
                    Top Categories
                    <span className="text-xs text-muted-foreground font-normal">ⓘ</span>
                  </CardTitle>
                  <CardDescription>Most represented fields</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-6">
                    <div className="relative w-40 h-40 flex-shrink-0">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={stats.categoryDistribution}
                            dataKey="count"
                            nameKey="category"
                            cx="50%"
                            cy="50%"
                            innerRadius={50}
                            outerRadius={70}
                            paddingAngle={0}
                          >
                            {stats.categoryDistribution.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#ec4899'][index % 6]} />
                            ))}
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                        <span className="text-2xl font-bold text-gray-900">{stats.categoryDistribution.reduce((a, b) => a + b.count, 0)}</span>
                        <small className="text-xs text-gray-500 mt-1">Total</small>
                      </div>
                    </div>
                    <div className="flex-1 space-y-2.5">
                      {stats.categoryDistribution.slice(0, 4).map((cat, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-sm">
                          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b'][idx] }}></div>
                          <span className="flex-1 font-medium text-gray-700 truncate">{cat.category}</span>
                          <span className="text-gray-900 font-semibold">{cat.count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Influence Score Distribution - Pie Chart */}
              <Card className="bg-white/80 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-base flex items-center justify-between">
                    Influence Score Distribution
                    <span className="text-xs text-muted-foreground font-normal">ⓘ</span>
                  </CardTitle>
                  <CardDescription>Score ranges across dataset</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-6">
                    <div className="relative w-40 h-40 flex-shrink-0">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={stats.influenceRanges.filter(r => r.count > 0)}
                            dataKey="count"
                            nameKey="range"
                            cx="50%"
                            cy="50%"
                            outerRadius={70}
                            paddingAngle={2}
                          >
                            {stats.influenceRanges.filter(r => r.count > 0).map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={['#22c55e', '#84cc16', '#eab308', '#f97316', '#ef4444'][index % 5]} />
                            ))}
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="flex-1 space-y-2">
                      {stats.influenceRanges.filter(r => r.count > 0).map((range, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-sm">
                          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: ['#22c55e', '#84cc16', '#eab308', '#f97316', '#ef4444'][idx] }}></div>
                          <span className="flex-1 font-medium text-gray-700">{range.range}</span>
                          <span className="text-gray-900 font-semibold">{range.count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Timeline Distribution - Area Chart */}
              <Card className="bg-white/80 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-base flex items-center justify-between">
                    Timeline Distribution
                    <span className="text-xs text-muted-foreground font-normal">ⓘ</span>
                  </CardTitle>
                  <CardDescription>Ideas by decade</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-48">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={stats.timelineData}>
                        <defs>
                          <linearGradient id="colorTimeline" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.1}/>
                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f3f5" vertical={false} />
                        <XAxis dataKey="decade" tick={{ fontSize: 11 }} stroke="#9ca3af" />
                        <YAxis tick={{ fontSize: 11 }} stroke="#9ca3af" />
                        <Tooltip />
                        <Area type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorTimeline)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Connectivity Analysis - Horizontal Bars */}
              <Card className="bg-white/80 backdrop-blur-sm md:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base flex items-center justify-between">
                    Top 10 Most Connected Ideas
                    <span className="text-xs text-muted-foreground font-normal">ⓘ</span>
                  </CardTitle>
                  <CardDescription>Ideas with highest number of relationships</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {stats.connectivity.slice(0, 8).map((item, idx) => (
                      <div key={idx} className="space-y-1.5">
                        <div className="flex items-center justify-between text-sm">
                          <span className="font-medium text-gray-700 truncate flex-1">{item.title}</span>
                          <span className="text-gray-900 font-semibold ml-2">{item.total}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <div className="flex-1 bg-gray-200 h-2 rounded-full overflow-hidden">
                            <div className="flex h-full">
                              <div 
                                className="bg-gradient-to-r from-orange-400 to-orange-500 h-full" 
                                style={{ width: `${(item.inDegree / item.total) * 100}%` }}
                              ></div>
                              <div 
                                className="bg-gradient-to-r from-blue-400 to-blue-500 h-full" 
                                style={{ width: `${(item.outDegree / item.total) * 100}%` }}
                              ></div>
                            </div>
                          </div>
                          <span className="text-xs text-gray-500 w-16 text-right">
                            {item.inDegree}↓ {item.outDegree}↑
                          </span>
                        </div>
                      </div>
                    ))}
                    <div className="flex items-center gap-4 pt-2 text-xs text-gray-600">
                      <div className="flex items-center gap-1.5">
                        <div className="w-2.5 h-2.5 rounded-full bg-orange-500"></div>
                        <span>Incoming</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <div className="w-2.5 h-2.5 rounded-full bg-blue-500"></div>
                        <span>Outgoing</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Selected Idea Influence Trend - Area Chart */}
              {selectedIdea && (
                <Card className="bg-white/80 backdrop-blur-sm md:col-span-2">
                  <CardHeader>
                    <CardTitle className="text-base flex items-center justify-between">
                      Influence Metrics for "{selectedIdea.title}"
                      <span className="text-xs text-muted-foreground font-normal">ⓘ</span>
                    </CardTitle>
                    <CardDescription>Comparative analysis across key metrics</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-56">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={[
                          { metric: 'Influence', value: selectedIdea.influence_score * 100, max: 100 },
                          { metric: 'Connections', value: (stats.selectedMetrics.totalConnections / Math.max(...stats.connectivity.map(c => c.total))) * 100, max: 100 },
                          { metric: 'Rank', value: ((stats.selectedMetrics.totalIdeas - stats.selectedMetrics.influenceRank) / stats.selectedMetrics.totalIdeas) * 100, max: 100 },
                          { metric: 'Descendants', value: (stats.selectedMetrics.outDegree / Math.max(...stats.connectivity.map(c => c.outDegree))) * 100, max: 100 }
                        ]}>
                          <defs>
                            <linearGradient id="colorInfluence" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#fa896b" stopOpacity={0.15}/>
                              <stop offset="95%" stopColor="#fa896b" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f1f3f5" vertical={false} />
                          <XAxis dataKey="metric" tick={{ fontSize: 11 }} stroke="#9ca3af" />
                          <YAxis tick={{ fontSize: 11 }} stroke="#9ca3af" domain={[0, 100]} />
                          <Tooltip formatter={(value: any) => `${value.toFixed(1)}%`} />
                          <Area type="monotone" dataKey="value" stroke="#fa896b" strokeWidth={2} fillOpacity={1} fill="url(#colorInfluence)" />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </>
      )}

      {!selectedIdea && (
        <Card className="bg-white/80 backdrop-blur-sm">
          <CardContent className="py-12">
            <div className="text-center text-muted-foreground">
              <Sparkles className="h-12 w-12 mx-auto mb-4 text-violet-300" />
              <p className="text-lg font-medium">Select an idea to begin analysis</p>
              <p className="text-sm mt-2">Choose an idea from the dropdown above to see AI predictions and statistical insights</p>
            </div>
          </CardContent>
        </Card>
      )}
    </motion.div>
  );
};

export default EvolutionTracker;
