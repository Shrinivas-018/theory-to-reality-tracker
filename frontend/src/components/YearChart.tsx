import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface Laureate {
  year: number;
  category: string;
}

interface Props {
  laureates: Laureate[];
  isLoading: boolean;
}

export default function YearChart({ laureates, isLoading }: Props) {
  if (isLoading) return <Skeleton className="h-64 w-full" />;

  // Count per decade
  const decades: Record<number, number> = {};
  laureates.forEach(({ year }) => {
    const decade = Math.floor(year / 10) * 10;
    decades[decade] = (decades[decade] ?? 0) + 1;
  });

  const data = Object.entries(decades)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([decade, count]) => ({ decade: `${decade}s`, count }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Awards by Decade</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
            <XAxis dataKey="decade" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="count" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
