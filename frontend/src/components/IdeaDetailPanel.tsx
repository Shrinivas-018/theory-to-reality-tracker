import React, { useEffect, useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Loader2, BrainCircuit, Lightbulb, ExternalLink, Network, Sparkles, Wand2, Check, GitMerge, Maximize2 } from "lucide-react";
import TreeMapVisualizer from "@/components/TreeMapVisualizer";
import TreeMapErrorBoundary from "@/components/TreeMapVisualizer/TreeMapErrorBoundary";
import FullPageTreeMap from "@/components/FullPageTreeMap";

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

interface IdeaDetailPanelProps {
  ideaId: string | null;
  onClose: () => void;
  allIdeas: Idea[];
  onSelectSimilar?: (id: string) => void;
}

const IdeaDetailPanel: React.FC<IdeaDetailPanelProps> = ({ ideaId, onClose, allIdeas, onSelectSimilar }) => {
  const [similarIdeas, setSimilarIdeas] = useState<any[]>([]);
  const [ancestors, setAncestors] = useState<Idea[]>([]);
  const [descendants, setDescendants] = useState<Idea[]>([]);
  const [forecast, setForecast] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [summarizing, setSummarizing] = useState(false);
  const [summarizedText, setSummarizedText] = useState<string | null>(null);
  const [showFullPageTreeMap, setShowFullPageTreeMap] = useState(false);

  const idea = allIdeas.find(i => i.id === ideaId);

  useEffect(() => {
    if (!ideaId) {
      setSimilarIdeas([]);
      setAncestors([]);
      setDescendants([]);
      setForecast(null);
      setSummarizedText(null);
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      try {
        const [simRes, forRes, ancRes, descRes] = await Promise.all([
          fetch(`http://localhost:5000/api/predictions/similar/${ideaId}?top_n=4`),
          fetch(`http://localhost:5000/api/predictions/forecast/${ideaId}`),
          fetch(`http://localhost:5000/api/ideas/${ideaId}/ancestors`),
          fetch(`http://localhost:5000/api/ideas/${ideaId}/descendants`)
        ]);

        const simData = await simRes.json();
        const forData = await forRes.json();
        const ancData = await ancRes.json();
        const descData = await descRes.json();

        if (simData.status === "success") {
          setSimilarIdeas(Array.isArray(simData.data) ? simData.data : []);
        }
        if (forData.status === "success") {
          setForecast(forData.data || null);
        }
        if (ancData.status === "success") {
          setAncestors(ancData.data?.ancestors || []);
        }
        if (descData.status === "success") {
          setDescendants(descData.data?.descendants || []);
        }
      } catch (err) {
        console.error("Failed to fetch detail data:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [ideaId]);

  const handleSummarize = async () => {
    if (!ideaId) return;
    setSummarizing(true);
    try {
      const res = await fetch(`http://localhost:5000/api/llm/summarize/${ideaId}`, {
        method: "POST",
      });
      const data = await res.json();
      if (data?.data?.description) {
        setSummarizedText(data.data.description);
      }
    } catch (err) {
      console.error("LLM summarize failed:", err);
    } finally {
      setSummarizing(false);
    }
  };

  const getStageColor = (stage: string) => {
    const stageColors: Record<string, string> = {
      philosophy: "bg-purple-100 text-purple-700 hover:bg-purple-200",
      scientific_validation: "bg-blue-100 text-blue-700 hover:bg-blue-200",
      engineering_application: "bg-orange-100 text-orange-700 hover:bg-orange-200",
      modern_technology: "bg-green-100 text-green-700 hover:bg-green-200",
    };
    return stageColors[stage] || "bg-gray-100 text-gray-700";
  };

  const getStageLabel = (stage: string) => {
    return stage.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
  };

  if (!idea) return null;

  const currentDescription = summarizedText || idea.description;

  return (
    <Sheet open={!!ideaId} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="overflow-y-auto sm:max-w-lg md:max-w-xl w-[90vw] border-l outline-none">
        <SheetHeader className="mb-6 space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="text-xs">{idea.category}</Badge>
            <Badge className={`text-xs ${getStageColor(idea.stage)}`} variant="secondary">
              {getStageLabel(idea.stage)}
            </Badge>
          </div>
          <SheetTitle className="text-2xl md:text-3xl leading-tight">
            {idea.title}
          </SheetTitle>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Lightbulb className="h-4 w-4" />
            <span>{idea.start_year}{idea.end_year ? ` – ${idea.end_year}` : ""}</span>
          </div>
          <SheetDescription className="text-sm mt-1">
            <strong>Key Contributors:</strong> {idea.laureates.join(", ")}
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-8 pb-10">
          
          {/* Description Section */}
          <section className="space-y-3 relative group">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-lg border-b pb-1">Description</h3>
              <button
                onClick={handleSummarize}
                disabled={summarizing || !!summarizedText}
                className={`text-xs px-2.5 py-1 rounded-md flex items-center gap-1.5 transition-all
                  ${summarizedText 
                    ? "bg-green-50 text-green-600 border border-green-200"
                    : summarizing 
                      ? "bg-violet-50 text-violet-400 border border-violet-200 cursor-wait"
                      : "bg-white text-violet-600 border border-violet-200 shadow-sm hover:bg-violet-50"
                  }`}
              >
                {summarizedText ? (
                  <><Check className="w-3 h-3"/> AI Summarized</>
                ) : summarizing ? (
                  <><Loader2 className="w-3 h-3 animate-spin"/> Generating...</>
                ) : (
                  <><Wand2 className="w-3 h-3"/> AI Expand</>
                )}
              </button>
            </div>
            <p className="text-sm leading-relaxed text-slate-700 whitespace-pre-wrap">
              {currentDescription}
            </p>
            <div className="flex flex-wrap gap-1.5 pt-2">
              {idea.keywords.map((kw, i) => (
                <Badge key={i} variant="secondary" className="text-[10px] bg-slate-100 text-slate-500">
                  {kw}
                </Badge>
              ))}
            </div>
          </section>

          {/* Influence Score */}
          <section className="space-y-3">
            <h3 className="font-semibold text-lg border-b pb-1">Influence & Impact</h3>
            <div className="p-4 rounded-lg bg-gradient-to-br from-slate-50 to-blue-50 border">
              <div className="flex items-end justify-between font-medium">
                <span className="text-slate-600">Global Score</span>
                <span className="text-2xl text-blue-700">{(idea.influence_score * 100).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-2.5 mt-3 overflow-hidden">
                <div 
                  className="bg-blue-500 h-2.5 rounded-full transition-all duration-1000" 
                  style={{ width: `${Math.min(idea.influence_score * 100, 100)}%` }}
                ></div>
              </div>
            </div>
          </section>

          {loading ? (
            <div className="flex items-center justify-center p-8 bg-slate-50 rounded-xl">
              <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
            </div>
          ) : (
            <>
              {/* Evolutionary Lineage Tree Map */}
              <section className="space-y-3">
                <div className="flex items-center justify-between border-b pb-1">
                  <h3 className="font-semibold text-lg flex items-center gap-2">
                    <GitMerge className="h-4 w-4 text-pink-500" />
                    Evolutionary Lineage
                  </h3>
                  {(ancestors.length > 0 || descendants.length > 0) && (
                    <button
                      onClick={() => setShowFullPageTreeMap(true)}
                      className="text-xs px-2.5 py-1 rounded-md flex items-center gap-1.5 transition-all bg-white text-blue-600 border border-blue-200 shadow-sm hover:bg-blue-50"
                      title="Expand to full screen"
                    >
                      <Maximize2 className="w-3 h-3" />
                      Expand
                    </button>
                  )}
                </div>
                <TreeMapErrorBoundary>
                  <TreeMapVisualizer
                    rootIdea={idea}
                    ancestors={ancestors}
                    descendants={descendants}
                    onNodeClick={onSelectSimilar || (() => {})}
                    isLoading={loading}
                  />
                </TreeMapErrorBoundary>
              </section>
              {/* AI Forecast */}
              {forecast && (
                <section className="space-y-3">
                  <h3 className="font-semibold text-lg flex items-center gap-2 border-b pb-1">
                    <Sparkles className="h-4 w-4 text-violet-500" />
                    AI Evolutionary Forecast
                  </h3>
                  <div className="bg-gradient-to-r from-violet-50 to-fuchsia-50 rounded-lg p-4 border border-violet-100 space-y-4">
                    
                    <div className="flex flex-col gap-1 text-sm">
                      <span className="text-violet-600 font-medium tracking-wide text-xs uppercase">Predicted Trajectory</span>
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-lg text-slate-800">
                           {forecast.prediction || getStageLabel(forecast.predicted_next_stage || "Unknown")}
                        </span>
                        <Badge variant="outline" className="bg-white text-violet-700 border-violet-200">
                          {((forecast.probability ?? forecast.confidence ?? 0) * 100).toFixed(0)}% Confidence
                        </Badge>
                      </div>
                    </div>

                    {forecast.explanation ? (
                      <div className="text-sm text-slate-600 leading-relaxed border-t border-violet-100 pt-3 space-y-1.5">
                        <div className="font-medium text-slate-800 mb-2">Reason:</div>
                        <div className="flex items-center gap-2">
                          <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                          <span>High similarity to modern ideas ({forecast.explanation.similarity_score.toFixed(2)})</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                          <span>Strong network connections ({forecast.explanation.connectivity.toFixed(3)})</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                          <span>Recent relevance (Age context: {forecast.explanation.age} years)</span>
                        </div>
                      </div>
                    ) : (
                      <div className="text-sm text-slate-600 leading-relaxed border-t border-violet-100 pt-3">
                        {forecast.reason}
                      </div>
                    )}


                  </div>
                </section>
              )}

              {/* Similar Concepts */}
              {similarIdeas.length > 0 && (
                <section className="space-y-3">
                  <h3 className="font-semibold text-lg flex items-center gap-2 border-b pb-1">
                    <Network className="h-4 w-4 text-emerald-500" />
                    Technological Kinship
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {similarIdeas.map((sim, i) => {
                      const relatedIdea = allIdeas.find(ai => ai.id === sim.id);
                      if (!relatedIdea) return null;
                      return (
                        <div 
                          key={sim.id} 
                          onClick={() => {
                            if (onSelectSimilar) {
                              onSelectSimilar(sim.id);
                            }
                          }}
                          className={`p-3 rounded-lg border bg-white shadow-sm hover:shadow-md hover:border-emerald-200 transition-all cursor-pointer group flex flex-col justify-between`}
                        >
                          <div>
                            <div className="flex items-start justify-between gap-2 mb-1">
                              <h4 className="font-medium text-sm group-hover:text-emerald-700 transition-colors line-clamp-2 leading-tight">
                                {relatedIdea.title}
                              </h4>
                              <ExternalLink className="h-3 w-3 text-slate-300 group-hover:text-emerald-500 flex-shrink-0 mt-0.5" />
                            </div>
                            <div className="text-[10px] text-muted-foreground line-clamp-1">
                              {relatedIdea.category}
                            </div>
                          </div>
                          
                          <div className="mt-3 flex items-center justify-between text-xs pt-2 border-t">
                            <span className="text-slate-500">{relatedIdea.start_year}</span>
                            <Badge variant="outline" className="text-[10px] text-emerald-600 bg-emerald-50 border-emerald-100">
                              {(sim.similarity * 100).toFixed(0)}% match
                            </Badge>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </section>
              )}
            </>
          )}
        </div>
      </SheetContent>

      {/* Full-Page Tree Map Dialog */}
      {idea && (
        <FullPageTreeMap
          isOpen={showFullPageTreeMap}
          onClose={() => setShowFullPageTreeMap(false)}
          rootIdea={idea}
          ancestors={ancestors}
          descendants={descendants}
          onNodeClick={(id) => {
            setShowFullPageTreeMap(false);
            if (onSelectSimilar) {
              onSelectSimilar(id);
            }
          }}
          isLoading={loading}
        />
      )}
    </Sheet>
  );
};

export default IdeaDetailPanel;
