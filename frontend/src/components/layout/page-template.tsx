'use client';

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface PageTemplateProps {
  title: string;
  subtitle?: ReactNode;
  children: ReactNode;
  actions?: ReactNode;
  breadcrumbs?: ReactNode | BreadcrumbItem[];
  className?: string;
}

function PageTemplate({
  title,
  subtitle,
  children,
  actions,
  breadcrumbs,
  className = ''
}: PageTemplateProps) {
  return (
    <div className={cn('min-h-screen bg-gray-50 dark:bg-gray-900', className)}>
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="px-4 sm:px-6 lg:px-8 py-6">
          {/* Breadcrumbs */}
          {breadcrumbs && (
            <div className="mb-4">
              {Array.isArray(breadcrumbs) ? (
                <nav className="flex" aria-label="Breadcrumb">
                  <ol className="flex items-center space-x-2">
                    {breadcrumbs.map((item, index) => (
                      <li key={index} className="flex items-center">
                        {item.href ? (
                          <a
                            href={item.href}
                            className="text-sm font-medium text-gray-500 hover:text-gray-700 transition-colors"
                          >
                            {item.label}
                          </a>
                        ) : (
                          <span className="text-sm font-medium text-gray-900">
                            {item.label}
                          </span>
                        )}
                        {index < breadcrumbs.length - 1 && (
                          <svg
                            className="ml-2 h-4 w-4 text-gray-400"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                              clipRule="evenodd"
                            />
                          </svg>
                        )}
                      </li>
                    ))}
                  </ol>
                </nav>
              ) : (
                breadcrumbs
              )}
            </div>
          )}

          {/* Page Header */}
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white sm:text-3xl">
                {title}
              </h1>
              {subtitle && (
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                  {subtitle}
                </p>
              )}
            </div>

            {/* Actions */}
            {actions && (
              <div className="mt-4 sm:mt-0 sm:ml-6 sm:flex-shrink-0">
                {actions}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}

export { PageTemplate };
export default PageTemplate;
