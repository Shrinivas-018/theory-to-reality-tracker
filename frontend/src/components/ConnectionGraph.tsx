import { useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface Node { id: string; label: string }
interface Edge { source: string; target: string }
interface Props {
  connections: { nodes: Node[]; edges: Edge[] };
  isLoading: boolean;
}

export default function ConnectionGraph({ connections, isLoading }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!connections?.nodes?.length || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = canvas.width;
    const H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    // Limit to first 80 nodes for performance
    const nodes = connections.nodes.slice(0, 80);
    const nodeIds = new Set(nodes.map((n) => n.id));
    const edges = connections.edges.filter(
      (e) => nodeIds.has(e.source) && nodeIds.has(e.target)
    );

    // Place nodes in a circle
    const positions: Record<string, { x: number; y: number }> = {};
    nodes.forEach((node, i) => {
      const angle = (i / nodes.length) * 2 * Math.PI;
      positions[node.id] = {
        x: W / 2 + (W * 0.38) * Math.cos(angle),
        y: H / 2 + (H * 0.38) * Math.sin(angle),
      };
    });

    // Draw edges
    ctx.strokeStyle = "hsl(215 20% 65% / 0.3)";
    ctx.lineWidth = 0.8;
    edges.forEach(({ source, target }) => {
      const s = positions[source];
      const t = positions[target];
      if (!s || !t) return;
      ctx.beginPath();
      ctx.moveTo(s.x, s.y);
      ctx.lineTo(t.x, t.y);
      ctx.stroke();
    });

    // Draw nodes
    nodes.forEach((node) => {
      const { x, y } = positions[node.id];
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, 2 * Math.PI);
      ctx.fillStyle = "hsl(var(--primary))";
      ctx.fill();
    });
  }, [connections]);

  if (isLoading) return <Skeleton className="h-96 w-full" />;

  if (!connections?.nodes?.length) {
    return (
      <div className="rounded-lg border p-8 text-center text-muted-foreground text-sm">
        No connection data. Make sure the Flask backend is running.
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          Laureate Connections ({connections.nodes.length} nodes, {connections.edges.length} edges)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <canvas
          ref={canvasRef}
          width={800}
          height={500}
          className="w-full rounded border bg-muted/20"
        />
        <p className="text-xs text-muted-foreground mt-2">
          Showing first 80 nodes. Connections between laureates who share the same year and category.
        </p>
      </CardContent>
    </Card>
  );
}
