'use client';

import { useMemo } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type ProjectReportRow = {
  project_id: string;
  project_name: string;
  total_spend: string;
  total_leads: number;
  net_amount: string;
  profit: string;
};

type ChannelReportRow = {
  channel_id: string;
  channel_name: string;
  total_spend: string;
  account_count: number;
  total_topup: string;
  service_fee_amount: string;
};

interface ReportsClientProps {
  month: string;
  projects: ProjectReportRow[];
  channels: ChannelReportRow[];
}

export default function ReportsClient({ month, projects, channels }: ReportsClientProps) {
  const projectChartData = useMemo(
    () =>
      projects.map((item) => ({
        name: item.project_name || "未命名项目",
        profit: Number(item.profit),
        totalSpend: Number(item.total_spend),
        netAmount: Number(item.net_amount),
        totalLeads: item.total_leads,
      })),
    [projects],
  );

  const channelChartData = useMemo(
    () =>
      channels.map((item) => ({
        name: item.channel_name || "未命名渠道",
        totalSpend: Number(item.total_spend),
        totalTopup: Number(item.total_topup),
        serviceFee: Number(item.service_fee_amount),
      })),
    [channels],
  );

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>{month} · 项目利润</CardTitle>
        </CardHeader>
        <CardContent className="h-[360px]">
          {projectChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={projectChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="profit" name="利润" fill="#22c55e" />
                <Bar dataKey="totalSpend" name="消耗" fill="#3b82f6" />
                <Bar dataKey="netAmount" name="净收入" fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-muted-foreground">暂无项目数据</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{month} · 渠道表现</CardTitle>
        </CardHeader>
        <CardContent className="h-[360px]">
          {channelChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={channelChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="totalSpend" name="渠道消耗" stroke="#3b82f6" strokeWidth={2} />
                <Line type="monotone" dataKey="totalTopup" name="充值金额" stroke="#22c55e" strokeWidth={2} />
                <Line type="monotone" dataKey="serviceFee" name="服务费" stroke="#f97316" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-muted-foreground">暂无渠道数据</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}


