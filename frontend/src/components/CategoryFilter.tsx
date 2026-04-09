import { Badge } from "@/components/ui/badge";

interface Props {
  categories: string[];
  selected: string;
  onSelect: (c: string) => void;
}

export default function CategoryFilter({ categories, selected, onSelect }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      <Badge
        variant={selected === "" ? "default" : "outline"}
        className="cursor-pointer"
        onClick={() => onSelect("")}
      >
        All
      </Badge>
      {categories.map((c) => (
        <Badge
          key={c}
          variant={selected === c ? "default" : "outline"}
          className="cursor-pointer"
          onClick={() => onSelect(c)}
        >
          {c}
        </Badge>
      ))}
    </div>
  );
}
