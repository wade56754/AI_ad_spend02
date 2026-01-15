/**
 * SupplierForm Component
 *
 * Form component for create/edit supplier
 * SoT 对齐: DATA_SCHEMA.md v5.2
 */

'use client';

import React from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import type { Supplier, SupplierCreateInput, SupplierUpdateInput } from '../types';
import { PaymentMethod, PAYMENT_METHOD_CONFIG } from '../types';

interface SupplierFormProps {
  supplier?: Supplier | null;
  onSubmit: (data: SupplierCreateInput | SupplierUpdateInput) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function SupplierForm({
  supplier,
  onSubmit,
  onCancel,
  isLoading = false,
}: SupplierFormProps) {
  const isEdit = !!supplier;

  const [formData, setFormData] = React.useState<SupplierCreateInput>({
    name: supplier?.name || '',
    contact_name: supplier?.contact_name || '',
    contact_email: supplier?.contact_email || '',
    contact_phone: supplier?.contact_phone || '',
    base_currency: supplier?.base_currency || 'USD',
    payment_method: supplier?.payment_method || PaymentMethod.BANK_TRANSFER,
    payment_terms: supplier?.payment_terms || '',
    tax_id: supplier?.tax_id || '',
    address: supplier?.address || '',
    country: supplier?.country || '',
    notes: supplier?.notes || '',
  });

  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error when field is modified
    if (errors[name]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    }
  };

  const handleSelectChange = (name: keyof SupplierCreateInput, value: string) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
    const errorKey = name as string;
    if (errors[errorKey]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[errorKey];
        return next;
      });
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = '供应商名称不能为空';
    }

    if (formData.contact_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.contact_email)) {
      newErrors.contact_email = '邮箱格式不正确';
    }

    if (formData.country && formData.country.length !== 2) {
      newErrors.country = '国家代码必须是2位字母';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      onSubmit(formData);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="fixed inset-0 bg-black/50" onClick={onCancel} />

        <div className="relative w-full max-w-2xl bg-white rounded-lg shadow-xl">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">
              {isEdit ? '编辑供应商' : '新增供应商'}
            </h2>
            <Button onClick={onCancel} variant="ghost" size="icon" className="rounded-full">
              <X className="h-5 w-5 text-gray-500" />
            </Button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-4 space-y-4">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  供应商名称 <span className="text-red-500">*</span>
                </label>
                <Input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  className={
                    errors.name
                      ? 'border-red-500 focus-visible:ring-red-500'
                      : 'border-gray-300 focus-visible:ring-blue-500'
                  }
                  placeholder="输入供应商名称"
                />
                {errors.name && <p className="mt-1 text-sm text-red-500">{errors.name}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">联系人姓名</label>
                <Input
                  type="text"
                  name="contact_name"
                  value={formData.contact_name}
                  onChange={handleChange}
                  className="border-gray-300 focus-visible:ring-blue-500"
                  placeholder="输入联系人姓名"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">联系人电话</label>
                <Input
                  type="text"
                  name="contact_phone"
                  value={formData.contact_phone}
                  onChange={handleChange}
                  className="border-gray-300 focus-visible:ring-blue-500"
                  placeholder="输入联系人电话"
                />
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">联系人邮箱</label>
                <Input
                  type="email"
                  name="contact_email"
                  value={formData.contact_email}
                  onChange={handleChange}
                  className={
                    errors.contact_email
                      ? 'border-red-500 focus-visible:ring-red-500'
                      : 'border-gray-300 focus-visible:ring-blue-500'
                  }
                  placeholder="输入联系人邮箱"
                />
                {errors.contact_email && (
                  <p className="mt-1 text-sm text-red-500">{errors.contact_email}</p>
                )}
              </div>
            </div>

            {/* Financial Info */}
            <div className="grid grid-cols-2 gap-4 pt-4 border-t">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">基础货币</label>
                <Select
                  value={formData.base_currency}
                  onValueChange={(value) => handleSelectChange('base_currency', value)}
                >
                  <SelectTrigger className="border-gray-300 focus:ring-blue-500">
                    <SelectValue placeholder="选择基础货币" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="USD">USD - 美元</SelectItem>
                    <SelectItem value="CNY">CNY - 人民币</SelectItem>
                    <SelectItem value="EUR">EUR - 欧元</SelectItem>
                    <SelectItem value="GBP">GBP - 英镑</SelectItem>
                    <SelectItem value="JPY">JPY - 日元</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">支付方式</label>
                <Select
                  value={formData.payment_method}
                  onValueChange={(value) =>
                    handleSelectChange('payment_method', value as PaymentMethod)
                  }
                >
                  <SelectTrigger className="border-gray-300 focus:ring-blue-500">
                    <SelectValue placeholder="选择支付方式" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(PAYMENT_METHOD_CONFIG).map(([value, config]) => (
                      <SelectItem key={value} value={value}>
                        {config.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">税务ID</label>
                <Input
                  type="text"
                  name="tax_id"
                  value={formData.tax_id}
                  onChange={handleChange}
                  className="border-gray-300 focus-visible:ring-blue-500"
                  placeholder="输入税务ID"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">国家代码</label>
                <Input
                  type="text"
                  name="country"
                  value={formData.country}
                  onChange={handleChange}
                  maxLength={2}
                  className={
                    errors.country
                      ? 'border-red-500 focus-visible:ring-red-500'
                      : 'border-gray-300 focus-visible:ring-blue-500'
                  }
                  placeholder="如 CN, US"
                />
                {errors.country && <p className="mt-1 text-sm text-red-500">{errors.country}</p>}
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">支付条款</label>
                <Input
                  type="text"
                  name="payment_terms"
                  value={formData.payment_terms}
                  onChange={handleChange}
                  className="border-gray-300 focus-visible:ring-blue-500"
                  placeholder="如: Net 30"
                />
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">地址</label>
                <Input
                  type="text"
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  className="border-gray-300 focus-visible:ring-blue-500"
                  placeholder="输入地址"
                />
              </div>
            </div>

            {/* Notes */}
            <div className="pt-4 border-t">
              <label className="block text-sm font-medium text-gray-700 mb-1">备注</label>
              <Textarea
                name="notes"
                value={formData.notes}
                onChange={handleChange}
                rows={3}
                className="border-gray-300 focus-visible:ring-blue-500"
                placeholder="输入备注信息"
              />
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-4 border-t">
              <Button type="button" onClick={onCancel} variant="outline">
                取消
              </Button>
              <Button type="submit" disabled={isLoading} variant="primary">
                {isLoading ? '提交中...' : isEdit ? '保存' : '创建'}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default SupplierForm;
