"use client";

import { forwardRef, useRef } from "react";
import { AnimatedBeam } from "@/components/ui/animated-beam";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Brand marks
//
// These are hand-drawn *approximations* in the correct brand colors, kept inline
// so the component stays dependency-free. For pixel-accurate marks, swap each
// one for the official path from `simple-icons` (all six ship in that package).
// ---------------------------------------------------------------------------

const ClaudeMark = () => (
  <svg viewBox="0 0 24 24" className="size-full" aria-label="Claude">
    {Array.from({ length: 12 }).map((_, i) => (
      <rect
        key={i}
        x="11.25"
        y="1.5"
        width="1.5"
        height="8.5"
        rx="0.75"
        fill="#D97757"
        transform={`rotate(${i * 30} 12 12)`}
      />
    ))}
  </svg>
);

const SolidWorksMark = () => (
  <svg viewBox="0 0 24 24" className="size-full" aria-label="SolidWorks">
    <rect x="1.5" y="1.5" width="21" height="21" rx="4" fill="#E4002B" />
    <text
      x="12"
      y="16.2"
      textAnchor="middle"
      fill="#ffffff"
      fontSize="9.5"
      fontWeight="700"
      fontFamily="system-ui, sans-serif"
    >
      SW
    </text>
  </svg>
);

const ArduinoMark = () => (
  <svg viewBox="0 0 24 24" className="size-full" aria-label="Arduino">
    <g
      fill="none"
      stroke="#00979D"
      strokeWidth="1.7"
      strokeLinecap="round"
    >
      <ellipse cx="12" cy="12" rx="10.4" ry="6.6" />
      {/* minus terminal */}
      <line x1="4.6" y1="12" x2="8.6" y2="12" />
      {/* plus terminal */}
      <line x1="15.4" y1="12" x2="19.4" y2="12" />
      <line x1="17.4" y1="10" x2="17.4" y2="14" />
    </g>
  </svg>
);

const RaspberryPiMark = () => (
  <svg viewBox="0 0 24 24" className="size-full" aria-label="Raspberry Pi">
    <g fill="#C51A4A">
      {/* leaves */}
      <path d="M11.6 5.4C10.6 3.5 8.4 2.7 6.9 3.6c.4 1.9 2.4 3.1 4 2.8z" />
      <path d="M12.4 5.4C13.4 3.5 15.6 2.7 17.1 3.6c-.4 1.9-2.4 3.1-4 2.8z" />
      {/* berry cluster */}
      <circle cx="12" cy="8.6" r="2.05" />
      <circle cx="8.7" cy="10.6" r="2.05" />
      <circle cx="15.3" cy="10.6" r="2.05" />
      <circle cx="8.7" cy="14.3" r="2.05" />
      <circle cx="15.3" cy="14.3" r="2.05" />
      <circle cx="12" cy="16.3" r="2.05" />
      <circle cx="12" cy="12.45" r="2.05" />
    </g>
  </svg>
);

const KiCadMark = () => (
  <svg viewBox="0 0 24 24" className="size-full" aria-label="KiCad">
    <g stroke="#314CB0" strokeWidth="1.7" fill="none" strokeLinecap="round">
      <circle cx="12" cy="12" r="3.1" fill="#314CB0" />
      <line x1="12" y1="2.4" x2="12" y2="8.9" />
      <line x1="12" y1="15.1" x2="12" y2="21.6" />
      <line x1="2.4" y1="12" x2="8.9" y2="12" />
      <line x1="15.1" y1="12" x2="21.6" y2="12" />
    </g>
    <g fill="#314CB0">
      <circle cx="12" cy="2.4" r="1.5" />
      <circle cx="12" cy="21.6" r="1.5" />
      <circle cx="2.4" cy="12" r="1.5" />
      <circle cx="21.6" cy="12" r="1.5" />
    </g>
  </svg>
);

const BlenderMark = () => (
  <svg viewBox="0 0 24 24" className="size-full" aria-label="Blender">
    <circle cx="13.2" cy="13.4" r="7.4" fill="#E87D0D" />
    <circle cx="13.2" cy="12.6" r="3.5" fill="#ffffff" />
    <circle cx="13.2" cy="12.6" r="1.7" fill="#265787" />
    <path
      d="M2.2 9.4 L10.4 4.6 L11.9 7.1 L4.6 11.4 Z"
      fill="#265787"
    />
  </svg>
);

const OutputMark = () => (
  <svg
    viewBox="0 0 24 24"
    className="size-full"
    fill="none"
    stroke="#3f3f46"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-label="Workstation"
  >
    <rect x="2" y="3.5" width="20" height="13" rx="2" />
    <line x1="8" y1="20.5" x2="16" y2="20.5" />
    <line x1="12" y1="16.5" x2="12" y2="20.5" />
  </svg>
);

// ---------------------------------------------------------------------------

const Circle = forwardRef<
  HTMLDivElement,
  { className?: string; children?: React.ReactNode }
>(({ className, children }, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        "z-10 flex size-14 items-center justify-center rounded-full border-2 border-border bg-white p-2.5 shadow-[0_0_20px_-12px_rgba(0,0,0,0.8)]",
        className,
      )}
    >
      {children}
    </div>
  );
});

Circle.displayName = "Circle";

export default function Demo() {
  const containerRef = useRef<HTMLDivElement>(null);
  const solidworksRef = useRef<HTMLDivElement>(null);
  const kicadRef = useRef<HTMLDivElement>(null);
  const blenderRef = useRef<HTMLDivElement>(null);
  const raspberryPiRef = useRef<HTMLDivElement>(null);
  const arduinoRef = useRef<HTMLDivElement>(null);
  const claudeRef = useRef<HTMLDivElement>(null);
  const outputRef = useRef<HTMLDivElement>(null);

  return (
    <div
      className="relative flex h-[500px] w-full items-center justify-center overflow-hidden rounded-lg border bg-background p-10 md:shadow-xl"
      ref={containerRef}
    >
      <div className="flex size-full max-h-[340px] max-w-2xl flex-row items-stretch justify-between gap-10">
        {/* inputs */}
        <div className="flex flex-col justify-center gap-5">
          <Circle ref={solidworksRef}>
            <SolidWorksMark />
          </Circle>
          <Circle ref={kicadRef}>
            <KiCadMark />
          </Circle>
          <Circle ref={blenderRef}>
            <BlenderMark />
          </Circle>
          <Circle ref={raspberryPiRef}>
            <RaspberryPiMark />
          </Circle>
          <Circle ref={arduinoRef}>
            <ArduinoMark />
          </Circle>
        </div>

        {/* Claude */}
        <div className="flex flex-col justify-center">
          <Circle ref={claudeRef} className="size-20 p-3.5">
            <ClaudeMark />
          </Circle>
        </div>

        {/* output */}
        <div className="flex flex-col justify-center">
          <Circle ref={outputRef}>
            <OutputMark />
          </Circle>
        </div>
      </div>

      {/* tools -> Claude */}
      <AnimatedBeam
        containerRef={containerRef}
        fromRef={solidworksRef}
        toRef={claudeRef}
        curvature={-60}
        gradientStartColor="#E4002B"
        gradientStopColor="#D97757"
      />
      <AnimatedBeam
        containerRef={containerRef}
        fromRef={kicadRef}
        toRef={claudeRef}
        curvature={-25}
        gradientStartColor="#314CB0"
        gradientStopColor="#D97757"
      />
      <AnimatedBeam
        containerRef={containerRef}
        fromRef={blenderRef}
        toRef={claudeRef}
        gradientStartColor="#E87D0D"
        gradientStopColor="#D97757"
      />
      <AnimatedBeam
        containerRef={containerRef}
        fromRef={raspberryPiRef}
        toRef={claudeRef}
        curvature={25}
        gradientStartColor="#C51A4A"
        gradientStopColor="#D97757"
      />
      <AnimatedBeam
        containerRef={containerRef}
        fromRef={arduinoRef}
        toRef={claudeRef}
        curvature={60}
        gradientStartColor="#00979D"
        gradientStopColor="#D97757"
      />

      {/* Claude -> output */}
      <AnimatedBeam
        containerRef={containerRef}
        fromRef={claudeRef}
        toRef={outputRef}
        gradientStartColor="#D97757"
        gradientStopColor="#E8A87C"
      />
    </div>
  );
}
