import { Card, CardContent } from "@/components/ui/card";
import { Award, Calendar, Tag, Users } from "lucide-react";

interface Laureate {
  year: number;
  category: string;
  laureate: string;
}

interface Props {
  laureates: Laureate[];
  isLoading: boolean;
}

export default function StatsCards({ laureates, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <div className="h-8 bg-muted animate-pulse rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const total = laureates.length;
  const categories = new Set(laureates.map((l) => l.category)).size;
  const earliest = laureates.length ? Math.min(...laureates.map((l) => l.year)) : 0;
  const latest = laureates.length ? Math.max(...laureates.map((l) => l.year)) : 0;

  const stats = [
    { label: "Total Laureates", value: total, icon: Users },
    { label: "Categories", value: categories, icon: Tag },
    { label: "First Award", value: earliest, icon: Calendar },
    { label: "Latest Award", value: latest, icon: Award },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {stats.map(({ label, value, icon: Icon }) => (
        <Card key={label}>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
              <Icon className="h-4 w-4 text-primary" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">{label}</p>
              <p className="text-xl font-bold">{value}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
