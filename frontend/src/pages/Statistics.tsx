import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Box, ShieldCheck, Sparkles, Wallet, Wrench } from "lucide-react";
import { ChartCard, PageHeader, StatCard } from "../components/ui";
import { useStore } from "../store";
const colors = ["#16A361", "#8bd4aa", "#639ee7", "#ffca6c", "#f8a072", "#dfe7e2"];
export default function Statistics() {
  const data = useStore((s) => s.data)!;
  const stats = data.stats;
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  return (
    <main className="page">
      <PageHeader title="数据统计" description="从数据看见生活，科学照顾每一件物品。" />
      <div className="stats-grid five">
        <StatCard label="物品总数" value={stats.itemCount} icon={Box} suffix="件" />
        <StatCard
          label="保修覆盖率"
          value={stats.warrantyCoverage}
          icon={ShieldCheck}
          suffix="%"
          note={`${stats.warrantyCount} / ${stats.itemCount} 件在保`}
        />
        <StatCard
          label="年度维护次数"
          value={stats.annualMaintenance}
          icon={Wrench}
          tone="orange"
          suffix="次"
        />
        <StatCard
          label="年度维修支出"
          value={stats.repairSpend}
          icon={Wallet}
          tone="blue"
          suffix="元"
        />
        <StatCard
          label="年度耗材支出"
          value={stats.consumableSpend}
          icon={Box}
          tone="purple"
          suffix="元"
        />
      </div>
      <div className="statistics-grid">
        <ChartCard title="物品分类分布" note={`共 ${stats.itemCount} 件`}>
          <div className="category-chart">
            <ResponsiveContainer width="52%" height={240}>
              <PieChart>
                <Pie
                  data={stats.categories}
                  dataKey="value"
                  nameKey="name"
                  innerRadius="58%"
                  outerRadius="88%"
                  paddingAngle={2}
                  isAnimationActive={!reduced}
                  animationDuration={650}
                >
                  {stats.categories.map((_, i) => (
                    <Cell key={i} fill={colors[i % colors.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="chart-legend">
              {stats.categories.map((c, i) => (
                <div key={c.name}>
                  <span style={{ background: colors[i % colors.length] }} />
                  {c.name}
                  <b>{c.value}</b>
                  <small>
                    {stats.itemCount ? ((c.value / stats.itemCount) * 100).toFixed(1) : 0}%
                  </small>
                </div>
              ))}
            </div>
          </div>
        </ChartCard>
        <ChartCard title="每月提醒趋势" note="当年提醒与已完成数量">
          <ResponsiveContainer width="100%" height={240}>
            <ComposedChart data={stats.reminderTrend}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="month" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar
                dataKey="count"
                name="提醒数"
                fill="#9ad9b5"
                radius={[4, 4, 0, 0]}
                isAnimationActive={!reduced}
                animationDuration={650}
              />
              <Line
                dataKey="completed"
                name="已处理"
                stroke="#118B50"
                strokeWidth={2}
                isAnimationActive={!reduced}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </ChartCard>
        <div className="statistics-side">
          <ChartCard title="维护频率排行" note="当年 · 次">
            <div className="ranking">
              {stats.maintenanceRanking.map((r, i) => (
                <div key={r.name}>
                  <span>{r.name}</span>
                  <div>
                    <i
                      style={{
                        width: `${(r.count / Math.max(...stats.maintenanceRanking.map((v) => v.count), 1)) * 100}%`,
                        background: colors[Math.min(i, 1)],
                      }}
                    />
                  </div>
                  <b>{r.count}</b>
                </div>
              ))}
              {!stats.maintenanceRanking.length && <p>今年尚未记录维护。</p>}
            </div>
          </ChartCard>
          <section className="panel insights">
            <h3>
              <Sparkles size={21} />
              AI 洞察
            </h3>
            <p>基于档案数据生成的规则洞察</p>
            {stats.insights.map((s, i) => (
              <div className={["green", "orange", "purple"][i % 3]} key={s}>
                <Sparkles size={20} />
                <span>{s}</span>
              </div>
            ))}
          </section>
        </div>
        <ChartCard title="保修到期分布" note="按当前日期计算">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={stats.warrantyDistribution}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar
                dataKey="count"
                name="物品数"
                fill="#86cea4"
                radius={[4, 4, 0, 0]}
                isAnimationActive={!reduced}
                animationDuration={650}
              >
                {stats.warrantyDistribution.map((_, i) => (
                  <Cell key={i} fill={i === 0 ? "#f8a072" : i === 1 ? "#ffca6c" : "#8bd4aa"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="耗材支出趋势" note="实际补货记录 · 元">
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={stats.consumableTrend}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Area
                dataKey="cost"
                name="耗材支出"
                stroke="#8762d5"
                fill="#f1eafa"
                strokeWidth={2}
                isAnimationActive={!reduced}
                animationDuration={650}
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
      <p className="data-footnote">
        所有统计来自同一 SQLite 数据库，不展示没有记录支持的增长率或用户平均值。
      </p>
    </main>
  );
}
