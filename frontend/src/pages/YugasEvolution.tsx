import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Download, Sparkles, Loader2, RefreshCw, Database,
  Globe, Github, Plus, Eye, Calendar, TrendingUp, Search, X,
  Filter, BarChart3, Network, Clock, Zap, History, LogOut, User as UserIcon
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
// @ts-ignore
import html2pdf from "html2pdf.js";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Slider } from "@/components/ui/slider";
import { authFetch } from "../lib/api";
import YugasChatPanel from "@/components/YugasChatPanel";
import IdeaChatPanel from "@/components/IdeaChatPanel";

interface YugaEvolution {
  description: string;
  statistics: string;
  characteristics: string;
  impact: string;
  time_period?: string;
  key_insight?: string;
  paragraphs?: { label: string; text: string }[];
  characteristics_list?: string[];
  statistics_detailed?: {
    original: string;
    metrics: { label: string; value: string; icon: string }[];
  };
}

interface YugaIdea {
  _id?: string;
  idea: string;
  description: string;
  source: string;
  images?: string[];
  evolution: {
    satya_yuga: YugaEvolution;
    treta_yuga: YugaEvolution;
    dwapar_yuga: YugaEvolution;
    kali_yuga: YugaEvolution;
  };
  timestamp: string;
}

const YugasEvolution = () => {
  const [ideas, setIdeas] = useState<YugaIdea[]>([]);
  const [filteredIdeas, setFilteredIdeas] = useState<YugaIdea[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [searching, setSearching] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [selectedIdea, setSelectedIdea] = useState<YugaIdea | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchType, setSearchType] = useState<string>("");

  // Data structure filters
  const [timeFilterStart, setTimeFilterStart] = useState(-10000);
  const [timeFilterEnd, setTimeFilterEnd] = useState(2100);
  const [complexityMin, setComplexityMin] = useState(0);
  const [complexityMax, setComplexityMax] = useState(100);
  const [selectedEvolutionChain, setSelectedEvolutionChain] = useState<any>(null);
  const [filterActive, setFilterActive] = useState(false);

  // Dashboard data
  const [dashboardData, setDashboardData] = useState<any>(null);

  // Images for selected idea
  const [ideaImages, setIdeaImages] = useState<string[]>([]);
  const [loadingImages, setLoadingImages] = useState(false);

  // Form state
  const [newIdeaName, setNewIdeaName] = useState("");
  const [newIdeaDesc, setNewIdeaDesc] = useState("");
  const [fetchSource, setFetchSource] = useState("wikipedia");
  const [fetchLimit, setFetchLimit] = useState(5);

  // User Profile & History state
  const [user, setUser] = useState<{ id: string; username: string } | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [searchHistory, setSearchHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    const u = localStorage.getItem("user");
    if (u) {
      try {
        setUser(JSON.parse(u));
      } catch (e) {
        console.error(e);
      }
    }
  }, []);

  const loadSearchHistory = async () => {
    setLoadingHistory(true);
    try {
      const res = await authFetch("/api/user/search-history");
      const data = await res.json();
      if (data.status === "success") {
        setSearchHistory(data.data || []);
      }
    } catch (error) {
      console.error("Error loading search history:", error);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    if (historyOpen) {
      loadSearchHistory();
    }
  }, [historyOpen]);

  const handleLogout = async () => {
    try {
      await authFetch("/api/auth/logout", { method: "POST" });
    } catch (e) {
      console.error(e);
    } finally {
      localStorage.removeItem("session_token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
  };

  const handleHistoryItemClick = async (query: string) => {
    setSearchQuery(query);
    setHistoryOpen(false);
    setSearching(true);
    try {
      const res = await authFetch("/api/yugas/search", {
        method: "POST",
        body: JSON.stringify({ query, limit: 20 })
      });
      const data = await res.json();
      if (data.status === "success") {
        setFilteredIdeas(data.data.ideas || []);
        setSearchType(data.data.search_type || "");
      }
    } catch (error) {
      console.error("Error searching from history:", error);
    } finally {
      setSearching(false);
    }
  };

  // Load ideas and stats on mount (dashboard data loads lazily when needed)
  useEffect(() => {
    loadIdeas();
    loadStats();
  }, []);

  // Update filtered ideas when ideas change
  useEffect(() => {
    setFilteredIdeas(ideas);
  }, [ideas]);

  const loadIdeas = async () => {
    setLoading(true);
    try {
      const res = await authFetch("/api/yugas/ideas?limit=200");
      const data = await res.json();
      if (data.status === "success") {
        setIdeas(data.data.ideas || []);
        setFilteredIdeas(data.data.ideas || []);
        setSearchQuery("");
        setSearchType("");
        setFilterActive(false);
      }
    } catch (error) {
      console.error("Error loading ideas:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const res = await authFetch("/api/yugas/stats");
      const data = await res.json();
      if (data.status === "success") {
        setStats(data.data);
      }
    } catch (error) {
      console.error("Error loading stats:", error);
    }
  };

  const loadDashboardData = async () => {
    try {
      const res = await authFetch("/api/yugas/data-structures/stats");
      const data = await res.json();
      if (data.status === "success") {
        setDashboardData(data.data);
      }
    } catch (error) {
      console.error("Error loading dashboard data:", error);
    }
  };

  const filterByTimePeriod = async () => {
    setLoading(true);
    setFilterActive(true);
    try {
      const res = await authFetch("/api/yugas/query/time-period", {
        method: "POST",
        body: JSON.stringify({
          start_year: timeFilterStart,
          end_year: timeFilterEnd
        })
      });

      const data = await res.json();
      if (data.status === "success") {
        setFilteredIdeas(data.data.ideas || []);
      }
    } catch (error) {
      console.error("Error filtering by time:", error);
    } finally {
      setLoading(false);
    }
  };

  const filterByComplexity = async () => {
    setLoading(true);
    setFilterActive(true);
    try {
      const res = await authFetch("/api/yugas/query/complexity", {
        method: "POST",
        body: JSON.stringify({
          min_score: complexityMin,
          max_score: complexityMax,
          yuga: "kali_yuga"
        })
      });

      const data = await res.json();
      if (data.status === "success") {
        const ideasOnly = data.data.ideas.map((item: any) => item.idea);
        setFilteredIdeas(ideasOnly || []);
      }
    } catch (error) {
      console.error("Error filtering by complexity:", error);
    } finally {
      setLoading(false);
    }
  };

  const viewEvolutionChain = async (ideaName: string) => {
    try {
      const res = await authFetch(`/api/yugas/evolution-chain/${encodeURIComponent(ideaName)}`);
      const data = await res.json();
      if (data.status === "success") {
        setSelectedEvolutionChain(data.data);
      }
    } catch (error) {
      console.error("Error loading evolution chain:", error);
    }
  };

  const clearFilters = () => {
    setFilteredIdeas(ideas);
    setFilterActive(false);
    setTimeFilterStart(-10000);
    setTimeFilterEnd(2100);
    setComplexityMin(0);
    setComplexityMax(100);
  };

  const generateSingleIdea = async () => {
    if (!newIdeaName.trim()) return;

    setGenerating(true);
    try {
      const res = await authFetch("/api/yugas/generate", {
        method: "POST",
        body: JSON.stringify({
          idea: newIdeaName,
          description: newIdeaDesc,
          source: "Manual"
        })
      });

      const data = await res.json();
      if (data.status === "success") {
        setNewIdeaName("");
        setNewIdeaDesc("");
        await loadIdeas();
        await loadStats();
      }
    } catch (error) {
      console.error("Error generating idea:", error);
    } finally {
      setGenerating(false);
    }
  };

  const fetchAndGenerate = async () => {
    setFetching(true);
    try {
      const res = await authFetch("/api/yugas/fetch-and-generate", {
        method: "POST",
        body: JSON.stringify({
          source: fetchSource,
          limit: fetchLimit
        })
      });

      const data = await res.json();
      if (data.status === "success") {
        await loadIdeas();
        await loadStats();
      }
    } catch (error) {
      console.error("Error fetching ideas:", error);
    } finally {
      setFetching(false);
    }
  };

  const exportCSV = async () => {
    try {
      const res = await authFetch("/api/yugas/export-csv");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'yuga_evolution_export.csv';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error exporting CSV:", error);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setFilteredIdeas(ideas);
      setSearchType("");
      return;
    }

    setSearching(true);
    try {
      const res = await authFetch("/api/yugas/search", {
        method: "POST",
        body: JSON.stringify({
          query: searchQuery,
          limit: 20
        })
      });

      const data = await res.json();
      if (data.status === "success") {
        setFilteredIdeas(data.data.ideas || []);
        setSearchType(data.data.search_type || "");
      }
    } catch (error) {
      console.error("Error searching:", error);
    } finally {
      setSearching(false);
    }
  };

  const clearSearch = () => {
    setSearchQuery("");
    setFilteredIdeas(ideas);
    setSearchType("");
  };

  const openIdeaDetail = async (idea: YugaIdea) => {
    setSelectedIdea(idea);
    setLoadingImages(true);
    setIdeaImages([]);
    try {
      const res = await authFetch(
        `/api/yugas/images/${encodeURIComponent(idea.idea)}`
      );
      const data = await res.json();
      if (data.status === "success" && data.data?.images) {
        setIdeaImages(data.data.images);
      }
    } catch (error) {
      console.error("Error fetching images:", error);
    } finally {
      setLoadingImages(false);
    }
  };

  const downloadPDFReport = async () => {
    if (!selectedIdea) return;
    const element = document.getElementById("yugas-report-printable");
    if (!element) return;

    // Clone the element to avoid mutating the original
    const clone = element.cloneNode(true) as HTMLDivElement;
    
    // Style the clone so it is visible to html2canvas, laid out correctly on the body,
    // but positioned off-screen / overlayed properly
    clone.style.position = "fixed";
    clone.style.left = "0";
    clone.style.top = "0";
    clone.style.width = "800px";
    clone.style.zIndex = "99999";
    clone.style.opacity = "1";
    clone.style.backgroundColor = "#ffffff";
    clone.style.visibility = "visible";
    clone.style.display = "block";

    document.body.appendChild(clone);

    // Wait for all images in the clone to load (especially CORS wikipedia images)
    const images = Array.from(clone.getElementsByTagName("img"));
    const imageLoadPromises = images.map((img) => {
      if (img.complete) return Promise.resolve();
      return new Promise((resolve) => {
        img.onload = resolve;
        img.onerror = resolve;
      });
    });

    // Wait a short moment to ensure styling is applied and images are loaded
    await Promise.all([
      ...imageLoadPromises,
      new Promise((resolve) => setTimeout(resolve, 500))
    ]);

    const opt = {
      margin:       [10, 10, 10, 10],
      filename:     `${selectedIdea.idea.replace(/\s+/g, '_')}_yugas_report.pdf`,
      image:        { type: 'jpeg', quality: 0.98 },
      html2canvas:  { 
        scale: 2, 
        useCORS: true, 
        logging: true, // Enable logging temporarily to help debug if needed
        scrollY: 0, 
        windowWidth: 800,
        backgroundColor: '#ffffff'
      },
      jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' },
      pagebreak:    { mode: ['avoid-all', 'css', 'legacy'] }
    };

    try {
      // @ts-ignore
      await html2pdf().set(opt).from(clone).save();
    } catch (err) {
      console.error("PDF generation error:", err);
    } finally {
      // Clean up the clone
      if (clone.parentNode) {
        clone.parentNode.removeChild(clone);
      }
    }
  };

  const yugaColors = {
    satya_yuga: "from-yellow-400 to-amber-500",
    treta_yuga: "from-blue-400 to-cyan-500",
    dwapar_yuga: "from-orange-400 to-red-500",
    kali_yuga: "from-purple-400 to-pink-500"
  };

  const yugaLabels = {
    satya_yuga: "Satya Yuga (Golden Age)",
    treta_yuga: "Treta Yuga (Silver Age)",
    dwapar_yuga: "Dwapar Yuga (Bronze Age)",
    kali_yuga: "Kali Yuga (Iron Age)"
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50 p-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center shadow-lg">
              <Sparkles className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Yugas Evolution</h1>
              <p className="text-gray-600 text-sm">Map modern ideas to their cosmic evolution across the four Yugas</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* User Profile Bar */}
            <div className="flex items-center gap-3 bg-white/70 backdrop-blur-xl border border-orange-200/40 px-4 py-2 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-amber-500 to-orange-500 flex items-center justify-center text-white font-bold text-sm uppercase shadow-sm">
                {user?.username?.charAt(0) || "U"}
              </div>
              <div className="hidden sm:block text-left">
                <div className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Explorer Portal</div>
                <div className="text-xs font-bold text-slate-800">{user?.username || "Explorer"}</div>
              </div>
              <div className="h-6 w-[1px] bg-slate-200/85 mx-1" />
              
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={() => setHistoryOpen(true)} 
                className="h-8 w-8 hover:bg-amber-100/50 rounded-xl relative text-slate-600 hover:text-orange-600 transition-colors"
                title="Search History"
              >
                <History className="h-4 w-4" />
              </Button>
              
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={handleLogout} 
                className="h-8 w-8 hover:bg-red-50 text-slate-600 hover:text-red-500 rounded-xl transition-colors"
                title="Logout"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>

            <Button onClick={() => window.location.href = '/'} variant="outline" className="gap-2 rounded-xl">
              <TrendingUp className="h-4 w-4" />
              Back to Modern Ideas
            </Button>
            <Button onClick={exportCSV} variant="outline" className="gap-2 rounded-xl">
              <Download className="h-4 w-4" />
              Export CSV
            </Button>
          </div>
        </div>


      </motion.div>

      {/* Search History Side Drawer */}
      <AnimatePresence>
        {historyOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.4 }}
              exit={{ opacity: 0 }}
              onClick={() => setHistoryOpen(false)}
              className="fixed inset-0 bg-black/40 z-[100] cursor-pointer"
            />
            {/* Drawer */}
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed top-0 right-0 bottom-0 w-full sm:w-[400px] bg-white/90 backdrop-blur-2xl border-l border-orange-100 shadow-2xl z-[110] flex flex-col h-full font-sans text-slate-800"
            >
              {/* Top Header */}
              <div className="p-6 border-b border-orange-50 flex items-center justify-between bg-gradient-to-r from-amber-50/20 to-orange-50/20">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-md">
                    <History className="h-4 w-4 text-white" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-900">Search History</h2>
                    <p className="text-xs text-slate-400">Your recent cosmic queries</p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setHistoryOpen(false)}
                  className="h-8 w-8 hover:bg-slate-100 rounded-full"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {loadingHistory ? (
                  <div className="h-48 flex items-center justify-center text-xs text-slate-400 gap-2">
                    <Loader2 className="h-4 w-4 animate-spin text-orange-600" />
                    Scanning stellar logs...
                  </div>
                ) : searchHistory.length === 0 ? (
                  <div className="h-48 flex flex-col items-center justify-center text-center p-4">
                    <Search className="h-8 w-8 text-slate-300 mb-2" />
                    <p className="text-xs font-semibold text-slate-500">No searches recorded</p>
                    <p className="text-[10px] text-slate-400 mt-1 max-w-[200px]">Use the portal search tools to record search events</p>
                  </div>
                ) : (
                  <div className="space-y-2.5">
                    {searchHistory.map((item) => (
                      <motion.div
                        key={item.id}
                        whileHover={{ scale: 1.01, x: 2 }}
                        onClick={() => handleHistoryItemClick(item.query)}
                        className="p-3.5 bg-amber-50/20 hover:bg-orange-50/40 border border-amber-100/40 hover:border-orange-200/50 rounded-xl cursor-pointer transition-all duration-200 group flex items-start justify-between gap-3 text-left"
                      >
                        <div className="space-y-1 flex-1 min-w-0">
                          <p className="text-xs font-bold text-slate-800 break-words group-hover:text-orange-700 transition-colors">
                            {item.query}
                          </p>
                          <div className="flex items-center gap-2">
                            <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-orange-100/60 text-orange-700 uppercase tracking-wider">
                              {item.search_type}
                            </span>
                            <span className="text-[9px] text-slate-400">
                              {item.results_count} results
                            </span>
                          </div>
                        </div>
                        <span className="text-[9px] text-slate-400 mt-0.5 whitespace-nowrap">
                          {new Date(item.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                        </span>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
              
              {/* Footer */}
              <div className="p-4 border-t border-orange-50 bg-amber-50/10 text-center">
                <p className="text-[9px] text-slate-400">
                  Absolute privacy. Searches are strictly segmented under your session.
                </p>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel - Controls & Filters */}
        <div className="lg:col-span-1 space-y-5">

          {/* ═══ Cosmic Era Filter ═══ */}
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}>
            <Card className="overflow-hidden border-0 shadow-xl bg-white/70 backdrop-blur-xl">
              {/* Gradient header strip */}
              <div className="h-1.5 bg-gradient-to-r from-blue-500 via-purple-500 to-orange-500" />
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center shadow-md">
                    <Filter className="h-4 w-4 text-white" />
                  </div>
                  <div>
                    <span className="text-base">Cosmic Era Filter</span>
                    <p className="text-xs font-normal text-muted-foreground mt-0.5">Query concepts by timeline emergence</p>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-5 pt-0">

                {/* ── Chronological Span ── */}
                <div className="rounded-xl border border-blue-100 bg-gradient-to-br from-blue-50/80 to-sky-50/60 p-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center">
                        <Clock className="h-3.5 w-3.5 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-blue-900">Chronological Span</p>
                        <p className="text-[10px] text-blue-500/80 font-medium">Cosmic emergence period</p>
                      </div>
                    </div>
                  </div>

                  {/* Year range display */}
                  <div className="grid grid-cols-2 gap-2">
                    <div className="p-2.5 bg-white/80 rounded-lg border border-blue-100 text-center">
                      <div className="text-[10px] text-blue-400 uppercase tracking-wider font-medium">From</div>
                      <div className="text-sm font-bold text-blue-800 mt-0.5">
                        {Math.abs(timeFilterStart).toLocaleString()} {timeFilterStart < 0 ? 'BCE' : 'CE'}
                      </div>
                    </div>
                    <div className="p-2.5 bg-white/80 rounded-lg border border-blue-100 text-center">
                      <div className="text-[10px] text-blue-400 uppercase tracking-wider font-medium">To</div>
                      <div className="text-sm font-bold text-blue-800 mt-0.5">
                        {Math.abs(timeFilterEnd).toLocaleString()} {timeFilterEnd < 0 ? 'BCE' : 'CE'}
                      </div>
                    </div>
                  </div>

                  {/* Slider controls */}
                  <div className="space-y-1.5 pt-2">
                    <Slider
                      min={-10000}
                      max={2100}
                      step={500}
                      value={[timeFilterStart, timeFilterEnd]}
                      onValueChange={(values) => {
                        setTimeFilterStart(values[0]);
                        setTimeFilterEnd(values[1]);
                      }}
                      className="w-full"
                    />
                    <div className="flex justify-between text-[10px] text-blue-400">
                      <span>10,000 BCE</span>
                      <span>Present</span>
                      <span>2100 CE</span>
                    </div>
                  </div>

                  <button
                    onClick={filterByTimePeriod}
                    className="w-full py-2 rounded-lg bg-gradient-to-r from-blue-500 to-sky-500 text-white text-sm font-semibold flex items-center justify-center gap-2 hover:from-blue-600 hover:to-sky-600 hover:shadow-md transition-all active:scale-[0.98]"
                  >
                    <Clock className="h-3.5 w-3.5" />
                    Apply Era Filter
                  </button>
                </div>

                {/* Clear Filters */}
                {filterActive && (
                  <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                    <button
                      onClick={clearFilters}
                      className="w-full py-2.5 rounded-lg bg-gradient-to-r from-red-500 to-rose-500 text-white text-sm font-semibold flex items-center justify-center gap-2 hover:from-red-600 hover:to-rose-600 hover:shadow-md transition-all active:scale-[0.98]"
                    >
                      <X className="h-4 w-4" />
                      Clear Era Filter
                    </button>
                  </motion.div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* ═══ Generate Evolution ═══ */}
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
            <Card className="overflow-hidden border-0 shadow-xl bg-white/70 backdrop-blur-xl">
              <div className="h-1.5 bg-gradient-to-r from-purple-500 via-violet-500 to-blue-500" />
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-md">
                    <Sparkles className="h-4 w-4 text-white" />
                  </div>
                  <div>
                    <span className="text-base">Generate Evolution</span>
                    <p className="text-xs font-normal text-muted-foreground mt-0.5">AI-powered Yuga mapping</p>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 pt-0">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-600 uppercase tracking-wider">Idea Name *</label>
                  <Input
                    placeholder="e.g., Pressure Cooker, Telescope..."
                    value={newIdeaName}
                    onChange={(e) => setNewIdeaName(e.target.value)}
                    className="bg-white/80 border-purple-100 focus:border-purple-400 focus:ring-purple-400/20"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-600 uppercase tracking-wider">Description <span className="font-normal normal-case text-gray-400">(optional)</span></label>
                  <Textarea
                    placeholder="Brief description to guide the AI..."
                    value={newIdeaDesc}
                    onChange={(e) => setNewIdeaDesc(e.target.value)}
                    rows={3}
                    className="bg-white/80 border-purple-100 focus:border-purple-400 focus:ring-purple-400/20 resize-none"
                  />
                </div>

                <button
                  onClick={generateSingleIdea}
                  disabled={generating || !newIdeaName.trim()}
                  className={`w-full py-2.5 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 transition-all active:scale-[0.98] ${
                    generating
                      ? "bg-purple-300 text-white cursor-wait"
                      : !newIdeaName.trim()
                        ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                        : "bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:from-violet-700 hover:to-purple-700 hover:shadow-lg shadow-purple-200"
                  }`}
                >
                  {generating ? (
                    <><Loader2 className="h-4 w-4 animate-spin" /> Mapping across Yugas...</>
                  ) : (
                    <><Sparkles className="h-4 w-4" /> Generate Evolution</>
                  )}
                </button>
              </CardContent>
            </Card>
          </motion.div>

          {/* ═══ Auto-Fetch Ideas ═══ */}
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}>
            <Card className="overflow-hidden border-0 shadow-xl bg-white/70 backdrop-blur-xl">
              <div className="h-1.5 bg-gradient-to-r from-teal-500 via-emerald-500 to-green-500" />
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-teal-500 to-emerald-600 flex items-center justify-center shadow-md">
                    <Database className="h-4 w-4 text-white" />
                  </div>
                  <div>
                    <span className="text-base">Auto-Fetch Ideas</span>
                    <p className="text-xs font-normal text-muted-foreground mt-0.5">Import from online sources</p>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 pt-0">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-600 uppercase tracking-wider">Source</label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => setFetchSource("wikipedia")}
                      className={`p-3 rounded-xl border-2 flex flex-col items-center gap-1.5 transition-all ${
                        fetchSource === "wikipedia"
                          ? "border-teal-400 bg-teal-50 shadow-sm"
                          : "border-gray-100 bg-white/60 hover:border-teal-200"
                      }`}
                    >
                      <Globe className={`h-5 w-5 ${fetchSource === "wikipedia" ? "text-teal-600" : "text-gray-400"}`} />
                      <span className={`text-xs font-semibold ${fetchSource === "wikipedia" ? "text-teal-700" : "text-gray-500"}`}>Wikipedia</span>
                    </button>
                    <button
                      onClick={() => setFetchSource("github")}
                      className={`p-3 rounded-xl border-2 flex flex-col items-center gap-1.5 transition-all ${
                        fetchSource === "github"
                          ? "border-teal-400 bg-teal-50 shadow-sm"
                          : "border-gray-100 bg-white/60 hover:border-teal-200"
                      }`}
                    >
                      <Github className={`h-5 w-5 ${fetchSource === "github" ? "text-teal-600" : "text-gray-400"}`} />
                      <span className={`text-xs font-semibold ${fetchSource === "github" ? "text-teal-700" : "text-gray-500"}`}>GitHub</span>
                    </button>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-600 uppercase tracking-wider">Fetch Limit</label>
                  <div className="flex items-center gap-3">
                    <Input
                      type="number"
                      min="1"
                      max="20"
                      value={fetchLimit}
                      onChange={(e) => setFetchLimit(parseInt(e.target.value) || 5)}
                      className="bg-white/80 border-teal-100 focus:border-teal-400 focus:ring-teal-400/20 w-20 text-center"
                    />
                    <div className="flex-1 flex gap-1">
                      {[1, 5, 10, 20].map(n => (
                        <button
                          key={n}
                          onClick={() => setFetchLimit(n)}
                          className={`flex-1 py-1 rounded-md text-xs font-medium transition-all ${
                            fetchLimit === n
                              ? "bg-teal-500 text-white shadow-sm"
                              : "bg-gray-50 text-gray-500 hover:bg-teal-50 hover:text-teal-600"
                          }`}
                        >
                          {n}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <button
                  onClick={fetchAndGenerate}
                  disabled={fetching}
                  className={`w-full py-2.5 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 transition-all active:scale-[0.98] ${
                    fetching
                      ? "bg-teal-300 text-white cursor-wait"
                      : "bg-gradient-to-r from-teal-500 to-emerald-500 text-white hover:from-teal-600 hover:to-emerald-600 hover:shadow-lg shadow-teal-200"
                  }`}
                >
                  {fetching ? (
                    <><Loader2 className="h-4 w-4 animate-spin" /> Fetching &amp; Generating...</>
                  ) : (
                    <><RefreshCw className="h-4 w-4" /> Fetch &amp; Generate</>
                  )}
                </button>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Right Panel - Ideas List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Yuga Evolution Records</span>
                <Button onClick={loadIdeas} variant="ghost" size="sm">
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </CardTitle>
              <CardDescription>
                {ideas.length} ideas mapped across the four Yugas
              </CardDescription>

              {/* Smart Search Bar */}
              <div className="mt-4 space-y-2">
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Smart search: Try 'algorithm', 'cooking', 'transportation'..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                      className="pl-10 pr-10"
                    />
                    {searchQuery && (
                      <button
                        onClick={clearSearch}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                  <Button onClick={handleSearch} disabled={searching || !searchQuery.trim()}>
                    {searching ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Search className="h-4 w-4" />
                    )}
                  </Button>
                </div>

                {searchType && (
                  <div className="flex items-center gap-2 text-xs">
                    <Badge variant={searchType === "semantic" ? "default" : "secondary"}>
                      {searchType === "semantic" ? "🧠 AI-Powered Search" :
                        searchType === "exact" ? "✓ Exact Match" : "Basic Search"}
                    </Badge>
                    <span className="text-muted-foreground">
                      Found {filteredIdeas.length} result{filteredIdeas.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-amber-500" />
                </div>
              ) : filteredIdeas.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>
                    {searchQuery
                      ? `No results found for "${searchQuery}". Try different keywords!`
                      : "No ideas yet. Generate your first Yuga evolution!"}
                  </p>
                  {searchQuery && (
                    <Button onClick={clearSearch} variant="outline" className="mt-4">
                      Clear Search
                    </Button>
                  )}
                </div>
              ) : (
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  {filteredIdeas.map((idea, idx) => (
                    <motion.div
                      key={idea._id || idx}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.05 }}
                    >
                      <Card
                        className="cursor-pointer hover:shadow-md transition-shadow"
                        onClick={() => openIdeaDetail(idea)}
                      >
                        <CardContent className="pt-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h3 className="font-semibold text-lg mb-1">{idea.idea}</h3>
                              <p className="text-sm text-muted-foreground mb-2">
                                {idea.description.substring(0, 100)}...
                              </p>
                              <div className="flex items-center gap-2 flex-wrap">
                                <Badge variant="outline">{idea.source}</Badge>
                                <span className="text-xs text-muted-foreground">
                                  {new Date(idea.timestamp).toLocaleDateString()}
                                </span>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="h-6 text-xs"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    viewEvolutionChain(idea.idea);
                                  }}
                                >
                                  <Network className="h-3 w-3 mr-1" />
                                  Chain
                                </Button>
                              </div>
                            </div>
                            <Eye className="h-5 w-5 text-muted-foreground" />
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Selected Idea Detail Modal */}
      {selectedIdea && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
          onClick={() => { setSelectedIdea(null); setIdeaImages([]); }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold mb-2">{selectedIdea.idea}</h2>
                  <p className="text-muted-foreground">{selectedIdea.description}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge>{selectedIdea.source}</Badge>
                    <span className="text-sm text-muted-foreground">
                      {new Date(selectedIdea.timestamp).toLocaleString()}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button 
                    onClick={downloadPDFReport}
                    variant="outline"
                    className="gap-2 border-orange-200/50 hover:bg-orange-50 text-slate-700 hover:text-orange-600 rounded-xl"
                  >
                    <Download className="h-4 w-4" />
                    Download PDF
                  </Button>
                  <Button variant="ghost" onClick={() => { setSelectedIdea(null); setIdeaImages([]); }}>
                    ✕
                  </Button>
                </div>
              </div>

              {/* Idea Images */}
              {loadingImages ? (
                <div className="flex items-center gap-2 mb-6 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Fetching images...
                </div>
              ) : ideaImages.length > 0 ? (
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-muted-foreground mb-3 flex items-center gap-2">
                    <Globe className="h-4 w-4" />
                    Related Images (via Wikimedia)
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {ideaImages.map((url, idx) => (
                      <a key={idx} href={url} target="_blank" rel="noopener noreferrer">
                        <img
                          src={url}
                          alt={`${selectedIdea.idea} - image ${idx + 1}`}
                          className="w-full h-32 object-cover rounded-lg border hover:opacity-90 transition-opacity cursor-pointer shadow-sm"
                          onError={(e) => {
                            (e.target as HTMLImageElement).parentElement!.style.display = "none";
                          }}
                        />
                      </a>
                    ))}
                  </div>
                </div>
              ) : null}

              <Tabs defaultValue="satya_yuga" className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                  {Object.keys(yugaLabels).map((yuga) => (
                    <TabsTrigger key={yuga} value={yuga}>
                      {yugaLabels[yuga as keyof typeof yugaLabels].split(" ")[0]}
                    </TabsTrigger>
                  ))}
                </TabsList>

                {Object.entries(selectedIdea.evolution).map(([yuga, data]) => (
                  <TabsContent key={yuga} value={yuga} className="space-y-4">
                    {/* Yuga header banner */}
                    <div className={`p-6 rounded-lg bg-gradient-to-r ${yugaColors[yuga as keyof typeof yugaColors]} text-white`}>
                      <h3 className="text-2xl font-bold mb-1">
                        {yugaLabels[yuga as keyof typeof yugaLabels]}
                      </h3>
                      {data.time_period && (
                        <div className="flex items-center gap-2 text-white/90">
                          <Calendar className="h-4 w-4" />
                          <span className="text-sm font-medium">{data.time_period}</span>
                        </div>
                      )}
                      {data.impact && (
                        <p className="mt-3 text-white/95 text-sm font-medium italic border-t border-white/30 pt-3">
                          "{data.impact}"
                        </p>
                      )}
                    </div>

                    {/* Structured description paragraphs */}
                    {data.paragraphs && data.paragraphs.length > 0 ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {data.paragraphs.map((para: any, idx: number) => (
                          para.text ? (
                            <Card key={idx} className="border border-gray-100">
                              <CardContent className="pt-4">
                                <div className="flex items-center gap-2 mb-2">
                                  <div className={`w-2 h-2 rounded-full bg-gradient-to-r ${yugaColors[yuga as keyof typeof yugaColors]}`} />
                                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                                    {para.label}
                                  </span>
                                </div>
                                <p className="text-sm leading-relaxed text-gray-700">{para.text}</p>
                              </CardContent>
                            </Card>
                          ) : null
                        ))}
                      </div>
                    ) : (
                      /* Fallback: plain description */
                      <Card>
                        <CardContent className="pt-4">
                          <p className="text-sm leading-relaxed whitespace-pre-line text-gray-700">
                            {data.description}
                          </p>
                        </CardContent>
                      </Card>
                    )}

                    {/* Key Insight callout */}
                    {data.key_insight && (
                      <div className={`p-4 rounded-lg bg-gradient-to-r ${yugaColors[yuga as keyof typeof yugaColors]} bg-opacity-10 border-l-4`}
                        style={{ borderLeftColor: "currentColor" }}>
                        <div className="flex items-start gap-3">
                          <Sparkles className="h-5 w-5 mt-0.5 flex-shrink-0 text-amber-600" />
                          <div>
                            <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-1">Key Insight</p>
                            <p className="text-sm text-gray-700 leading-relaxed">{data.key_insight}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Metric cards */}
                    {data.statistics_detailed?.metrics && data.statistics_detailed.metrics.length > 0 && (
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="flex items-center gap-2 text-base">
                            <BarChart3 className="h-4 w-4" />
                            Metrics & Statistics
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                            {data.statistics_detailed.metrics.map((metric: any, idx: number) => (
                              <div key={idx} className="p-3 bg-gray-50 rounded-lg border border-gray-100 hover:bg-gray-100 transition-colors">
                                <div className="text-xl mb-1">{metric.icon}</div>
                                <div className="text-xs text-muted-foreground font-medium">{metric.label}</div>
                                <div className="text-sm font-bold text-gray-800 mt-0.5">{metric.value}</div>
                              </div>
                            ))}
                          </div>
                          {data.statistics_detailed.original && (
                            <p className="mt-3 text-xs text-muted-foreground bg-blue-50 p-2 rounded">
                              {data.statistics_detailed.original}
                            </p>
                          )}
                        </CardContent>
                      </Card>
                    )}

                    {/* Characteristics */}
                    {data.characteristics_list && data.characteristics_list.length > 0 && (
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="flex items-center gap-2 text-base">
                            <Sparkles className="h-4 w-4" />
                            Key Characteristics
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="flex flex-wrap gap-2">
                            {data.characteristics_list.map((char: string, idx: number) => (
                              <span
                                key={idx}
                                className={`px-3 py-1 rounded-full text-sm font-medium text-white bg-gradient-to-r ${yugaColors[yuga as keyof typeof yugaColors]}`}
                              >
                                {char}
                              </span>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </TabsContent>
                ))}
              </Tabs>

              {/* Per-Idea AI Chat Section */}
              <div className="mt-6 border-t border-gray-100 pt-5">
                <IdeaChatPanel
                  ideaId={selectedIdea.idea}
                  ideaTitle={selectedIdea.idea}
                  ideaCategory="Yugas Evolution"
                />
              </div>

              {/* Off-screen Printable Template for PDF Report */}
              <div
                id="yugas-report-printable"
                style={{
                  position: "absolute",
                  left: "-9999px",
                  top: "-9999px",
                  width: "800px",
                  padding: "32px",
                  backgroundColor: "#ffffff",
                  fontFamily: "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
                  color: "#1e293b",
                  fontSize: "13px",
                  lineHeight: "1.6",
                }}
              >
                {/* Report Cover / Header */}
                <div style={{ borderBottom: "4px solid #f59e0b", paddingBottom: "24px", marginBottom: "24px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "11px", fontWeight: 700, color: "#d97706", textTransform: "uppercase", letterSpacing: "2px" }}>
                      Cosmic Evolution Report
                    </span>
                    <span style={{ fontSize: "11px", color: "#94a3b8" }}>
                      Generated on {new Date().toLocaleDateString()}
                    </span>
                  </div>
                  <h1 style={{ fontSize: "28px", fontWeight: 800, color: "#0f172a", margin: "8px 0 0 0" }}>
                    {selectedIdea.idea}
                  </h1>
                  <p style={{ color: "#475569", marginTop: "8px", fontSize: "13px", lineHeight: "1.7" }}>
                    {selectedIdea.description}
                  </p>
                  <div style={{ display: "flex", gap: "16px", marginTop: "12px", fontSize: "11px", color: "#64748b" }}>
                    <span><strong>Source:</strong> {selectedIdea.source}</span>
                    <span><strong>Mapped on:</strong> {new Date(selectedIdea.timestamp).toLocaleDateString()}</span>
                  </div>
                </div>

                {/* Images Section */}
                {ideaImages.length > 0 && (
                  <div style={{ marginBottom: "32px" }}>
                    <h2 style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "2px", marginBottom: "12px" }}>
                      Historical Visual Reference
                    </h2>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                      {ideaImages.slice(0, 4).map((url, idx) => (
                        <div key={idx} style={{ height: "160px", overflow: "hidden", borderRadius: "8px", border: "1px solid #e2e8f0", backgroundColor: "#f8fafc" }}>
                          <img
                            src={url}
                            alt={`${selectedIdea.idea} reference ${idx + 1}`}
                            style={{ width: "100%", height: "100%", objectFit: "cover" }}
                            crossOrigin="anonymous"
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Yuga Timeline Breakdown */}
                <div>
                  {Object.entries(selectedIdea.evolution).map(([yuga, data]) => {
                    const yugaTitle = yugaLabels[yuga as keyof typeof yugaLabels];
                    const colors: Record<string, { bg: string; border: string; text: string; badge: string }> = {
                      satya_yuga: { bg: "#fffbeb", border: "#f59e0b", text: "#92400e", badge: "#f59e0b" },
                      treta_yuga: { bg: "#eff6ff", border: "#3b82f6", text: "#1e40af", badge: "#3b82f6" },
                      dwapar_yuga: { bg: "#fff7ed", border: "#f97316", text: "#9a3412", badge: "#f97316" },
                      kali_yuga: { bg: "#faf5ff", border: "#a855f7", text: "#6b21a8", badge: "#a855f7" },
                    };
                    const c = colors[yuga] || colors.kali_yuga;

                    return (
                      <div key={yuga} style={{ border: "1px solid #e2e8f0", borderRadius: "12px", padding: "24px", backgroundColor: "#ffffff", marginBottom: "24px", pageBreakInside: "avoid" }}>
                        {/* Era header banner */}
                        <div style={{ padding: "16px", borderRadius: "8px", borderLeft: `4px solid ${c.border}`, backgroundColor: c.bg, display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                          <div>
                            <h3 style={{ fontSize: "16px", fontWeight: 700, color: c.text, margin: 0 }}>{yugaTitle}</h3>
                            {data.time_period && (
                              <p style={{ fontSize: "11px", fontWeight: 600, color: c.text, opacity: 0.9, margin: "4px 0 0 0" }}>{data.time_period}</p>
                            )}
                          </div>
                          <span style={{ fontSize: "10px", textTransform: "uppercase", fontWeight: 700, letterSpacing: "1px", padding: "3px 10px", borderRadius: "12px", backgroundColor: c.badge, color: "#ffffff" }}>
                            {yuga.replace("_", " ")}
                          </span>
                        </div>

                        {/* Impact Quote */}
                        {data.impact && (
                          <div style={{ padding: "12px", backgroundColor: "#f8fafc", borderRadius: "8px", borderLeft: "2px solid #cbd5e1", fontStyle: "italic", fontSize: "12px", color: "#475569", marginBottom: "16px" }}>
                            "{data.impact}"
                          </div>
                        )}

                        {/* Description paragraphs */}
                        <div style={{ marginBottom: "16px" }}>
                          <h4 style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "1.5px", marginBottom: "8px" }}>Evolutionary Narrative</h4>
                          {data.paragraphs && data.paragraphs.length > 0 ? (
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                              {data.paragraphs.map((para: any, pIdx: number) => (
                                para.text ? (
                                  <div key={pIdx} style={{ padding: "12px", backgroundColor: "#f8fafc", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
                                    <span style={{ fontSize: "10px", fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "1px", display: "block", marginBottom: "4px" }}>
                                      {para.label}
                                    </span>
                                    <p style={{ fontSize: "12px", lineHeight: "1.6", color: "#334155", margin: 0 }}>{para.text}</p>
                                  </div>
                                ) : null
                              ))}
                            </div>
                          ) : (
                            <p style={{ fontSize: "12px", lineHeight: "1.7", color: "#334155", whiteSpace: "pre-wrap" }}>{data.description}</p>
                          )}
                        </div>

                        {/* Metrics and Characteristics */}
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                          {/* Metrics */}
                          {data.statistics_detailed?.metrics && data.statistics_detailed.metrics.length > 0 && (
                            <div>
                              <h4 style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "1.5px", marginBottom: "8px" }}>Era Metrics</h4>
                              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px" }}>
                                {data.statistics_detailed.metrics.map((metric: any, mIdx: number) => (
                                  <div key={mIdx} style={{ padding: "8px", backgroundColor: "#f8fafc", borderRadius: "8px", border: "1px solid #e2e8f0", textAlign: "center" }}>
                                    <div style={{ fontSize: "16px", marginBottom: "2px" }}>{metric.icon}</div>
                                    <div style={{ fontSize: "9px", color: "#94a3b8", fontWeight: 500 }}>{metric.label}</div>
                                    <div style={{ fontSize: "10px", fontWeight: 700, color: "#1e293b", marginTop: "2px" }}>{metric.value}</div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Characteristics */}
                          {data.characteristics_list && data.characteristics_list.length > 0 && (
                            <div>
                              <h4 style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "1.5px", marginBottom: "8px" }}>Key Characteristics</h4>
                              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                                {data.characteristics_list.map((char: string, cIdx: number) => (
                                  <span
                                    key={cIdx}
                                    style={{ padding: "3px 10px", fontSize: "10px", fontWeight: 600, borderRadius: "12px", backgroundColor: c.badge, color: "#ffffff" }}
                                  >
                                    {char}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Key Insight */}
                        {data.key_insight && (
                          <div style={{ padding: "12px", backgroundColor: "#fffbeb", borderRadius: "8px", borderLeft: "4px solid #f59e0b", fontSize: "12px", color: "#334155", marginTop: "16px" }}>
                            <span style={{ fontWeight: 700, color: "#92400e", display: "block", marginBottom: "4px", textTransform: "uppercase", letterSpacing: "1px", fontSize: "9px" }}>Key Insight</span>
                            {data.key_insight}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
                
                {/* Footer */}
                <div style={{ textAlign: "center", paddingTop: "32px", borderTop: "1px solid #e2e8f0", color: "#94a3b8", fontSize: "10px", marginTop: "32px" }}>
                  <p style={{ fontWeight: 600, color: "#64748b", margin: 0 }}>Theory-to-Reality Cosmic Evolution Tracker</p>
                  <p style={{ margin: "4px 0 0 0" }}>Generated dynamically from indexed research metadata.</p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
      {/* Evolution Chain Modal */}
      {selectedEvolutionChain && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedEvolutionChain(null)}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl max-w-2xl w-full p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
                  <Network className="h-6 w-6 text-purple-600" />
                  Evolution Chain
                </h2>
                <p className="text-muted-foreground">Using Lineage Graph (DAG)</p>
              </div>
              <Button variant="ghost" onClick={() => setSelectedEvolutionChain(null)}>
                ✕
              </Button>
            </div>

            <div className="space-y-6">
              <div>
                <h3 className="font-semibold text-lg mb-3 text-center text-purple-600">
                  {selectedEvolutionChain.idea}
                </h3>
              </div>

              {selectedEvolutionChain.ancestors && selectedEvolutionChain.ancestors.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2 flex items-center gap-2">
                    <span className="text-blue-600">↑</span> Ancestors (Evolved From)
                  </h4>
                  <div className="space-y-2">
                    {selectedEvolutionChain.ancestors.map((ancestor: string, idx: number) => (
                      <div key={idx} className="flex items-center gap-2 pl-4">
                        <div className="w-2 h-2 rounded-full bg-blue-500" />
                        <span className="text-sm">{ancestor}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedEvolutionChain.descendants && selectedEvolutionChain.descendants.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2 flex items-center gap-2">
                    <span className="text-green-600">↓</span> Descendants (Evolved Into)
                  </h4>
                  <div className="space-y-2">
                    {selectedEvolutionChain.descendants.map((descendant: string, idx: number) => (
                      <div key={idx} className="flex items-center gap-2 pl-4">
                        <div className="w-2 h-2 rounded-full bg-green-500" />
                        <span className="text-sm">{descendant}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedEvolutionChain.chain_length === 1 && (
                <div className="text-center text-muted-foreground py-4">
                  <Network className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>No evolution chain found for this idea</p>
                </div>
              )}

              <div className="pt-4 border-t">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Chain Length:</span>
                  <Badge>{selectedEvolutionChain.chain_length} ideas</Badge>
                </div>
                <div className="flex items-center justify-between text-sm mt-2">
                  <span className="text-muted-foreground">Data Structure:</span>
                  <span className="font-mono text-xs">{selectedEvolutionChain.data_structure}</span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
      {/* Yugas AI Chat Panel */}
      <YugasChatPanel />
    </div>
  );
};

export default YugasEvolution;
