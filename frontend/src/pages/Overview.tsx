import {
  ArrowRight,
  Activity,
  ChartNoAxesCombined,
  ShieldAlert,
  UsersRound,
} from "lucide-react";
import type { Analytics, Collection, Execution, Indicators } from "../types";
import { SalesChart, BranchChart } from "../components/Charts";
import { Badge, Change, date, Empty, number } from "../components/ui";
export function Overview({
  analytics,
  indicators,
  executions,
  onDetail,
  onReview,
  onSales,
}: {
  analytics: Analytics;
  indicators: Indicators;
  executions: Collection<Execution>;
  onDetail: (id: string) => void;
  onReview: () => void;
  onSales: () => void;
}) {
  const cards = [
    {
      label: "Observed sales",
      value: `${number(analytics.summary.observed_current, true)} m`,
      note: `Reporting year ${analytics.trends.at(-1)?.year}`,
      icon: ChartNoAxesCombined,
    },
    {
      label: "Analyses processed",
      value: number(indicators.executions),
      note:
        indicators.success_rate == null
          ? "Ready for your first analysis"
          : `${indicators.success_rate}% successful or awaiting review`,
      icon: Activity,
    },
    {
      label: "Critical findings",
      value: number(indicators.critical),
      note: "Persisted critical analyses",
      icon: ShieldAlert,
    },
    {
      label: "Human reviews",
      value: number(indicators.pending_reviews),
      note: "Awaiting a supervisor decision",
      icon: UsersRound,
    },
  ];
  return (
    <>
      <div className="metrics-grid">
        {cards.map((c, i) => (
          <section className={`metric-card metric-${i}`} key={c.label}>
            <div>
              <span>{c.label}</span>
              <c.icon size={19} />
            </div>
            <strong>{c.value}</strong>
            <small>{c.note}</small>
          </section>
        ))}
      </div>
      <div className="overview-grid">
        <section className="panel sales-panel">
          <div className="panel-head">
            <div>
              <h2>Sales evolution</h2>
              <p>Observed reporting-year volume · metres</p>
            </div>
            <span className="legend">
              <i /> All selected records
            </span>
          </div>
          <div className="chart-summary">
            <strong>
              {number(analytics.summary.observed_current)}
              <small> m</small>
            </strong>
            <Change value={analytics.summary.variation} />
            <span>matched pair comparison</span>
          </div>
          <SalesChart data={analytics.trends} />
          <div className="panel-foot">
            <span>
              {analytics.summary.coverage_pct}% matched coverage · no monthly
              allocation
            </span>
            <button onClick={onSales}>
              Explore analytics <ArrowRight size={14} />
            </button>
          </div>
        </section>
        <section className="panel review-callout">
          <span className="eyebrow">HUMAN IN THE LOOP</span>
          <div className="review-orbit">
            <UsersRound size={35} />
            <i />
          </div>
          <h2>
            Your judgment.
            <br />
            In the right place.
          </h2>
          <p>
            Critical recommendations stay on hold until a supervisor reviews the
            evidence.
          </p>
          <button className="button primary" onClick={onReview}>
            Review inbox{" "}
            <span className="count">{indicators.pending_reviews}</span>
            <ArrowRight size={16} />
          </button>
          <small>
            <i /> Every decision is audited
          </small>
        </section>
      </div>
      <div className="bottom-grid">
        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>Product performance</h2>
              <p>Current volume and matched change</p>
            </div>
            <button className="text-link" onClick={onSales}>
              View all <ArrowRight size={14} />
            </button>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Product / line</th>
                  <th>Observed volume</th>
                  <th>Change</th>
                  <th>Risk</th>
                </tr>
              </thead>
              <tbody>
                {analytics.products.slice(0, 5).map((p) => (
                  <tr key={p.id}>
                    <td>
                      <strong>{p.name}</strong>
                      <small>
                        {p.line} · {p.id}
                      </small>
                    </td>
                    <td>{number(p.observed_current)} m</td>
                    <td>
                      <Change value={p.variation} />
                    </td>
                    <td>
                      <Badge status={p.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>Recent activity</h2>
              <p>Real persisted agent executions</p>
            </div>
            <Activity size={17} />
          </div>
          {executions.items.length ? (
            <div className="activity-list">
              {executions.items.slice(0, 5).map((e) => (
                <button
                  key={e.ejecucion_id}
                  onClick={() => onDetail(e.ejecucion_id)}
                >
                  <span
                    className={`activity-dot ${e.business_status?.toLowerCase()}`}
                  />
                  <span>
                    <strong>{e.producto || "Analysis"}</strong>
                    <small>{date(e.fecha)}</small>
                  </span>
                  <Badge status={e.estado} />
                </button>
              ))}
            </div>
          ) : (
            <Empty title="A fresh start">
              Your first analysis will appear here with its actual graph path.
            </Empty>
          )}
        </section>
      </div>
      <section className="panel branch-panel">
        <div className="panel-head">
          <div>
            <h2>Branch overview</h2>
            <p>Observed volume by location · current reporting year</p>
          </div>
        </div>
        <BranchChart data={analytics.branches} />
      </section>
    </>
  );
}
