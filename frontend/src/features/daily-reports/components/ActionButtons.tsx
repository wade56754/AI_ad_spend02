/**
 * Daily Report Action Buttons Component
 *
 * Displays available actions for a daily report based on current status
 * SoT: STATE_MACHINE.md v2.6 § 8 (8-state machine)
 */

'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  MoreHorizontal,
  Send,
  Check,
  AlertTriangle,
  Shield,
  FileCheck,
  Lock,
  Loader2,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useDailyReportActions, getAvailableActions } from '../hooks/useDailyReportActions';
import type { DailyReport, DailyReportStatus } from '../types';
import { FlagTrendDialog } from './FlagTrendDialog';
import { ResolveFlagDialog } from './ResolveFlagDialog';
import { ConfirmFinalDialog } from './ConfirmFinalDialog';

interface ActionButtonsProps {
  report: DailyReport;
  variant?: 'dropdown' | 'inline' | 'compact';
  userRole?: string;
  onActionComplete?: () => void;
  className?: string;
}

/**
 * Icon mapping for actions
 */
const ACTION_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  submit_for_trend: Send,
  approve_trend: Check,
  flag_trend: AlertTriangle,
  resolve_flag: Shield,
  submit_for_final: FileCheck,
  confirm_final: Check,
  lock: Lock,
};

/**
 * Button variant mapping
 */
const ACTION_BUTTON_VARIANTS: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  default: 'outline',
  success: 'default',
  warning: 'secondary',
  destructive: 'destructive',
};

export function ActionButtons({
  report,
  variant = 'dropdown',
  userRole = 'admin',
  onActionComplete,
  className,
}: ActionButtonsProps) {
  const actions = useDailyReportActions();
  const availableActions = getAvailableActions(report.status);

  // Dialog states
  const [flagDialogOpen, setFlagDialogOpen] = useState(false);
  const [resolveDialogOpen, setResolveDialogOpen] = useState(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);

  // Filter actions by user role
  const filteredActions = availableActions.filter((action) =>
    action.allowedRoles.includes(userRole) || action.allowedRoles.includes('admin')
  );

  if (filteredActions.length === 0) {
    return null;
  }

  const handleAction = async (actionName: string) => {
    // Check if action requires dialog
    if (actionName === 'flag_trend') {
      setFlagDialogOpen(true);
      return;
    }
    if (actionName === 'resolve_flag') {
      setResolveDialogOpen(true);
      return;
    }
    if (actionName === 'confirm_final') {
      setConfirmDialogOpen(true);
      return;
    }

    // Execute simple actions directly
    try {
      await actions.executeAction(actionName, report.id);
      onActionComplete?.();
    } catch {
      // Error is handled by the mutation
    }
  };

  // Dropdown variant
  if (variant === 'dropdown') {
    return (
      <>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className={cn('h-8 w-8', className)}
              disabled={actions.isLoading}
            >
              {actions.isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <MoreHorizontal className="h-4 w-4" />
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            {filteredActions.map((action, index) => {
              const Icon = ACTION_ICONS[action.action];
              return (
                <DropdownMenuItem
                  key={action.action}
                  onClick={() => handleAction(action.action)}
                  className={cn(
                    action.variant === 'destructive' && 'text-red-600',
                    action.variant === 'warning' && 'text-amber-600',
                    action.variant === 'success' && 'text-green-600'
                  )}
                >
                  {Icon && <Icon className="mr-2 h-4 w-4" />}
                  {action.label}
                </DropdownMenuItem>
              );
            })}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Dialogs */}
        <FlagTrendDialog
          open={flagDialogOpen}
          onOpenChange={setFlagDialogOpen}
          reportId={report.id}
          onSuccess={onActionComplete}
        />
        <ResolveFlagDialog
          open={resolveDialogOpen}
          onOpenChange={setResolveDialogOpen}
          reportId={report.id}
          onSuccess={onActionComplete}
        />
        <ConfirmFinalDialog
          open={confirmDialogOpen}
          onOpenChange={setConfirmDialogOpen}
          report={report}
          onSuccess={onActionComplete}
        />
      </>
    );
  }

  // Inline variant - shows all buttons
  if (variant === 'inline') {
    return (
      <>
        <div className={cn('flex items-center gap-2', className)}>
          {filteredActions.map((action) => {
            const Icon = ACTION_ICONS[action.action];
            return (
              <TooltipProvider key={action.action}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant={ACTION_BUTTON_VARIANTS[action.variant]}
                      size="sm"
                      onClick={() => handleAction(action.action)}
                      disabled={actions.isLoading}
                    >
                      {actions.isLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      ) : Icon ? (
                        <Icon className="h-4 w-4 mr-2" />
                      ) : null}
                      {action.label}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{action.description}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            );
          })}
        </div>

        {/* Dialogs */}
        <FlagTrendDialog
          open={flagDialogOpen}
          onOpenChange={setFlagDialogOpen}
          reportId={report.id}
          onSuccess={onActionComplete}
        />
        <ResolveFlagDialog
          open={resolveDialogOpen}
          onOpenChange={setResolveDialogOpen}
          reportId={report.id}
          onSuccess={onActionComplete}
        />
        <ConfirmFinalDialog
          open={confirmDialogOpen}
          onOpenChange={setConfirmDialogOpen}
          report={report}
          onSuccess={onActionComplete}
        />
      </>
    );
  }

  // Compact variant - icon buttons only
  return (
    <>
      <div className={cn('flex items-center gap-1', className)}>
        {filteredActions.slice(0, 2).map((action) => {
          const Icon = ACTION_ICONS[action.action];
          return (
            <TooltipProvider key={action.action}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => handleAction(action.action)}
                    disabled={actions.isLoading}
                  >
                    {actions.isLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : Icon ? (
                      <Icon className="h-4 w-4" />
                    ) : null}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{action.label}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          );
        })}
        {filteredActions.length > 2 && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {filteredActions.slice(2).map((action) => {
                const Icon = ACTION_ICONS[action.action];
                return (
                  <DropdownMenuItem
                    key={action.action}
                    onClick={() => handleAction(action.action)}
                  >
                    {Icon && <Icon className="mr-2 h-4 w-4" />}
                    {action.label}
                  </DropdownMenuItem>
                );
              })}
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>

      {/* Dialogs */}
      <FlagTrendDialog
        open={flagDialogOpen}
        onOpenChange={setFlagDialogOpen}
        reportId={report.id}
        onSuccess={onActionComplete}
      />
      <ResolveFlagDialog
        open={resolveDialogOpen}
        onOpenChange={setResolveDialogOpen}
        reportId={report.id}
        onSuccess={onActionComplete}
      />
      <ConfirmFinalDialog
        open={confirmDialogOpen}
        onOpenChange={setConfirmDialogOpen}
        report={report}
        onSuccess={onActionComplete}
      />
    </>
  );
}

export default ActionButtons;
