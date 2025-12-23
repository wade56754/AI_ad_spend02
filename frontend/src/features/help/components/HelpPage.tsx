'use client';

/**
 * Help Center Page Component
 *
 * Route: /help
 * Purpose: Display help documentation, FAQs, and support resources
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  HelpCircle,
  Search,
  Book,
  FileText,
  MessageCircle,
  Mail,
  Phone,
  ChevronRight,
  ChevronDown,
  ExternalLink,
  Lightbulb,
  Shield,
  CreditCard,
  BarChart2,
  Users,
  Settings
} from 'lucide-react';

// Help categories
const helpCategories = [
  {
    id: 'getting-started',
    name: '快速入门',
    description: '了解系统基础功能',
    icon: Lightbulb,
    articles: [
      { id: 1, title: '系统概览', description: '了解 AI 广告投放管理系统的核心功能' },
      { id: 2, title: '首次登录指南', description: '账户设置和初始配置' },
      { id: 3, title: '界面导航', description: '快速熟悉系统界面布局' },
    ],
  },
  {
    id: 'daily-reports',
    name: '日报管理',
    description: '日报提交和审核流程',
    icon: BarChart2,
    articles: [
      { id: 4, title: '日报提交流程', description: '如何正确提交每日投放数据' },
      { id: 5, title: '日报审核说明', description: '了解日报的审核状态和流程' },
      { id: 6, title: '数据异常处理', description: '发现数据异常时的处理方法' },
    ],
  },
  {
    id: 'finance',
    name: '财务管理',
    description: '充值和结算相关',
    icon: CreditCard,
    articles: [
      { id: 7, title: '充值申请流程', description: '如何提交充值申请' },
      { id: 8, title: '对账管理', description: '账户对账操作指南' },
      { id: 9, title: '结算周期说明', description: '了解结算规则和周期' },
    ],
  },
  {
    id: 'account',
    name: '账户管理',
    description: '广告账户相关操作',
    icon: Users,
    articles: [
      { id: 10, title: '账户添加', description: '如何添加新的广告账户' },
      { id: 11, title: '账户授权', description: '账户权限配置说明' },
      { id: 12, title: '账户状态', description: '了解账户的各种状态' },
    ],
  },
  {
    id: 'security',
    name: '安全设置',
    description: '账户安全相关',
    icon: Shield,
    articles: [
      { id: 13, title: '密码管理', description: '如何修改和重置密码' },
      { id: 14, title: '双因素认证', description: '启用双因素认证保护账户' },
      { id: 15, title: '会话管理', description: '管理登录会话和设备' },
    ],
  },
  {
    id: 'settings',
    name: '系统设置',
    description: '系统配置和偏好',
    icon: Settings,
    articles: [
      { id: 16, title: '通知设置', description: '配置系统通知偏好' },
      { id: 17, title: '数据导出', description: '如何导出系统数据' },
      { id: 18, title: '集成配置', description: '第三方平台集成设置' },
    ],
  },
];

// FAQ data
const faqs = [
  {
    id: 1,
    question: '如何重置密码？',
    answer: '您可以在登录页面点击"忘记密码"链接，系统会发送重置密码的邮件到您的注册邮箱。按照邮件中的指引即可完成密码重置。',
  },
  {
    id: 2,
    question: '日报提交后可以修改吗？',
    answer: '日报在"待审核"状态下可以撤回修改。一旦进入"已审核"或"已锁定"状态，则无法修改。如需修改已锁定的数据，请联系管理员。',
  },
  {
    id: 3,
    question: '充值审批需要多长时间？',
    answer: '正常情况下，充值申请会在提交后的2个工作日内完成审批。如有特殊情况，财务人员会通过系统消息通知您。',
  },
  {
    id: 4,
    question: '如何查看账户余额？',
    answer: '您可以在"广告账号管理"页面查看每个广告账户的余额信息。账户余额通过系统自动计算，基于充值金额和消耗数据。',
  },
  {
    id: 5,
    question: '数据报表可以导出吗？',
    answer: '是的，系统支持数据导出功能。在各个报表页面，您可以点击"导出"按钮，选择需要的格式（Excel或CSV）进行导出。',
  },
];

export function HelpPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const toggleFaq = (id: number) => {
    setExpandedFaq(expandedFaq === id ? null : id);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-100">
            <HelpCircle className="h-6 w-6 text-purple-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">帮助中心</h1>
            <p className="text-sm text-gray-500">查找文档、常见问题和联系支持</p>
          </div>
        </div>
      </div>

      {/* Search Section */}
      <Card className="bg-gradient-to-r from-purple-500 to-indigo-600 text-white border-0">
        <CardContent className="pt-8 pb-8">
          <div className="text-center max-w-xl mx-auto">
            <h2 className="text-2xl font-bold mb-2">有什么可以帮助您的？</h2>
            <p className="text-purple-100 mb-6">搜索帮助文档或浏览下方常见问题</p>
            <div className="relative">
              <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
              <Input
                placeholder="搜索帮助文档..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-12 h-12 text-gray-900 bg-white border-0"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Help Categories */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">帮助分类</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {helpCategories.map((category) => {
            const Icon = category.icon;
            const isExpanded = selectedCategory === category.id;
            return (
              <Card
                key={category.id}
                className={`cursor-pointer transition-all hover:shadow-md ${
                  isExpanded ? 'ring-2 ring-purple-500' : ''
                }`}
                onClick={() => setSelectedCategory(isExpanded ? null : category.id)}
              >
                <CardContent className="pt-6">
                  <div className="flex items-start gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100">
                      <Icon className="h-5 w-5 text-purple-600" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold text-gray-900">{category.name}</h3>
                        <ChevronRight
                          className={`h-5 w-5 text-gray-400 transition-transform ${
                            isExpanded ? 'rotate-90' : ''
                          }`}
                        />
                      </div>
                      <p className="text-sm text-gray-500 mt-1">{category.description}</p>
                    </div>
                  </div>

                  {/* Expanded Articles */}
                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t space-y-2">
                      {category.articles.map((article) => (
                        <button
                          key={article.id}
                          className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 text-left"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <FileText className="h-4 w-4 text-gray-400" />
                          <div>
                            <p className="text-sm font-medium text-gray-900">{article.title}</p>
                            <p className="text-xs text-gray-500">{article.description}</p>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* FAQ Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="h-5 w-5" />
            常见问题
          </CardTitle>
          <CardDescription>快速找到常见问题的答案</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {faqs.map((faq) => (
              <div
                key={faq.id}
                className="border rounded-lg overflow-hidden"
              >
                <button
                  onClick={() => toggleFaq(faq.id)}
                  className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50"
                >
                  <span className="font-medium text-gray-900">{faq.question}</span>
                  <ChevronDown
                    className={`h-5 w-5 text-gray-400 transition-transform ${
                      expandedFaq === faq.id ? 'rotate-180' : ''
                    }`}
                  />
                </button>
                {expandedFaq === faq.id && (
                  <div className="px-4 pb-4 text-gray-600">
                    {faq.answer}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Contact Support */}
      <Card>
        <CardHeader>
          <CardTitle>需要更多帮助？</CardTitle>
          <CardDescription>如果您没有找到答案，请联系我们的支持团队</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center gap-4 p-4 border rounded-lg">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
                <Mail className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">邮件支持</p>
                <p className="text-sm text-gray-500">support@example.com</p>
              </div>
            </div>
            <div className="flex items-center gap-4 p-4 border rounded-lg">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
                <Phone className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">电话支持</p>
                <p className="text-sm text-gray-500">400-888-8888</p>
              </div>
            </div>
            <div className="flex items-center gap-4 p-4 border rounded-lg">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-100">
                <Book className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">在线文档</p>
                <a href="#" className="text-sm text-purple-600 hover:underline flex items-center gap-1">
                  查看完整文档 <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default HelpPage;
