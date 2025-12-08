'use client';

import React from 'react';

export default function DebugPage() {
  return (
    <div className="p-6">
      <h1>调试页面</h1>
      <p>测试基本组件渲染</p>

      {/* 测试 lucide-react 图标 */}
      <div className="mt-4">
        <h2>测试图标</h2>
        <div style={{ display: 'flex', gap: '1rem' }}>
          {React.createElement('div', { key: 'test1' }, '测试1')}
          {React.createElement('div', { key: 'test2' }, '测试2')}
        </div>
      </div>
    </div>
  );
}