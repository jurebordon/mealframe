'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  ComposedChart,
  Bar,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { TrendingUp, Flame, Award, CalendarOff, Loader2 } from 'lucide-react'
import { useStats } from '@/hooks/use-stats'

type TimePeriod = 7 | 30 | 90

const STATUS_COLORS: Record<string, string> = {
  Followed: 'oklch(0.68 0.13 150)',
  Adjusted: 'oklch(0.68 0.14 55)',
  Skipped: 'oklch(0.28 0.02 45)',
  Replaced: 'oklch(0.62 0.01 60)',
  Social: 'oklch(0.72 0.16 70)',
}

export default function StatsPage() {
  const [timePeriod, setTimePeriod] = useState<TimePeriod>(30)
  const { data: stats, isLoading, isError } = useStats(timePeriod)

  const adherencePercent = stats
    ? Math.round(parseFloat(stats.adherence_rate) * 100)
    : 0

  // Transform daily_adherence into chart data with 7-day rolling average
  const chartData = (stats?.daily_adherence ?? []).map((day, index, arr) => {
    const rate = Math.round(parseFloat(day.adherence_rate) * 100)
    const startIdx = Math.max(0, index - 6)
    const slice = arr.slice(startIdx, index + 1)
    const avg = Math.round(
      slice.reduce((sum, d) => sum + parseFloat(d.adherence_rate) * 100, 0) /
        slice.length
    )
    // Format date label based on period
    const d = new Date(day.date + 'T00:00:00')
    const label =
      timePeriod <= 7
        ? d.toLocaleDateString('en-US', { weekday: 'short' })
        : d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    return { label, rate, average: avg }
  })

  // Build completion status pie data from by_status
  const completionData = stats
    ? [
        { name: 'Followed', value: stats.by_status.followed, color: STATUS_COLORS.Followed },
        { name: 'Adjusted', value: stats.by_status.adjusted, color: STATUS_COLORS.Adjusted },
        { name: 'Skipped', value: stats.by_status.skipped, color: STATUS_COLORS.Skipped },
        { name: 'Replaced', value: stats.by_status.replaced, color: STATUS_COLORS.Replaced },
        { name: 'Social', value: stats.by_status.social, color: STATUS_COLORS.Social },
      ].filter((d) => d.value > 0)
    : []

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto max-w-5xl px-4 py-6">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h1 className="text-pretty text-lg font-bold text-foreground sm:text-xl md:text-2xl">
              Your Progress
            </h1>
          </div>

          {/* Time Period Selector */}
          <div className="flex gap-2">
            {([7, 30, 90] as const).map((period) => (
              <Button
                key={period}
                variant={timePeriod === period ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTimePeriod(period)}
              >
                {period} days
              </Button>
            ))}
          </div>
        </div>
      </header>

      <main className="container mx-auto max-w-5xl px-4 py-8">
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        )}

        {isError && (
          <div className="rounded-xl border border-border bg-card p-6 text-center">
            <p className="text-sm text-muted-foreground">
              Failed to load statistics. Please try again later.
            </p>
          </div>
        )}

        {stats && (
          <>
            {/* Overview Cards */}
            <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardContent className="p-6">
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">Adherence Rate</p>
                    <TrendingUp className="h-4 w-4 text-success" />
                  </div>
                  <p className="text-3xl font-bold text-foreground">
                    {adherencePercent}%
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {stats.completed_slots} of {stats.total_slots} tracked
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">Current Streak</p>
                    <Flame className="h-4 w-4 text-warning" />
                  </div>
                  <p className="text-3xl font-bold text-foreground">
                    {stats.current_streak} {stats.current_streak === 1 ? 'day' : 'days'}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {stats.current_streak > 0 ? 'Keep it going!' : 'Start today!'}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">Best Streak</p>
                    <Award className="h-4 w-4 text-primary" />
                  </div>
                  <p className="text-3xl font-bold text-foreground">
                    {stats.best_streak} {stats.best_streak === 1 ? 'day' : 'days'}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Personal record
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">Override Days</p>
                    <CalendarOff className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <p className="text-3xl font-bold text-foreground">
                    {stats.override_days}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    No-plan days
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Adherence Chart */}
            {chartData.length > 0 && (
              <Card className="mb-8">
                <CardHeader>
                  <CardTitle>Daily Adherence</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <ComposedChart data={chartData}>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="oklch(0.32 0.025 45)"
                      />
                      <XAxis
                        dataKey="label"
                        stroke="oklch(0.62 0.01 60)"
                        fontSize={12}
                        tickLine={false}
                        interval={timePeriod >= 90 ? 6 : timePeriod >= 30 ? 2 : 0}
                      />
                      <YAxis
                        stroke="oklch(0.62 0.01 60)"
                        fontSize={12}
                        tickLine={false}
                        domain={[0, 100]}
                        ticks={[0, 25, 50, 75, 100]}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'oklch(0.22 0.018 40)',
                          border: '1px solid oklch(0.32 0.025 45)',
                          borderRadius: '8px',
                        }}
                        itemStyle={{ color: 'oklch(0.95 0.008 85)' }}
                        labelStyle={{ color: 'oklch(0.95 0.008 85)' }}
                        formatter={(value: number, name: string) => {
                          if (name === 'rate') return [`${value}%`, 'Daily']
                          if (name === 'average') return [`${value}%`, '7-day Avg']
                          return [value, name]
                        }}
                      />
                      <Bar
                        dataKey="rate"
                        fill="oklch(0.72 0.16 70)"
                        radius={[4, 4, 0, 0]}
                      />
                      <Line
                        type="monotone"
                        dataKey="average"
                        stroke="oklch(0.68 0.13 150)"
                        strokeWidth={2}
                        dot={false}
                        name="7-day Average"
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            )}

            <div className="mb-8 grid gap-8 lg:grid-cols-2">
              {/* By Meal Type Breakdown */}
              {stats.by_meal_type.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>By Meal Type</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      Sorted by adherence (lowest first)
                    </p>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {stats.by_meal_type.map((mt) => {
                        const rate = Math.round(
                          parseFloat(mt.adherence_rate) * 100
                        )
                        return (
                          <div key={mt.meal_type_id}>
                            <div className="mb-2 flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-foreground">
                                  {mt.name}
                                </span>
                                {rate < 80 && (
                                  <span className="rounded-full bg-warning/20 px-2 py-0.5 text-xs text-warning">
                                    Focus area
                                  </span>
                                )}
                              </div>
                              <span className="text-sm font-semibold text-foreground">
                                {rate}%
                              </span>
                            </div>
                            <div className="relative h-2 w-full overflow-hidden rounded-full bg-muted">
                              <div
                                className="h-full rounded-full transition-all"
                                style={{
                                  width: `${rate}%`,
                                  backgroundColor:
                                    rate >= 90
                                      ? 'oklch(0.68 0.13 150)'
                                      : rate >= 80
                                        ? 'oklch(0.72 0.16 70)'
                                        : 'oklch(0.68 0.14 55)',
                                }}
                              />
                            </div>
                            <p className="mt-1 text-xs text-muted-foreground">
                              {mt.followed} of {mt.total} followed
                            </p>
                          </div>
                        )
                      })}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Completion Status Breakdown */}
              {completionData.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Completion Status</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      How you completed meals
                    </p>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={280}>
                      <PieChart>
                        <Pie
                          data={completionData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          outerRadius={90}
                          fill="#8884d8"
                          dataKey="value"
                          label={false}
                          stroke="oklch(0.22 0.018 40)"
                          strokeWidth={2}
                        >
                          {completionData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'oklch(0.22 0.018 40)',
                            border: '1px solid oklch(0.32 0.025 45)',
                            borderRadius: '8px',
                          }}
                          itemStyle={{ color: 'oklch(0.95 0.008 85)' }}
                          labelStyle={{ color: 'oklch(0.95 0.008 85)' }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
                      {completionData.map((status) => (
                        <div
                          key={status.name}
                          className="flex items-center gap-2"
                        >
                          <div
                            className="h-3 w-3 rounded-sm"
                            style={{ backgroundColor: status.color }}
                          />
                          <span className="text-muted-foreground">
                            {status.name}: {status.value}
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Empty State */}
            {stats.total_slots === 0 && (
              <Card>
                <CardContent className="p-8 text-center">
                  <p className="text-muted-foreground">
                    No meal data for this period. Generate a weekly plan and start
                    tracking your meals to see statistics here.
                  </p>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </main>
    </div>
  )
}
