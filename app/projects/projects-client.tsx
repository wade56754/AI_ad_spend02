'use client';

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api";

type ProjectRow = {
  id: string;
  name: string;
  client_name: string | null;
  currency: string;
  status: string;
  created_by: string | null;
  updated_by: string | null;
  created_at: string;
  updated_at: string;
};

interface ProjectsClientProps {
  initialProjects: ProjectRow[];
  currentUserId: string | null;
  accessToken: string | null;
}

type FormState = {
  name: string;
  client_name: string;
  currency: string;
  status: string;
};

const defaultFormState: FormState = {
  name: "",
  client_name: "",
  currency: "USD",
  status: "active",
};

export default function ProjectsClient({ initialProjects, currentUserId, accessToken }: ProjectsClientProps) {
  const router = useRouter();
  const [projects, setProjects] = useState<ProjectRow[]>(initialProjects);
  const [modalOpen, setModalOpen] = useState(false);
  const [formState, setFormState] = useState<FormState>(defaultFormState);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const modalTitle = editingId ? "编辑项目" : "新增项目";

  const sortedProjects = useMemo(
    () => [...projects].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()),
    [projects],
  );

  const openCreateModal = () => {
    setFormState(defaultFormState);
    setEditingId(null);
    setErrorMessage(null);
    setModalOpen(true);
  };

  const openEditModal = (project: ProjectRow) => {
    setFormState({
      name: project.name,
      client_name: project.client_name ?? "",
      currency: project.currency,
      status: project.status,
    });
    setEditingId(project.id);
    setErrorMessage(null);
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingId(null);
    setErrorMessage(null);
  };

  const handleChange = (field: keyof FormState) => (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormState((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    const payload: Record<string, unknown> = {
      name: formState.name.trim(),
      client_name: formState.client_name.trim() || null,
      currency: formState.currency,
      status: formState.status,
    };

    if (!payload.name) {
      setErrorMessage("项目名称不能为空");
      setIsSubmitting(false);
      return;
    }

    try {
      if (!accessToken) {
        setErrorMessage("缺少访问令牌，请重新登录");
        setIsSubmitting(false);
        return;
      }

      let response;
      if (editingId) {
        payload.updated_by = currentUserId;
        response = await apiFetch<ProjectRow>(`/api/projects/${editingId}`, {
          method: "PUT",
          body: JSON.stringify(payload),
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });
      } else {
        payload.created_by = currentUserId;
        response = await apiFetch<ProjectRow>("/api/projects", {
          method: "POST",
          body: JSON.stringify(payload),
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });
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

      const project = response.data;
      setProjects((prev) => {
        const others = prev.filter((item) => item.id !== project.id);
        return [project, ...others];
      });

      closeModal();
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
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>项目管理</CardTitle>
          <Button onClick={openCreateModal}>新增项目</Button>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b">
                  <th className="py-3 pr-4 font-medium">名称</th>
                  <th className="py-3 pr-4 font-medium">客户</th>
                  <th className="py-3 pr-4 font-medium">币种</th>
                  <th className="py-3 pr-4 font-medium">状态</th>
                  <th className="py-3 pr-4 font-medium">更新时间</th>
                  <th className="py-3 pr-4 font-medium text-right">操作</th>
                </tr>
              </thead>
              <tbody>
                {sortedProjects.map((project) => (
                  <tr key={project.id} className="border-b last:border-b-0">
                    <td className="py-3 pr-4">{project.name}</td>
                    <td className="py-3 pr-4">{project.client_name ?? "-"}</td>
                    <td className="py-3 pr-4">{project.currency}</td>
                    <td className="py-3 pr-4">
                      <Badge variant={project.status === "active" ? "default" : "secondary"}>{project.status}</Badge>
                    </td>
                    <td className="py-3 pr-4">
                      {new Date(project.updated_at ?? project.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 pr-0 text-right">
                      <Button variant="outline" size="sm" onClick={() => openEditModal(project)}>
                        编辑
                      </Button>
                    </td>
                  </tr>
                ))}
                {sortedProjects.length === 0 && (
                  <tr>
                    <td className="py-6 text-center text-muted-foreground" colSpan={6}>
                      暂无项目数据
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-lg border bg-background p-6 shadow-lg">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold">{modalTitle}</h2>
              <Button variant="ghost" size="sm" onClick={closeModal}>
                关闭
              </Button>
            </div>
            <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
              <div className="flex flex-col gap-2">
                <Label htmlFor="project-name">项目名称</Label>
                <Input
                  id="project-name"
                  value={formState.name}
                  onChange={handleChange("name")}
                  placeholder="请输入项目名称"
                  required
                />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="project-client">客户名称</Label>
                <Input
                  id="project-client"
                  value={formState.client_name}
                  onChange={handleChange("client_name")}
                  placeholder="可选"
                />
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="flex flex-col gap-2">
                  <Label htmlFor="project-currency">币种</Label>
                  <Input
                    id="project-currency"
                    value={formState.currency}
                    onChange={handleChange("currency")}
                    placeholder="USD"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <Label htmlFor="project-status">状态</Label>
                  <select
                    id="project-status"
                    className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    value={formState.status}
                    onChange={handleChange("status")}
                  >
                    <option value="active">active</option>
                    <option value="archived">archived</option>
                    <option value="paused">paused</option>
                  </select>
                </div>
              </div>

              {errorMessage && <p className="text-sm text-destructive">{errorMessage}</p>}

              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={closeModal}>
                  取消
                </Button>
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting ? "处理中..." : "保存"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}


