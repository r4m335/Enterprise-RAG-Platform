import * as React from "react";
import { cn } from "@/lib/utils";

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: number;
  indicatorClassName?: string;
  showShimmer?: boolean;
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value = 0, indicatorClassName, showShimmer = true, ...props }, ref) => {
    const clampedValue = Math.min(100, Math.max(0, value || 0));

    return (
      <div
        ref={ref}
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={clampedValue}
        className={cn(
          "relative h-2 w-full overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800",
          className
        )}
        {...props}
      >
        <div
          className={cn(
            "h-full w-full flex-1 bg-gradient-to-r from-blue-600 via-indigo-500 to-violet-500 transition-all duration-300 ease-out relative overflow-hidden rounded-full",
            indicatorClassName
          )}
          style={{ transform: `translateX(-${100 - clampedValue}%)` }}
        >
          {showShimmer && clampedValue > 0 && clampedValue < 100 && (
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/25 to-transparent animate-shimmer" />
          )}
        </div>
      </div>
    );
  }
);

Progress.displayName = "Progress";

export { Progress };
