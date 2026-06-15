import * as React from "react";
import { cn } from "../../lib/utils";

const Separator = React.forwardRef<
  React.ComponentRef<typeof import("@radix-ui/react-separator").Root>,
  React.ComponentPropsWithoutRef<typeof import("@radix-ui/react-separator").Root>
>(({ className, orientation = "horizontal", decorative = true, ...props }, ref) => (
  <div
    ref={ref as React.Ref<HTMLDivElement>}
    role={decorative ? "none" : "separator"}
    className={cn(
      "shrink-0 bg-border",
      orientation === "horizontal" ? "h-[1px] w-full" : "h-full w-[1px]",
      className
    )}
    {...props}
  />
));
Separator.displayName = "Separator";

export { Separator };
