import { useEffect, useState } from 'react'

import { MorphingTextDemo } from '@/components/ui/morphing-text.demo'
import { Default as SpotlightCardDemo } from '@/components/ui/spotlight-card.demo'
import { DemoBackgroundPaths } from '@/components/ui/background-paths.demo'
import { AnimatedTabsDemo } from '@/components/ui/animated-tabs.demo'
import SpinnerDemoModule from '@/components/ui/spinner.demo'
import { Demo as GradientButtonDemo } from '@/components/ui/gradient-button.demo'
import ShimmerTextDemo from '@/components/ui/shimmer-text.demo'
import AnimatedBeamDemo from '@/components/ui/animated-beam.demo'

const SpinnerDemo = SpinnerDemoModule.Demo

const sections: { name: string; file: string; render: () => React.ReactNode }[] = [
  { name: 'Animated Beam', file: 'animated-beam.tsx', render: () => <AnimatedBeamDemo /> },
  { name: 'Shimmer Text', file: 'shimmer-text.tsx', render: () => <ShimmerTextDemo /> },
  { name: 'Morphing Text', file: 'morphing-text.tsx', render: () => <MorphingTextDemo /> },
  { name: 'Spotlight Card', file: 'spotlight-card.tsx', render: () => <SpotlightCardDemo /> },
  { name: 'Animated Tabs', file: 'animated-tabs.tsx', render: () => <AnimatedTabsDemo /> },
  { name: 'Spinner', file: 'spinner.tsx', render: () => <SpinnerDemo /> },
  { name: 'Gradient Button', file: 'gradient-button.tsx', render: () => <GradientButtonDemo /> },
  { name: 'Background Paths', file: 'background-paths.tsx', render: () => <DemoBackgroundPaths /> },
]

function App() {
  const [dark, setDark] = useState(false)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
  }, [dark])

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-50 flex items-center justify-between border-b border-border bg-background/80 px-6 py-4 backdrop-blur">
        <div>
          <h1 className="text-lg font-semibold tracking-tight">Component Studio</h1>
          <p className="text-sm text-muted-foreground">
            {sections.length} components from the 21st.dev archive
          </p>
        </div>
        <button
          onClick={() => setDark((d) => !d)}
          className="rounded-md border border-border px-3 py-1.5 text-sm transition-colors hover:bg-accent"
        >
          {dark ? 'Light' : 'Dark'}
        </button>
      </header>

      <main className="mx-auto flex max-w-6xl flex-col gap-16 px-6 py-12">
        {sections.map((section) => (
          <section key={section.file}>
            <div className="mb-4 flex items-baseline gap-3">
              <h2 className="text-base font-medium">{section.name}</h2>
              <code className="text-xs text-muted-foreground">{section.file}</code>
            </div>
            <div className="overflow-hidden rounded-xl border border-border">
              {section.render()}
            </div>
          </section>
        ))}
      </main>
    </div>
  )
}

export default App
