import React, { useState, useMemo, useCallback } from "react";
import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

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

interface NodeSelectorProps {
  ideas: Idea[];
  onPathRequest: (startId: string, targetId: string) => void;
  isLoading: boolean;
}

// Stage configuration for consistent styling
const stageConfig: Record<string, {
  label: string;
  color: string;
  textColor: string;
  bgColor: string;
}> = {
  philosophy: {
    label: "Philosophy",
    color: "bg-purple-500",
    textColor: "text-purple-700",
    bgColor: "bg-purple-50",
  },
  scientific_validation: {
    label: "Scientific Validation",
    color: "bg-blue-500",
    textColor: "text-blue-700",
    bgColor: "bg-blue-50",
  },
  engineering_application: {
    label: "Engineering Application",
    color: "bg-orange-500",
    textColor: "text-orange-700",
    bgColor: "bg-orange-50",
  },
  modern_technology: {
    label: "Modern Technology",
    color: "bg-green-500",
    textColor: "text-green-700",
    bgColor: "bg-green-50",
  },
};

const NodeSelector: React.FC<NodeSelectorProps> = ({ ideas, onPathRequest, isLoading }) => {
  const [startQuery, setStartQuery] = useState("");
  const [targetQuery, setTargetQuery] = useState("");
  const [selectedStart, setSelectedStart] = useState<Idea | null>(null);
  const [selectedTarget, setSelectedTarget] = useState<Idea | null>(null);
  const [showStartDropdown, setShowStartDropdown] = useState(false);
  const [showTargetDropdown, setShowTargetDropdown] = useState(false);

  // Filter ideas based on query - case-insensitive search across title, description, and keywords
  const filterIdeas = useCallback((query: string): Idea[] => {
    if (!query.trim()) return [];
    
    const normalizedQuery = query.toLowerCase().trim();
    
    return ideas.filter(idea => {
      const titleMatch = idea.title.toLowerCase().includes(normalizedQuery);
      const descMatch = idea.description.toLowerCase().includes(normalizedQuery);
      const keywordMatch = idea.keywords.some(k => k.toLowerCase().includes(normalizedQuery));
      
      return titleMatch || descMatch || keywordMatch;
    }).slice(0, 8); // Limit results for better UX
  }, [ideas]);

  const startResults = useMemo(() => filterIdeas(startQuery), [startQuery, filterIdeas]);
  const targetResults = useMemo(() => filterIdeas(targetQuery), [targetQuery, filterIdeas]);

  const handleStartQueryChange = (value: string) => {
    setStartQuery(value);
    setShowStartDropdown(value.length > 0);
    if (selectedStart && value !== selectedStart.title) {
      setSelectedStart(null);
    }
  };

  const handleTargetQueryChange = (value: string) => {
    setTargetQuery(value);
    setShowTargetDropdown(value.length > 0);
    if (selectedTarget && value !== selectedTarget.title) {
      setSelectedTarget(null);
    }
  };

  const handleStartSelect = (idea: Idea) => {
    setSelectedStart(idea);
    setStartQuery(idea.title);
    setShowStartDropdown(false);
  };

  const handleTargetSelect = (idea: Idea) => {
    setSelectedTarget(idea);
    setTargetQuery(idea.title);
    setShowTargetDropdown(false);
  };

  const handleStartClear = () => {
    setSelectedStart(null);
    setStartQuery("");
    setShowStartDropdown(false);
  };

  const handleTargetClear = () => {
    setSelectedTarget(null);
    setTargetQuery("");
    setShowTargetDropdown(false);
  };

  const handleFindPath = () => {
    if (selectedStart && selectedTarget && selectedStart.id !== selectedTarget.id) {
      onPathRequest(selectedStart.id, selectedTarget.id);
    }
  };

  const isValidSelection = selectedStart && selectedTarget && selectedStart.id !== selectedTarget.id;

  const renderIdeaResult = (idea: Idea, onSelect: (idea: Idea) => void) => {
    const config = stageConfig[idea.stage] || stageConfig.philosophy;
    
    return (
      <button
        key={idea.id}
        onClick={() => onSelect(idea)}
        className="w-full text-left px-3 py-3 hover:bg-slate-50 border-b last:border-0 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${config.color} shrink-0`} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-medium text-sm truncate">{idea.title}</span>
              <Badge variant="outline" className={`text-xs ${config.textColor} shrink-0`}>
                {idea.start_year}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground line-clamp-1">{idea.description}</p>
          </div>
        </div>
      </button>
    );
  };

  const renderSelectedBadge = (idea: Idea, onClear: () => void, label: string) => {
    const config = stageConfig[idea.stage] || stageConfig.philosophy;
    
    return (
      <div className={`${config.color} text-white rounded-lg px-3 py-2 flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{idea.title}</span>
          <span className="text-xs opacity-90">({idea.start_year})</span>
        </div>
        <button
          onClick={onClear}
          className="text-white/70 hover:text-white ml-2 p-1 rounded-full hover:bg-white/20 transition-colors"
          aria-label={`Clear ${label}`}
        >
          <X className="h-3 w-3" />
        </button>
      </div>
    );
  };

  return (
    <Card className="bg-white/80 backdrop-blur-sm">
      <CardContent className="p-6 space-y-6">
        {/* Dual Search Fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Start Idea Selection */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-purple-700">
              Start Idea (Origin)
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Search starting idea..."
                value={startQuery}
                onChange={(e) => handleStartQueryChange(e.target.value)}
                onFocus={() => setShowStartDropdown(startQuery.length > 0)}
              />
              
              {/* Start Dropdown */}
              {showStartDropdown && startResults.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white border rounded-lg shadow-lg z-10 max-h-64 overflow-y-auto">
                  {startResults.map(idea => renderIdeaResult(idea, handleStartSelect))}
                </div>
              )}
            </div>
            
            {/* Selected Start Badge */}
            {selectedStart && renderSelectedBadge(selectedStart, handleStartClear, "start idea")}
          </div>

          {/* Target Idea Selection */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-green-700">
              Target Idea (Destination)
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Search destination idea..."
                value={targetQuery}
                onChange={(e) => handleTargetQueryChange(e.target.value)}
                onFocus={() => setShowTargetDropdown(targetQuery.length > 0)}
              />
              
              {/* Target Dropdown */}
              {showTargetDropdown && targetResults.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white border rounded-lg shadow-lg z-10 max-h-64 overflow-y-auto">
                  {targetResults.map(idea => renderIdeaResult(idea, handleTargetSelect))}
                </div>
              )}
            </div>
            
            {/* Selected Target Badge */}
            {selectedTarget && renderSelectedBadge(selectedTarget, handleTargetClear, "target idea")}
          </div>
        </div>

        {/* Find Evolution Path Button */}
        <div className="flex justify-center">
          <Button
            onClick={handleFindPath}
            disabled={!isValidSelection || isLoading}
            className="px-8 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:opacity-50"
          >
            {isLoading ? "Finding path..." : "Find Evolution Path"}
          </Button>
        </div>

        {/* Validation Messages */}
        {selectedStart && selectedTarget && selectedStart.id === selectedTarget.id && (
          <div className="text-center text-sm text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2">
            Please select two different ideas to find an evolution path.
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default NodeSelector;