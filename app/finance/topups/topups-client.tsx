'use client';

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api";

type TopupRow = {
  id: string;
  ad_account_id: string;
  project_id: string;
  channel_id: string;
  requested_by: string;
  amount: string;
  service_fee_amount: string | null;
  status: string;
  remark: string | null;
  created_by: string | null;
  updated_by: string | null;
  created_at: string;
  updated_at: string;
};

type OptionRow = {
  id: string;
  name: string;
  project_id?: string;
  channel_id?: string;
};

interface TopupsClientProps {
  accountOptions: OptionRow[];
  projectOptions: OptionRow[];
  channelOptions: OptionRow[];
  currentUserId: string;
  accessToken: string | null;
}

type Action =
  | { type: "create"; payload: Omit<TopupRow, "id" | "service_fee_amount" | "status" | "created_at" | "updated_at" | "remark" | "created_by" | "updated_by"> & { remark?: string | null } }
  | { type: "approve"; id: string; remark?: string | null }
  | { type: "pay"; id: string; remark?: string | null }
  | { type: "confirm"; id: string; remark?: string | null }
  | { type: "reject"; id: string; remark?: string | null };

type FormState = {
  ad_account_id: string;
  project_id: string;
  channel_id: string;
  amount: string;
  remark: string;
};

const defaultFormState = (): FormState => ({
  ad_account_id: "",
  project_id: "",
  channel_id: "",
  amount: "",
  remark: "",
});

const TOPUP_ACTIONS = [
  { key: "approve", label: "户管审批" },
  { key: "pay", label: "财务付款" },
  { key: "confirm", label: "户管确认到账" },
  { key: "reject", label: "驳回" },
] as const;

const statusBadgeVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  pending: "secondary",
  approved: "default",
  paid: "default",
  done: "outline",
  rejected: "destructive",
};

export default function TopupsClient({
  accountOptions,
  projectOptions,
  channelOptions,
  currentUserId,
  accessToken,
}: TopupsClientProps) {
  const router = useRouter();
  const [topups, setTopups] = useState<TopupRow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [formState, setFormState] = useState<FormState>(defaultFormState());
  const [isSubmitting, setIsSubmitting] = useState(false);

  const accountMap = useMemo(() => {
    return accountOptions.reduce<Record<string, OptionRow>>((acc, item) => {
      acc[item.id] = item;
      return acc;
    }, {});
  }, [accountOptions]);

  const projectMap = useMemo(() => {
    return projectOptions.reduce<Record<string, string>>((acc, item) => {
      acc[item.id] = item.name;
      return acc;
    }, {});
  }, [projectOptions]);

  const channelMap = useMemo(() => {
    return channelOptions.reduce<Record<string, string>>((acc, item) => {
      acc[item.id] = item.name;
      return acc;
    }, {});
  }, [channelOptions]);

  useEffect(() => {
    let ignore = false;

    async function fetchTopups() {
      if (!accessToken) {
        setErrorMessage("缺少访问令牌，请重新登录");
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      const response = await apiFetch<TopupRow[]>("/api/topups", {
        headers: accessToken
          ? {
              Authorization: `Bearer ${accessToken}`,
            }
          : undefined,
      });
      if (!ignore) {
        const apiError = response.error?.message;
        if (apiError) {
          setErrorMessage(apiError);
        } else {
          setTopups(response.data ?? []);
          setErrorMessage(null);
        }
        setIsLoading(false);
      }
    }

    fetchTopups();

    return () => {
      ignore = true;
    };
  }, [accessToken]);

  const handleFormChange =
    (field: keyof FormState) =>
    (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      setFormState((prev) => ({ ...prev, [field]: event.target.value }));
    };

  const triggerAction = async (action: Action) => {
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      if (!accessToken) {
        setErrorMessage("缺少访问令牌，请重新登录");
        return;
      }

      let response;
      switch (action.type) {
        case "create": {
          response = await apiFetch<TopupRow>("/api/topups", {
            method: "POST",
            body: JSON.stringify({
              ...action.payload,
              remark: action.payload.remark ?? null,
              project_id: action.payload.project_id,
              channel_id: action.payload.channel_id,
              requested_by: currentUserId,
              created_by: currentUserId,
            }),
            headers: accessToken
              ? {
                  Authorization: `Bearer ${accessToken}`,
                }
              : undefined,
          });
          break;
        }
        case "approve":
        case "pay":
        case "confirm":
        case "reject": {
          response = await apiFetch<TopupRow>(`/api/topups/${action.id}/${action.type}`, {
            method: "POST",
            body: JSON.stringify({
              actor_id: currentUserId,
              remark: action.remark ?? null,
            }),
            headers: accessToken
              ? {
                  Authorization: `Bearer ${accessToken}`,
                }
              : undefined,
          });
          break;
        }
        default:
          return;
      }

      const apiError = response.error?.message;
      if (apiError) {
        setErrorMessage(apiError);
        return;
      }

      if (!response.data) {
        setErrorMessage("接口返回缺少数据");
        return;
      }

      if (action.type === "create") {
        setFormState(defaultFormState());
      }

      const payload = response.data;
      setTopups((prev) => {
        const exists = prev.find((item) => item.id === payload.id);
        if (exists) {
          return prev.map((item) => (item.id === payload.id ? payload : item));
        }
        return [payload, ...prev];
      });

      router.refresh();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "请求失败");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreate = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!formState.ad_account_id || !formState.project_id || !formState.channel_id) {
      setErrorMessage("请选择账户、项目与渠道");
      return;
    }

    triggerAction({
      type: "create",
      payload: {
        ad_account_id: formState.ad_account_id,
        project_id: formState.project_id,
        channel_id: formState.channel_id,
        requested_by: currentUserId,
        amount: formState.amount,
        remark: formState.remark.trim() || null,
      },
    });
  };

  const renderActionButtons = (topup: TopupRow) => {
    return (
      <div className="flex flex-wrap gap-2 justify-end">
        {TOPUP_ACTIONS.map(({ key, label }) => {
          const isReject = key === "reject";
          const intent = isReject ? "destructive" : "outline";

          const clickable = {
            approve: topup.status === "pending",
            pay: topup.status === "approved",
            confirm: topup.status === "paid",
            reject: ["pending", "approved", "paid"].includes(topup.status),
          }[key as typeof TOPUP_ACTIONS[number]["key"]];

          if (!clickable) {
            return (
              <Button key={key} variant="ghost" size="sm" disabled>
                {label}
              </Button>
            );
          }

          return (
            <Button
              key={key}
              variant={intent}
              size="sm"
              onClick={() =>
                triggerAction({
                  type: key as Action["type"],
                  id: topup.id,
                } as Action)
              }
              disabled={isSubmitting}
            >
              {label}
            </Button>
          );
        })}
      </div>
    );
  };

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>发起充值</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="grid gap-4 md:grid-cols-2" onSubmit={handleCreate}>
            <div className="flex flex-col gap-2">
              <Label htmlFor="topup-account">广告账户</Label>
              <select
                id="topup-account"
                className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                value={formState.ad_account_id}
                onChange={handleFormChange("ad_account_id")}
              >
                <option value="">请选择账户</option>
                {accountOptions.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="topup-project">项目</Label>
              <select
                id="topup-project"
                className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                value={formState.project_id}
                onChange={handleFormChange("project_id")}
              >
                <option value="">请选择项目</option>
                {projectOptions.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="topup-channel">渠道</Label>
              <select
                id="topup-channel"
                className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                value={formState.channel_id}
                onChange={handleFormChange("channel_id")}
              >
                <option value="">请选择渠道</option>
                {channelOptions.map((channel) => (
                  <option key={channel.id} value={channel.id}>
                    {channel.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="topup-amount">充值金额</Label>
              <Input
                id="topup-amount"
                type="number"
                min="0"
                step="0.01"
                value={formState.amount}
                onChange={handleFormChange("amount")}
                placeholder="请输入充值金额"
              />
            </div>

            <div className="md:col-span-2 flex flex-col gap-2">
              <Label htmlFor="topup-remark">备注</Label>
              <textarea
                id="topup-remark"
                className="min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                value={formState.remark}
                onChange={handleFormChange("remark")}
                placeholder="可选"
              />
            </div>

            {errorMessage && (
              <div className="md:col-span-2 text-sm text-destructive">{errorMessage}</div>
            )}

            <div className="md:col-span-2 flex justify-end">
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "提交中..." : "发起充值"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>充值审批流</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">加载中...</p>
          ) : topups.length === 0 ? (
            <p className="text-sm text-muted-foreground">暂无充值记录</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="py-3 pr-4 font-medium">账户</th>
                    <th className="py-3 pr-4 font-medium">项目</th>
                    <th className="py-3 pr-4 font-medium">渠道</th>
                    <th className="py-3 pr-4 font-medium">金额 / 手续费</th>
                    <th className="py-3 pr-4 font-medium">状态</th>
                    <th className="py-3 pr-4 font-medium">备注</th>
                    <th className="py-3 pr-4 font-medium">更新时间</th>
                    <th className="py-3 pr-4 font-medium text-right">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {topups.map((topup) => (
                    <tr key={topup.id} className="border-b last:border-b-0">
                      <td className="py-3 pr-4">{accountMap[topup.ad_account_id]?.name ?? topup.ad_account_id}</td>
                      <td className="py-3 pr-4">{projectMap[topup.project_id] ?? topup.project_id}</td>
                      <td className="py-3 pr-4">{channelMap[topup.channel_id] ?? topup.channel_id}</td>
                      <td className="py-3 pr-4">
                        <div className="flex flex-col gap-1">
                          <span>{Number(topup.amount).toFixed(2)}</span>
                          <span className="text-xs text-muted-foreground">
                            手续费：{Number(topup.service_fee_amount ?? 0).toFixed(2)}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 pr-4">
                        <Badge variant={statusBadgeVariant[topup.status] ?? "secondary"}>{topup.status}</Badge>
                      </td>
                      <td className="py-3 pr-4 text-muted-foreground">{topup.remark ?? "—"}</td>
                      <td className="py-3 pr-4">{new Date(topup.updated_at ?? topup.created_at).toLocaleString()}</td>
                      <td className="py-3 pr-0">{renderActionButtons(topup)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}


