import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

interface Laureate {
  laureate: string;
  category: string;
  year: number;
  motivation?: string;
}

interface Props {
  laureates: Laureate[];
  isLoading: boolean;
  isError: boolean;
}

const categoryColors: Record<string, string> = {
  Physics: "bg-blue-100 text-blue-800",
  Chemistry: "bg-green-100 text-green-800",
  Medicine: "bg-red-100 text-red-800",
  Literature: "bg-yellow-100 text-yellow-800",
  Peace: "bg-purple-100 text-purple-800",
  Economics: "bg-orange-100 text-orange-800",
};

export default function LaureateTable({ laureates, isLoading, isError }: Props) {
  if (isError) {
    return (
      <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 text-center text-sm text-destructive">
        Could not load laureates. Make sure the Flask backend is running on port 5000.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[...Array(8)].map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  if (!laureates.length) {
    return (
      <div className="rounded-lg border p-8 text-center text-muted-foreground text-sm">
        No laureates found.
      </div>
    );
  }

  return (
    <div className="rounded-lg border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Category</TableHead>
            <TableHead>Year</TableHead>
            <TableHead className="hidden md:table-cell">Motivation</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {laureates.map((l, i) => (
            <TableRow key={i}>
              <TableCell className="font-medium">{l.laureate}</TableCell>
              <TableCell>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${categoryColors[l.category] ?? "bg-gray-100 text-gray-800"}`}>
                  {l.category}
                </span>
              </TableCell>
              <TableCell>{l.year}</TableCell>
              <TableCell className="hidden md:table-cell text-sm text-muted-foreground max-w-xs truncate">
                {l.motivation ?? "—"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
