import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  BarChart,
  Bar,
  Cell,
} from "recharts";
import { number } from "./ui";
import type { Analytics, Ranking } from "../types";
export function SalesChart({ data }: { data: Analytics["trends"] }) {
  return (
    <div
      className="chart"
      role="img"
      aria-label="Observed reporting-year sales in metres"
    >
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{ top: 15, right: 16, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="salesFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#4a806b" stopOpacity={0.22} />
              <stop offset="100%" stopColor="#4a806b" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid
            vertical={false}
            stroke="var(--border)"
            strokeDasharray="4 4"
          />
          <XAxis
            dataKey="year"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "var(--muted)", fontSize: 11 }}
            dy={10}
          />
          <YAxis
            tickFormatter={(v) => number(v, true)}
            axisLine={false}
            tickLine={false}
            tick={{ fill: "var(--muted)", fontSize: 11 }}
            width={54}
          />
          <Tooltip
            contentStyle={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 10,
              color: "var(--text)",
            }}
            formatter={(v) => [`${number(Number(v))} m`, "Observed sales"]}
            labelFormatter={(l) => `Reporting year ${l}`}
          />
          <Area
            isAnimationActive={false}
            type="monotone"
            dataKey="total"
            stroke="#458269"
            strokeWidth={2.5}
            fill="url(#salesFill)"
            activeDot={{ r: 5 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
export function BranchChart({ data }: { data: Ranking[] }) {
  return (
    <div
      className="chart compact"
      role="img"
      aria-label="Observed sales by branch"
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 5, right: 35 }}>
          <CartesianGrid horizontal={false} stroke="var(--border)" />
          <XAxis
            type="number"
            tickFormatter={(v) => number(v, true)}
            axisLine={false}
            tickLine={false}
            tick={{ fill: "var(--muted)", fontSize: 10 }}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={135}
            tick={{ fill: "var(--muted)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 10,
            }}
            formatter={(v) => [`${number(Number(v))} m`, "Observed sales"]}
          />
          <Bar
            isAnimationActive={false}
            dataKey="observed_current"
            radius={[0, 4, 4, 0]}
            barSize={19}
          >
            {data.map((d, i) => (
              <Cell key={d.id} fill={i === 0 ? "#27634d" : "#97b9a5"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
