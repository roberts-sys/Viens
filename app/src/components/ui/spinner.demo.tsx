import { Spinner } from "@/components/ui/spinner"

const variants = ['default', 'circle', 'pinwheel', 'circle-filled', 'ellipsis', 'ring', 'bars', 'infinite'] as const;

const Demo = () => (
  <div className="grid grid-cols-4 gap-16">
    {variants.map((variant) => (
      <div key={variant} className="flex flex-col items-center justify-center gap-4">
        <Spinner key={variant} variant={variant} />
        <span className="text-xs text-muted-foreground font-mono">{variant}</span>
      </div>
    ))}
  </div>
);

export default { Demo }
