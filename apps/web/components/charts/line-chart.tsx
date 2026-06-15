"use client";

import { useEffect, useRef } from "react";
import { createChart, IChartApi, Time } from "lightweight-charts";

interface LineChartProps {
  data: Array<{ time: string; value: number }>;
  color?: string;
  height?: number;
}

export function ChartLine({ data, color = "#ff5c35", height = 300 }: LineChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !data.length) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: { background: { color: "transparent" }, textColor: "#999" },
      grid: {
        vertLines: { color: "rgba(42, 46, 57, 0.2)" },
        horzLines: { color: "rgba(42, 46, 57, 0.2)" },
      },
      rightPriceScale: { borderColor: "rgba(42, 46, 57, 0.3)" },
      timeScale: { borderColor: "rgba(42, 46, 57, 0.3)", timeVisible: true },
    });

    const lineSeries = chart.addLineSeries({
      color,
      lineWidth: 2,
    });

    lineSeries.setData(
      data.map((d) => ({ time: d.time as Time, value: d.value }))
    );

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [data, color, height]);

  return <div ref={containerRef} className="w-full" />;
}
