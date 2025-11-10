'use client';

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api";

type AccountOption = {
  id: string;
  name: string;
};

type ReportRow = {
  id: string;
  ad_account_id: string;
  date: string;
  spend: string;
  leads_count: number;
  note: string | null;
  created_at: string;
};

interface DailyReportsClientProps {
  accounts: AccountOption[];
  initialReports: ReportRow[];
  currentUserId: string;
  accessToken: string | null;
}

type FormState = {
  ad_account_id: string;
  date: string;
  spend: string;
  leads_count: string;
  note: string;
};

const defaultFormState = (accounts: AccountOption[]): FormState => ({
  ad_account_id: accounts[0]?.id ?? "",
  date: new Date().toISOString().slice(0, 10),
  spend: "",
  leads_count: "",
  note: "",
});

export default function DailyReportsClient({
  accounts,
  initialReports,
  currentUserId,
  accessToken,
}: DailyReportsClientProps) {
  const router = useRouter();
  const [reports, setReports] = useState<ReportRow[]>(initialReports);
  const [formState, setFormState] = useState<FormState>(defaultFormState(accounts));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const accountMap = useMemo(() => {
    return accounts.reduce<Record<string, string>>((acc, item) => {
      acc[item.id] = item.name;
      return acc;
    }, {});
  }, [accounts]);

  const handleChange =
    (field: keyof FormState) =>
    (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
      setFormState((prev) => ({ ...prev, [field]: event.target.value }));
    };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    if (!formState.ad_account_id) {
      setErrorMessage("请选择广告账户");
      setIsSubmitting(false);
      return;
    }

    const payload = {
      ad_account_id: formState.ad_account_id,
      user_id: currentUserId,
      date: formState.date,
      spend: Number(formState.spend),
      leads_count: Number(formState.leads_count),
      note: formState.note.trim() || null,
    };

    if (Number.isNaN(payload.spend) || payload.spend < 0) {
      setErrorMessage("请输入合法的消耗金额");
      setIsSubmitting(false);
      return;
    }

    if (!Number.isInteger(payload.leads_count) || payload.leads_count < 0) {
      setErrorMessage("请输入合法的引流数量");
      setIsSubmitting(false);
      return;
    }

    try {
      if (!accessToken) {
        setErrorMessage("缺少访问令牌，请重新登录");
        setIsSubmitting(false);
        return;
      }

      const response = await apiFetch<ReportRow>("/api/ad-spend", {
        method: "POST",
        body: JSON.stringify(payload),
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      const apiError = response.error?.message;
      if (apiError) {
        setErrorMessage(apiError);
        return;
      }

      if (!response.data) {
        setErrorMessage("接口返回缺少数据");
        return;
      }

      setReports((prev) => [response.data, ...prev]);
      setFormState(defaultFormState(accounts));
      router.refresh();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "请求失败");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>日报录入</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
            <div className="flex flex-col gap-2">
              <Label htmlFor="ad-account">广告账户</Label>
              <select
                id="ad-account"
                className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                value={formState.ad_account_id}
                onChange={handleChange("ad_account_id")}
              >
                <option value="">请选择账户</option>
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="report-date">日期</Label>
              <Input
                id="report-date"
                type="date"
                value={formState.date}
                max={new Date().toISOString().slice(0, 10)}
                onChange={handleChange("date")}
              />
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="report-spend">消耗金额</Label>
              <Input
                id="report-spend"
                type="number"
                step="0.01"
                min="0"
                value={formState.spend}
                onChange={handleChange("spend")}
                placeholder="请输入消耗金额"
              />
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="report-leads">引流数量</Label>
              <Input
                id="report-leads"
                type="number"
                min="0"
                step="1"
                value={formState.leads_count}
                onChange={handleChange("leads_count")}
                placeholder="请输入引流数量"
              />
            </div>

            <div className="md:col-span-2 flex flex-col gap-2">
              <Label htmlFor="report-note">备注</Label>
              <textarea
                id="report-note"
                className="min-h-[120px] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                value={formState.note}
                onChange={handleChange("note")}
                placeholder="可选"
              />
            </div>

            {errorMessage && (
              <div className="md:col-span-2 text-sm text-destructive">
                {errorMessage}
              </div>
            )}

            <div className="md:col-span-2 flex justify-end gap-3">
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "提交中..." : "提交日报"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>最近日报</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b">
                  <th className="py-3 pr-4 font-medium">日期</th>
                  <th className="py-3 pr-4 font-medium">账户</th>
                  <th className="py-3 pr-4 font-medium">消耗</th>
                  <th className="py-3 pr-4 font-medium">引流数</th>
                  <th className="py-3 pr-4 font-medium">备注</th>
                  <th className="py-3 pr-4 font-medium">创建时间</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((report) => (
                  <tr key={report.id} className="border-b last:border-b-0">
                    <td className="py-3 pr-4">{report.date}</td>
                    <td className="py-3 pr-4">{accountMap[report.ad_account_id] ?? report.ad_account_id}</td>
                    <td className="py-3 pr-4">
                      <Badge variant="secondary">{Number(report.spend).toFixed(2)}</Badge>
                    </td>
                    <td className="py-3 pr-4">{report.leads_count}</td>
                    <td className="py-3 pr-4 text-muted-foreground">
                      {report.note ? report.note : "—"}
                    </td>
                    <td className="py-3 pr-4">{new Date(report.created_at).toLocaleString()}</td>
                  </tr>
                ))}
                {reports.length === 0 && (
                  <tr>
                    <td className="py-6 text-center text-muted-foreground" colSpan={6}>
                      暂无日报数据
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}


