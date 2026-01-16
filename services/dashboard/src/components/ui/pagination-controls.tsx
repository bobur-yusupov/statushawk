import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationControlsProps {
    page: number;
    setPage: (page: number) => void;
    hasPrevious: boolean;
    hasNext: boolean;
    totalCount: number;
    isLoading?: boolean;
    pageSize?: number;
}

export function PaginationControls({
    page,
    setPage,
    hasPrevious,
    hasNext,
    totalCount,
    isLoading = false,
    pageSize = 20
}: PaginationControlsProps) {
    const start = (page - 1) * pageSize + 1;
    const end = Math.min(page * pageSize, totalCount);

    return (
    <div className="flex items-center justify-between border-t pt-4">
      <div className="text-sm text-zinc-500">
        {totalCount > 0 ? (
          <>
            Showing <span className="font-medium">{start}</span> to{" "}
            <span className="font-medium">{end}</span> of{" "}
            <span className="font-medium">{totalCount}</span> results
          </>
        ) : (
          "No results found"
        )}
      </div>
      
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setPage(Math.max(page - 1, 1))}
          disabled={!hasPrevious || isLoading}
        >
          <ChevronLeft className="h-4 w-4 mr-2" />
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setPage(page + 1)}
          disabled={!hasNext || isLoading}
        >
          Next
          <ChevronRight className="h-4 w-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}
