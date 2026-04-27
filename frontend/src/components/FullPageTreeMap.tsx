/**
 * Full-Page Tree Map Visualizer
 * 
 * Displays the evolution tree map in a full-screen dialog for better visibility
 */

import React from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { X, Maximize2 } from "lucide-react";
import TreeMapVisualizer from "@/components/TreeMapVisualizer";
import TreeMapErrorBoundary from "@/components/TreeMapVisualizer/TreeMapErrorBoundary";

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
}

interface FullPageTreeMapProps {
  isOpen: boolean;
  onClose: () => void;
  rootIdea: Idea;
  ancestors: Idea[];
  descendants: Idea[];
  onNodeClick: (id: string) => void;
  isLoading?: boolean;
}

const FullPageTreeMap: React.FC<FullPageTreeMapProps> = ({
  isOpen,
  onClose,
  rootIdea,
  ancestors,
  descendants,
  onNodeClick,
  isLoading = false,
}) => {
  const getStageColor = (stage: string) => {
    const stageColors: Record<string, string> = {
      philosophy: "bg-purple-100 text-purple-700",
      scientific_validation: "bg-blue-100 text-blue-700",
      engineering_application: "bg-orange-100 text-orange-700",
      modern_technology: "bg-green-100 text-green-700",
    };
    return stageColors[stage] || "bg-gray-100 text-gray-700";
  };

  const getStageLabel = (stage: string) => {
    return stage.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-[95vw] w-[95vw] h-[95vh] max-h-[95vh] p-0 gap-0">
        {/* Header */}
        <DialogHeader className="px-6 py-4 border-b bg-gradient-to-r from-slate-50 to-blue-50">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="outline" className="text-xs">{rootIdea.category}</Badge>
                <Badge className={`text-xs ${getStageColor(rootIdea.stage)}`} variant="secondary">
                  {getStageLabel(rootIdea.stage)}
                </Badge>
              </div>
              <DialogTitle className="text-2xl font-bold leading-tight mb-1">
                {rootIdea.title}
              </DialogTitle>
              <DialogDescription className="text-sm text-slate-600">
                {rootIdea.start_year}{rootIdea.end_year ? ` – ${rootIdea.end_year}` : ""} • 
                {ancestors.length} ancestors, {descendants.length} descendants
              </DialogDescription>
            </div>
            <button
              onClick={onClose}
              className="rounded-full p-2 hover:bg-slate-200 transition-colors"
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </DialogHeader>

        {/* Tree Map Content */}
        <div className="flex-1 overflow-hidden p-6 bg-slate-950 relative">
          {/* Background Grid Pattern */}
          <div 
            className="absolute inset-0 pointer-events-none opacity-20"
            style={{
              backgroundImage: 'radial-gradient(circle at 2px 2px, rgba(255,255,255,0.4) 1px, transparent 0)',
              backgroundSize: '32px 32px'
            }}
          />
          <TreeMapErrorBoundary>
            <div className="h-full w-full relative z-10">
              <TreeMapVisualizer
                rootIdea={rootIdea}
                ancestors={ancestors}
                descendants={descendants}
                onNodeClick={onNodeClick}
                isLoading={isLoading}
              />
            </div>
          </TreeMapErrorBoundary>
        </div>

        {/* Footer with stats */}
        <div className="px-6 py-3 border-t bg-white flex items-center justify-between text-sm text-slate-600">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-pink-400"></div>
              <span>Ancestors ({ancestors.length})</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-violet-400"></div>
              <span>Descendants ({descendants.length})</span>
            </div>
          </div>
          <div className="text-xs text-slate-500">
            Click any node to navigate • Hover to highlight connections
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default FullPageTreeMap;
