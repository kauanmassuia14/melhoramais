"use client";

import { useEffect, useRef, useCallback } from "react";

interface BorderBeamProps {
  size?: number;
  duration?: number;
  colorFrom?: string;
  colorTo?: string;
  className?: string;
  reverse?: boolean;
}

export function BorderBeam({
  size = 200,
  duration = 15,
  colorFrom = "#06b6d4",
  colorTo = "#8b5cf6",
  className = "",
  reverse = false,
}: BorderBeamProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const parent = canvas.parentElement;
    if (!parent) return;

    const w = parent.offsetWidth;
    const h = parent.offsetHeight;
    canvas.width = w;
    canvas.height = h;

    const perimeter = 2 * (w + h);
    const speed = perimeter / (duration * 60);

    let offset = 0;

    function animate() {
      if (!ctx || !canvas) return;
      ctx.clearRect(0, 0, w, h);

      if (reverse) {
        offset -= speed;
      } else {
        offset += speed;
      }
      if (offset > perimeter) offset -= perimeter;
      if (offset < 0) offset += perimeter;

      const grad = ctx.createLinearGradient(0, 0, w, h);
      grad.addColorStop(0, colorFrom);
      grad.addColorStop(1, colorTo);

      ctx.strokeStyle = grad;
      ctx.lineWidth = 1.5;
      ctx.shadowColor = colorFrom;
      ctx.shadowBlur = 8;
      ctx.beginPath();

      // Draw beam segment along the perimeter
      const beamLength = size;
      const start = offset;
      const end = offset + beamLength;

      for (let i = start; i < end; i += 1) {
        const pos = i % perimeter;
        const { x, y } = perimeterPoint(pos, w, h);
        if (i === start) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }

      ctx.stroke();
      requestAnimationFrame(animate);
    }

    animate();
  }, [size, duration, colorFrom, colorTo, reverse]);

  useEffect(() => {
    draw();
    const handleResize = () => draw();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [draw]);

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 pointer-events-none ${className}`}
      style={{ zIndex: 1 }}
    />
  );
}

function perimeterPoint(
  pos: number,
  w: number,
  h: number
): { x: number; y: number } {
  const perimeter = 2 * (w + h);
  const p = ((pos % perimeter) + perimeter) % perimeter;

  if (p < w) return { x: p, y: 0 };
  if (p < w + h) return { x: w, y: p - w };
  if (p < 2 * w + h) return { x: w - (p - w - h), y: h };
  return { x: 0, y: h - (p - 2 * w - h) };
}
