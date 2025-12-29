/**
 * useAlertToast Hook
 *
 * 使用 Sonner toast 显示临时告警通知
 * 支持 critical/warning/info 三种级别
 */

import { toast } from 'sonner';
import type { Alert, AlertSeverity } from '../components/AlertBanner';

const SEVERITY_ACTIONS = {
  critical: (message: string, options?: { onClick?: () => void }) => {
    toast.error(message, {
      duration: 8000, // 严重告警显示更长时间
      action: options?.onClick
        ? {
            label: '查看',
            onClick: options.onClick,
          }
        : undefined,
    });
  },
  warning: (message: string, options?: { onClick?: () => void }) => {
    toast.warning(message, {
      duration: 5000,
      action: options?.onClick
        ? {
            label: '查看',
            onClick: options.onClick,
          }
        : undefined,
    });
  },
  info: (message: string, options?: { onClick?: () => void }) => {
    toast.info(message, {
      duration: 4000,
      action: options?.onClick
        ? {
            label: '查看',
            onClick: options.onClick,
          }
        : undefined,
    });
  },
};

/**
 * 显示告警 toast
 */
export function showAlertToast(
  severity: AlertSeverity,
  message: string,
  options?: { onClick?: () => void }
) {
  SEVERITY_ACTIONS[severity](message, options);
}

/**
 * 批量显示告警 toast
 * 仅显示高优先级告警 (critical/warning)，避免信息过载
 */
export function showAlertToasts(alerts: Alert[]) {
  // 只显示 critical 和 warning 级别的告警作为 toast
  const criticalAlerts = alerts.filter((a) => a.severity === 'critical');
  const warningAlerts = alerts.filter((a) => a.severity === 'warning');

  // 先显示 critical
  criticalAlerts.forEach((alert) => {
    const message = alert.count !== undefined
      ? `${alert.message} (${alert.count})`
      : alert.message;

    showAlertToast('critical', message, {
      onClick: alert.href
        ? () => (window.location.href = alert.href!)
        : alert.scrollTo
        ? () => {
            const element = document.getElementById(alert.scrollTo!);
            element?.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        : undefined,
    });
  });

  // 延迟显示 warning，避免同时弹出多个
  if (warningAlerts.length > 0) {
    setTimeout(() => {
      warningAlerts.forEach((alert) => {
        const message = alert.count !== undefined
          ? `${alert.message} (${alert.count})`
          : alert.message;

        showAlertToast('warning', message, {
          onClick: alert.href
            ? () => (window.location.href = alert.href!)
            : alert.scrollTo
            ? () => {
                const element = document.getElementById(alert.scrollTo!);
                element?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }
            : undefined,
        });
      });
    }, 500);
  }
}

/**
 * 显示操作成功 toast
 */
export function showSuccessToast(message: string) {
  toast.success(message, { duration: 3000 });
}

/**
 * 显示操作失败 toast
 */
export function showErrorToast(message: string) {
  toast.error(message, { duration: 5000 });
}

export default { showAlertToast, showAlertToasts, showSuccessToast, showErrorToast };
